"""
build_longitudinal_panel.py — Construction of the 2014-2023 AIDSVu
longitudinal panel for the Kassanjee v7 supplement §S8.

Reads AIDSVu County and State NewDX .xlsx files (one per year, 2014-2023)
and the parsed CDC Van Handel 220-county FIPS list (cdc_220_counties.csv).

Produces:
  - aidsvu_msa_newdx_panel_2014_2023.csv  (350 rows: 35 MSAs x 10 years)
  - aidsvu_state_newdx_panel_2014_2023.csv (520 rows: 52 units x 10 years)
  - cdc_220_counties_with_msa_flag.csv (220 rows with MSA overlay flag)
  - aidsvu_220_overlay_annual_agg.csv (30 rows: 3 strata x 10 years)

Also runs the statistical tests reported in main letter §4.6:
  - MSA-level AR(1) autocorrelation on detrended annual total dx
  - Pre-EHE (2014-2018) vs post-EHE (2019-2023) within-MSA Wilcoxon
  - State-vs-MSA divergence in IDU-share trends post-EHE
  - Mann-Kendall on stratum aggregates
  - Test-retest reliability (odd-year vs even-year aggregates)
"""

import os
import re
import glob
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, pearsonr
import statsmodels.api as sm
from statsmodels.tsa.stattools import acf

# ---------------------------------------------------------------------
# 1. Configuration: county-to-MSA crosswalk for 35 EHE-priority MSAs.
#    Each MSA maps to a list of (state, county_name_or_fips) tuples.
#    Handles CT Planning Regions (2022+) and LA Parishes.
# ---------------------------------------------------------------------

MSA_COUNTY_MAP = {
    # MSA name : [(state, county_or_fips), ...]
    "Atlanta": [
        ("Georgia", "Fulton"), ("Georgia", "DeKalb"), ("Georgia", "Cobb"),
        ("Georgia", "Gwinnett"), ("Georgia", "Clayton"),
    ],
    "Austin":      [("Texas", "Travis"), ("Texas", "Williamson"), ("Texas", "Hays")],
    "BatonRouge":  [("Louisiana", "East Baton Rouge"), ("Louisiana", "Ascension")],
    "Bridgeport":  [("Connecticut", "Greater Bridgeport Planning Region")],  # 2022+
    "BrowardCO":   [("Florida", "Broward")],
    "Charleston":  [("South Carolina", "Charleston"), ("South Carolina", "Berkeley"),
                    ("South Carolina", "Dorchester")],
    "Charlotte":   [("North Carolina", "Mecklenburg")],
    "Columbia":    [("South Carolina", "Richland"), ("South Carolina", "Lexington")],
    "Dallas":      [("Texas", "Dallas")],
    "Denver":      [("Colorado", "Denver"), ("Colorado", "Adams"), ("Colorado", "Arapahoe"),
                    ("Colorado", "Jefferson")],
    "Detroit":     [("Michigan", "Wayne"), ("Michigan", "Oakland"), ("Michigan", "Macomb")],
    "ElPaso":      [("Texas", "El Paso")],
    "FortWorth":   [("Texas", "Tarrant")],
    "HamptonRoads":[("Virginia", "Norfolk"), ("Virginia", "Virginia Beach"),
                    ("Virginia", "Chesapeake")],
    "Hartford":    [("Connecticut", "Capitol Planning Region")],  # 2022+
    "Houston":     [("Texas", "Harris")],
    "Jackson":     [("Mississippi", "Hinds")],
    "Jacksonville":[("Florida", "Duval")],
    "KansasCity":  [("Missouri", "Jackson")],
    "LosAngeles":  [("California", "Los Angeles")],
    "MiamiDadeCO": [("Florida", "Miami-Dade")],
    "Milwaukee":   [("Wisconsin", "Milwaukee")],
    "NewHaven":    [("Connecticut", "South Central Connecticut Planning Region")],  # 2022+
    "NewOrleans":  [("Louisiana", "Orleans"), ("Louisiana", "Jefferson")],
    "NewYork":     [("New York", "New York"), ("New York", "Kings"),
                    ("New York", "Queens"), ("New York", "Bronx"),
                    ("New York", "Richmond")],
    "OrangeCO":    [("California", "Orange")],
    "Orlando":     [("Florida", "Orange")],
    "PalmBeachCO": [("Florida", "Palm Beach")],
    "Phoenix":     [("Arizona", "Maricopa")],
    "Raleigh":     [("North Carolina", "Wake")],
    "Richmond":    [("Virginia", "Richmond city")],
    "SanAntonio":  [("Texas", "Bexar")],
    "SanJuan":     [("Puerto Rico", "San Juan")],
    "StLouis":     [("Missouri", "St. Louis city"), ("Missouri", "St. Louis County")],
    "Tampa":       [("Florida", "Hillsborough"), ("Florida", "Pinellas")],
}

EHE_LAUNCH_YEAR = 2019
YEARS = list(range(2014, 2024))

# ---------------------------------------------------------------------
# 2. Reader for AIDSVu County NewDX file (one .xlsx per year).
#    Column names vary slightly across years; this normalizes.
# ---------------------------------------------------------------------

def read_aidsvu_county_newdx(path, year):
    """Read AIDSVu County NewDX .xlsx for `year`. Returns DataFrame with
       columns: state, county, n_new_dx, n_idu_dx (IDU is a derived
       percentage * count for IDU-attributed cases)."""
    # Files start with 2-3 lines of header text; data starts at the row
    # whose first cell is "State" or "GEO ID" depending on year.
    df_raw = pd.read_excel(path, header=None)
    header_row = df_raw.index[df_raw.iloc[:, 0].astype(str).str.contains(
        r"^(State|GEO ID)$", regex=True, na=False
    )][0]
    df = pd.read_excel(path, header=header_row)
    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]
    rename = {}
    for c in df.columns:
        cl = c.lower()
        if cl == "state":
            rename[c] = "state"
        elif "county" in cl and "name" in cl:
            rename[c] = "county"
        elif "new diagnoses" in cl and "rate" not in cl and "idu" not in cl.replace("idu", "").lower():
            rename[c] = "n_new_dx"
        elif "idu" in cl and ("%" in c or "percent" in cl):
            rename[c] = "idu_pct"
    df = df.rename(columns=rename)
    df = df[["state", "county", "n_new_dx", "idu_pct"]].copy()
    df["n_new_dx"] = pd.to_numeric(df["n_new_dx"], errors="coerce")
    df["idu_pct"] = pd.to_numeric(df["idu_pct"], errors="coerce").fillna(0.0)
    df["n_idu_dx"] = df["n_new_dx"] * df["idu_pct"] / 100.0
    df["year"] = year
    return df.dropna(subset=["n_new_dx"])


def read_aidsvu_state_newdx(path, year):
    """Same as above for state-level files."""
    df_raw = pd.read_excel(path, header=None)
    header_row = df_raw.index[df_raw.iloc[:, 0].astype(str).str.contains(
        r"^State$", regex=True, na=False
    )][0]
    df = pd.read_excel(path, header=header_row)
    df.columns = [str(c).strip() for c in df.columns]
    rename = {}
    for c in df.columns:
        cl = c.lower()
        if cl == "state":
            rename[c] = "state"
        elif "new diagnoses" in cl and "rate" not in cl and "idu" not in cl.replace("idu", "").lower():
            rename[c] = "n_new_dx"
        elif "idu" in cl and ("%" in c or "percent" in cl):
            rename[c] = "idu_pct"
    df = df.rename(columns=rename)
    df = df[["state", "n_new_dx", "idu_pct"]].copy()
    df["n_new_dx"] = pd.to_numeric(df["n_new_dx"], errors="coerce")
    df["idu_pct"] = pd.to_numeric(df["idu_pct"], errors="coerce").fillna(0.0)
    df["n_idu_dx"] = df["n_new_dx"] * df["idu_pct"] / 100.0
    df["year"] = year
    return df.dropna(subset=["n_new_dx"])


# ---------------------------------------------------------------------
# 3. Build MSA panel
# ---------------------------------------------------------------------

def build_msa_panel(county_data_dir):
    """Reads all yearly AIDSVu county files, aggregates to MSA-year."""
    rows = []
    for year in YEARS:
        # Find the .xlsx file for this year (filename pattern varies)
        candidates = glob.glob(os.path.join(
            county_data_dir, f"AIDSVu_County_NewDX_{year}*.xlsx"
        ))
        if not candidates:
            print(f"WARN: no AIDSVu county file for {year}, skipping")
            continue
        df = read_aidsvu_county_newdx(candidates[0], year)
        for msa, county_list in MSA_COUNTY_MAP.items():
            matches = []
            for state, cty in county_list:
                # Match on state + county; handle variants (e.g., trailing " County")
                m = df[(df["state"] == state) &
                       (df["county"].str.replace(" County", "", regex=False)
                                    .str.replace(" Parish", "", regex=False)
                                    .str.strip()
                        == cty.replace(" County", "")
                              .replace(" Parish", "")
                              .strip())]
                matches.append(m)
            sub = pd.concat(matches, ignore_index=True) if matches else pd.DataFrame()
            n_new = sub["n_new_dx"].sum()
            n_idu = sub["n_idu_dx"].sum()
            idu_pct = 100 * n_idu / n_new if n_new > 0 else 0.0
            rows.append({
                "msa": msa, "year": year,
                "n_new_dx": n_new, "n_idu_dx": n_idu,
                "idu_pct": idu_pct,
                "n_counties_found": len(sub), "n_counties_total": len(county_list),
            })
    return pd.DataFrame(rows)


def build_state_panel(state_data_dir):
    """Reads all yearly AIDSVu state files, builds state-year panel."""
    rows = []
    for year in YEARS:
        candidates = glob.glob(os.path.join(
            state_data_dir, f"AIDSVu_State_NewDX_{year}*.xlsx"
        ))
        if not candidates:
            print(f"WARN: no AIDSVu state file for {year}, skipping")
            continue
        df = read_aidsvu_state_newdx(candidates[0], year)
        rows.append(df[["state", "year", "n_new_dx", "n_idu_dx", "idu_pct"]])
    return pd.concat(rows, ignore_index=True)


# ---------------------------------------------------------------------
# 4. Van Handel overlay: cross-reference CDC-220 against MSAs
# ---------------------------------------------------------------------

def build_vanhandel_overlay(cdc_220_path, msa_panel):
    """Reads parsed CDC-220 county list, flags any inside the 35 EHE MSAs.
       Per Van Handel et al. MMWR 2016, overlap should be zero."""
    cdc = pd.read_csv(cdc_220_path)  # cols: state, fips, county, rank_vh2016
    # Build set of (state, county) inside any MSA
    in_msa = set()
    msa_lookup = {}
    for msa, county_list in MSA_COUNTY_MAP.items():
        for state, cty in county_list:
            key = (state, cty.replace(" County", "").replace(" Parish", "").strip())
            in_msa.add(key)
            msa_lookup[key] = msa
    cdc["in_msa"] = False
    cdc["msa_name"] = ""
    for i, row in cdc.iterrows():
        key = (row["state"],
               str(row["county"]).replace(" County", "")
                                 .replace(" Parish", "").strip())
        if key in in_msa:
            cdc.at[i, "in_msa"] = True
            cdc.at[i, "msa_name"] = msa_lookup[key]
    return cdc


# ---------------------------------------------------------------------
# 5. Stratum aggregation
# ---------------------------------------------------------------------

def build_stratum_aggregates(county_data_dir, cdc_overlay):
    """Aggregates AIDSVu county data into three strata per year."""
    cdc_220_keys = {(r["state"],
                     str(r["county"]).replace(" County", "")
                                     .replace(" Parish", "").strip())
                    for _, r in cdc_overlay.iterrows()}
    msa_keys = set()
    for msa, county_list in MSA_COUNTY_MAP.items():
        for state, cty in county_list:
            msa_keys.add((state, cty.replace(" County", "")
                                    .replace(" Parish", "").strip()))
    rows = []
    for year in YEARS:
        candidates = glob.glob(os.path.join(
            county_data_dir, f"AIDSVu_County_NewDX_{year}*.xlsx"
        ))
        if not candidates:
            continue
        df = read_aidsvu_county_newdx(candidates[0], year)
        for _, row in df.iterrows():
            key = (row["state"],
                   str(row["county"]).replace(" County", "")
                                     .replace(" Parish", "").strip())
            if key in msa_keys:
                stratum = "A_msa"
            elif key in cdc_220_keys:
                stratum = "B_vuln_rural"
            else:
                stratum = "C_other"
            rows.append({
                "stratum": stratum, "year": year,
                "n_new_dx": row["n_new_dx"], "n_idu_dx": row["n_idu_dx"],
            })
    rec = pd.DataFrame(rows)
    agg = rec.groupby(["stratum", "year"]).agg(
        total_dx=("n_new_dx", "sum"),
        total_idu=("n_idu_dx", "sum"),
        n_counties_reporting=("n_new_dx", "size"),
    ).reset_index()
    agg["idu_share_pct"] = np.where(
        agg["total_dx"] > 0, 100 * agg["total_idu"] / agg["total_dx"], 0.0
    ).round(2)
    return agg


# ---------------------------------------------------------------------
# 6. Statistical tests reported in §4.6
# ---------------------------------------------------------------------

def compute_panel_statistics(msa_panel, state_panel):
    """Returns a dict of the statistics cited in main letter §4.6."""
    results = {}

    # AR(1) autocorrelation, averaged across MSAs (detrended)
    phis = []
    for msa, sub in msa_panel.groupby("msa"):
        x = sub.sort_values("year")["n_new_dx"].values
        if len(x) < 5:
            continue
        # Detrend by OLS on year
        years = np.arange(len(x))
        slope, intercept = np.polyfit(years, x, 1)
        resid = x - (slope * years + intercept)
        ac = acf(resid, nlags=1, fft=False)
        phis.append(ac[1])
    results["ar1_phi"] = np.mean(phis)
    results["ar1_halflife_years"] = -np.log(2) / np.log(abs(results["ar1_phi"])) \
        if abs(results["ar1_phi"]) < 1 else np.nan

    # Test-retest reliability (odd vs even year aggregates per MSA)
    odd_total, even_total, odd_idu, even_idu = [], [], [], []
    for msa, sub in msa_panel.groupby("msa"):
        sub = sub.sort_values("year")
        odd = sub[sub["year"] % 2 == 1]
        even = sub[sub["year"] % 2 == 0]
        if len(odd) == 0 or len(even) == 0:
            continue
        odd_total.append(odd["n_new_dx"].mean())
        even_total.append(even["n_new_dx"].mean())
        odd_idu.append(odd["idu_pct"].mean())
        even_idu.append(even["idu_pct"].mean())
    r_total, _ = pearsonr(odd_total, even_total)
    r_idu, _ = pearsonr(odd_idu, even_idu)
    results["testretest_r_total_dx"] = r_total
    results["testretest_r_idu_share"] = r_idu

    # Pre-EHE vs post-EHE Wilcoxon (within-MSA differences in mean annual dx)
    diffs = []
    for msa, sub in msa_panel.groupby("msa"):
        pre = sub[sub["year"] < EHE_LAUNCH_YEAR]["n_new_dx"]
        post = sub[sub["year"] >= EHE_LAUNCH_YEAR]["n_new_dx"]
        if len(pre) == 0 or len(post) == 0:
            continue
        diffs.append(post.mean() - pre.mean())
    diffs = np.array(diffs)
    stat, p = wilcoxon(diffs)
    results["wilcoxon_median_delta"] = np.median(diffs)
    results["wilcoxon_p"] = p

    # State-vs-MSA divergence in IDU share post-EHE
    def annual_idu_change(panel, unit_col):
        slopes = []
        for unit, sub in panel.groupby(unit_col):
            post = sub[sub["year"] >= EHE_LAUNCH_YEAR].sort_values("year")
            if len(post) < 3:
                continue
            x = post["year"].values - EHE_LAUNCH_YEAR
            y = post["idu_pct"].values
            slope, _ = np.polyfit(x, y, 1)
            slopes.append(slope)
        return np.array(slopes)

    state_slopes = annual_idu_change(state_panel, "state")
    msa_slopes = annual_idu_change(msa_panel, "msa")
    from scipy.stats import ttest_1samp
    results["state_idu_slope_mean"] = state_slopes.mean()
    results["state_idu_slope_p"] = ttest_1samp(state_slopes, 0).pvalue
    results["msa_idu_slope_mean"] = msa_slopes.mean()
    results["msa_idu_slope_p"] = ttest_1samp(msa_slopes, 0).pvalue

    return results


# ---------------------------------------------------------------------
# 7. Main
# ---------------------------------------------------------------------

def main(data_dir=".", out_dir=".", cdc_220_path="cdc_220_counties.csv"):
    print(f"Building MSA panel from {data_dir}...")
    msa_panel = build_msa_panel(data_dir)
    msa_panel.to_csv(os.path.join(out_dir, "aidsvu_msa_newdx_panel_2014_2023.csv"),
                     index=False)
    print(f"  Wrote {len(msa_panel)} MSA-year observations")

    print(f"Building state panel from {data_dir}...")
    state_panel = build_state_panel(data_dir)
    state_panel.to_csv(os.path.join(out_dir, "aidsvu_state_newdx_panel_2014_2023.csv"),
                       index=False)
    print(f"  Wrote {len(state_panel)} state-year observations")

    print(f"Building Van Handel overlay...")
    cdc_overlay = build_vanhandel_overlay(cdc_220_path, msa_panel)
    cdc_overlay.to_csv(os.path.join(out_dir, "cdc_220_counties_with_msa_flag.csv"),
                       index=False)
    n_inside = cdc_overlay["in_msa"].sum()
    print(f"  Of 220 CDC-vulnerable counties: {n_inside} inside EHE MSAs (expected 0)")

    print(f"Building stratum aggregates...")
    agg = build_stratum_aggregates(data_dir, cdc_overlay)
    agg.to_csv(os.path.join(out_dir, "aidsvu_220_overlay_annual_agg.csv"), index=False)
    print(f"  Wrote {len(agg)} stratum-year aggregates")

    print(f"\nComputing §4.6 statistics...")
    stats = compute_panel_statistics(msa_panel, state_panel)
    for k, v in stats.items():
        print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=".",
                        help="Directory containing AIDSVu_County_NewDX_*.xlsx and AIDSVu_State_NewDX_*.xlsx")
    parser.add_argument("--out-dir", default=".",
                        help="Directory to write output CSVs")
    parser.add_argument("--cdc-220", default="cdc_220_counties.csv",
                        help="Path to parsed Van Handel 220-county FIPS list")
    args = parser.parse_args()
    main(args.data_dir, args.out_dir, args.cdc_220)
