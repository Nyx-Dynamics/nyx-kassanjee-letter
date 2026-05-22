"""
build_combined_xlsx_full.py — Full-schema canonical ingestion of AIDSVu
state and county new-diagnosis data 2014-2023.

Differs from build_combined_xlsx.py:
  - Preserves ALL columns from raw .xlsx files (81 county, 413 state)
    rather than slimming to 14/12 analytic columns.
  - Column names normalized: '\n' replaced with space, whitespace
    collapsed. No semantic changes.
  - Suppression codes (-1, -2, -9) converted to NaN only on data
    columns (those containing 'Cases', 'Rate', or 'Percent' in name).
    Flag columns like 'Correctional Facility Warning' are preserved
    as-is.
  - Derived sheets (MSA panel, state panel, stratum aggregates, Van
    Handel overlay, statistics) unchanged from prior version.

Use case: deposit-quality artifact preserving full demographic
stratifications (race × age × sex × transmission route) for downstream
re-users who need fields beyond the Kassanjee letter's analytic scope.

Output: aidsvu_combined_2014_2023_FULL.xlsx (~12-15 MB).
"""

import os
import platform
import re
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, pearsonr, ttest_1samp
from statsmodels.tsa.stattools import acf

DATA_DIR = '.'
CDC_220_PATH = 'cdc_220_counties.csv'

# ---------------------------------------------------------------------
# Run isolation: every invocation writes to its own timestamped directory.
# Format: runs/YYYY-MM-DD_HHMMSS/
# This prevents overwriting prior runs and makes it trivial to diff
# between fix-cycle generations in the PyCharm project tree.
# ---------------------------------------------------------------------
RUN_TIMESTAMP = datetime.now().strftime('%Y-%m-%d_%H%M%S')
RUN_DIR = Path('runs') / RUN_TIMESTAMP
OUTPUT_PATH = str(RUN_DIR / 'aidsvu_combined_2014_2023_FULL.xlsx')

YEARS = list(range(2014, 2024))
EHE_LAUNCH_YEAR = 2019
SUPPRESSION_CODES = [-1, -2, -9]


# ---------------------------------------------------------------------
# 35 EHE-priority MSA county crosswalk (same as slim version)
# ---------------------------------------------------------------------
MSA_COUNTY_MAP = {
    "Atlanta": [("Georgia", "Fulton County"), ("Georgia", "DeKalb County"),
                ("Georgia", "Cobb County"), ("Georgia", "Gwinnett County"),
                ("Georgia", "Clayton County")],
    "Austin": [("Texas", "Travis County"), ("Texas", "Williamson County"),
               ("Texas", "Hays County")],
    "BatonRouge": [("Louisiana", "East Baton Rouge Parish"),
                   ("Louisiana", "Ascension Parish")],
    "Bridgeport": [("Connecticut", "Fairfield County"),
                   ("Connecticut", "Greater Bridgeport Planning Region")],
    "BrowardCO": [("Florida", "Broward County")],
    "Charleston": [("South Carolina", "Charleston County"),
                   ("South Carolina", "Berkeley County"),
                   ("South Carolina", "Dorchester County")],
    "Charlotte": [("North Carolina", "Mecklenburg County")],
    "Columbia": [("South Carolina", "Richland County"),
                 ("South Carolina", "Lexington County")],
    "Dallas": [("Texas", "Dallas County")],
    "Denver": [("Colorado", "Denver County"), ("Colorado", "Adams County"),
               ("Colorado", "Arapahoe County"), ("Colorado", "Jefferson County")],
    "Detroit": [("Michigan", "Wayne County"), ("Michigan", "Oakland County"),
                ("Michigan", "Macomb County")],
    "ElPaso": [("Texas", "El Paso County")],
    "FortWorth": [("Texas", "Tarrant County")],
    "HamptonRoads": [("Virginia", "Norfolk city"),
                     ("Virginia", "Virginia Beach city"),
                     ("Virginia", "Chesapeake city")],
    "Hartford": [("Connecticut", "Hartford County"),
                 ("Connecticut", "Capitol Planning Region")],
    "Houston": [("Texas", "Harris County")],
    "Jackson": [("Mississippi", "Hinds County")],
    "Jacksonville": [("Florida", "Duval County")],
    "KansasCity": [("Missouri", "Jackson County")],
    "LosAngeles": [("California", "Los Angeles County")],
    "MiamiDadeCO": [("Florida", "Miami-Dade County")],
    "Milwaukee": [("Wisconsin", "Milwaukee County")],
    "NewHaven": [("Connecticut", "New Haven County"),
                 ("Connecticut", "South Central Connecticut Planning Region")],
    "NewOrleans": [("Louisiana", "Orleans Parish"),
                   ("Louisiana", "Jefferson Parish")],
    "NewYork": [("New York", "New York County"), ("New York", "Kings County"),
                ("New York", "Queens County"), ("New York", "Bronx County"),
                ("New York", "Richmond County")],
    "OrangeCO": [("California", "Orange County")],
    "Orlando": [("Florida", "Orange County")],
    "PalmBeachCO": [("Florida", "Palm Beach County")],
    "Phoenix": [("Arizona", "Maricopa County")],
    "Raleigh": [("North Carolina", "Wake County")],
    "Richmond": [("Virginia", "Richmond city")],
    "SanAntonio": [("Texas", "Bexar County")],
    "SanJuan": [("Puerto Rico", "San Juan Municipio")],
    "StLouis": [("Missouri", "St. Louis city"), ("Missouri", "St. Louis County")],
    "Tampa": [("Florida", "Hillsborough County"), ("Florida", "Pinellas County")],
}


def normalize_col_name(c):
    """Collapse whitespace and newlines in column names without changing semantics."""
    return re.sub(r'\s+', ' ', str(c).replace('\n', ' ')).strip()


def is_data_column(col):
    """Identify columns that should have suppression codes converted to NaN."""
    name = col.lower()
    return ('cases' in name or 'rate' in name or 'percent' in name)


def clean_suppression_codes(df):
    """Convert -1, -2, -9 to NaN on data columns; preserve flag/metadata columns."""
    for col in df.columns:
        if is_data_column(col):
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].where(~df[col].isin(SUPPRESSION_CODES), np.nan)
    return df


# ---------------------------------------------------------------------
# Full-schema ingestion
# ---------------------------------------------------------------------
def read_county_year_full(path, year):
    """Read full 81-column county file, preserve all columns, clean suppressions."""
    df = pd.read_excel(path, sheet_name='Data', header=3)
    df.columns = [normalize_col_name(c) for c in df.columns]
    df = clean_suppression_codes(df)
    # Enforce year from filename (in case Year column has anomalies)
    if 'Year' in df.columns:
        df['Year'] = year
    else:
        df.insert(0, 'Year', year)
    # GEO ID as zero-padded 5-digit string for FIPS consistency
    if 'GEO ID' in df.columns:
        df['GEO ID'] = df['GEO ID'].astype(str).str.zfill(5)
    return df


def read_state_year_full(path, year):
    """Read full 413-column state file, preserve all columns, clean suppressions."""
    df = pd.read_excel(path, sheet_name='Data', header=3)
    df.columns = [normalize_col_name(c) for c in df.columns]
    df = clean_suppression_codes(df)
    if 'Year' in df.columns:
        df['Year'] = year
    else:
        df.insert(0, 'Year', year)
    return df


def build_county_raw_full():
    rows = []
    for year in YEARS:
        path = f'{DATA_DIR}/AIDSVu_County_NewDX_{year}-20250726.xlsx'
        df = read_county_year_full(path, year)
        rows.append(df)
        print(f"  Read county {year}: {len(df):,} rows × {len(df.columns)} cols")
    combined = pd.concat(rows, ignore_index=True)
    return combined


def build_state_raw_full():
    rows = []
    for year in YEARS:
        path = f'{DATA_DIR}/AIDSVu_State_NewDX_{year}-20250726.xlsx'
        df = read_state_year_full(path, year)
        rows.append(df)
        print(f"  Read state {year}: {len(df):,} rows × {len(df.columns)} cols")
    combined = pd.concat(rows, ignore_index=True)
    return combined


# ---------------------------------------------------------------------
# Derived sheets — operate on slim view internally
# ---------------------------------------------------------------------
def slim_county_view(county_full):
    """Internal slim view for MSA panel building. Original column names preserved."""
    cols = {
        'Year': 'year',
        'GEO ID': 'geoid',
        'State': 'state',
        'County Name': 'county',
        'New Diagnoses Cases': 'n_new_dx',
        'New Diagnoses IDU Cases': 'n_idu_dx',
        'New Diagnoses IDU Percent': 'idu_pct',
    }
    available = {orig: new for orig, new in cols.items() if orig in county_full.columns}
    df = county_full[list(available.keys())].rename(columns=available)
    return df


def slim_state_view(state_full):
    """Internal slim view for state panel."""
    cols = {
        'Year': 'year',
        'GEO ID': 'geoid',
        'State': 'state',
        'State Abbreviation': 'state_abbr',
        'New Diagnoses State Cases': 'n_new_dx',
        'New Diagnoses IDU Cases': 'n_idu_dx',
        'New Diagnoses IDU Percent': 'idu_pct',
    }
    available = {orig: new for orig, new in cols.items() if orig in state_full.columns}
    df = state_full[list(available.keys())].rename(columns=available)
    return df

def normalize_county_name(name):
    if pd.isna(name):
        return ''
    return re.sub(r'\s+', ' ', str(name).replace('\n', ' ')).strip()

def build_msa_panel(county_slim):
    rows = []
    for year in YEARS:
        year_df = county_slim[county_slim['year'] == year]
        for msa, county_list in MSA_COUNTY_MAP.items():
            n_new = 0.0
            n_idu = 0.0
            n_found = 0
            for state, cty in county_list:
                m = year_df[
                    (year_df['state'] == state) &
                    (year_df['county'].apply(normalize_county_name) == cty)
                ]
                if len(m) > 0:
                    n_new += m['n_new_dx'].sum(skipna=True)
                    n_idu += m['n_idu_dx'].sum(skipna=True)
                    n_found += len(m)
            idu_pct = 100 * n_idu / n_new if n_new > 0 else np.nan
            rows.append({
                'msa': msa, 'year': year,
                'n_new_dx': n_new, 'n_idu_dx': n_idu, 'idu_pct': idu_pct,
                'n_counties_found': n_found, 'n_counties_total': len(county_list),
            })
    return pd.DataFrame(rows)


def build_state_panel(state_slim):
    keep_cols = ['state', 'year', 'n_new_dx', 'n_idu_dx', 'idu_pct']
    df = state_slim[keep_cols].copy()
    df = df[df['state'].notna() & (df['state'] != 'United States')]
    return df.sort_values(['state', 'year']).reset_index(drop=True)


def build_vanhandel_overlay():
    cdc = pd.read_csv(CDC_220_PATH)
    cdc['fips'] = cdc['fips'].astype(str).str.zfill(5)
    cdc['in_msa'] = False
    cdc['msa_name'] = ''
    msa_county_keys = set()
    msa_county_lookup = {}
    for msa, county_list in MSA_COUNTY_MAP.items():
        for state, cty in county_list:
            key = (state, normalize_county_name(cty))
            msa_county_keys.add(key)
            msa_county_lookup[key] = msa
    for i, row in cdc.iterrows():
        bare_name = str(row['county']).strip()
        for cty_variant in [f"{bare_name} County", f"{bare_name} Parish", bare_name]:
            key = (row['state'], cty_variant)
            if key in msa_county_keys:
                cdc.at[i, 'in_msa'] = True
                cdc.at[i, 'msa_name'] = msa_county_lookup[key]
                break
    return cdc


def build_stratum_aggregates(county_slim, cdc_overlay):
    cdc_fips = set(cdc_overlay['fips'].astype(str).str.zfill(5).tolist())
    cdc_inside_fips = set(
        cdc_overlay[cdc_overlay['in_msa']]['fips'].astype(str).str.zfill(5).tolist()
    )
    cdc_outside_fips = cdc_fips - cdc_inside_fips
    msa_fips = set()
    for year in [2023]:
        year_df = county_slim[county_slim['year'] == year]
        for msa, county_list in MSA_COUNTY_MAP.items():
            for state, cty in county_list:
                m = year_df[
                    (year_df['state'] == state) &
                    (year_df['county'].apply(normalize_county_name) == cty)
                ]
                msa_fips.update(m['geoid'].astype(str).str.zfill(5).tolist())
    rows = []
    for year in YEARS:
        year_df = county_slim[county_slim['year'] == year].copy()
        year_df['fips_padded'] = year_df['geoid'].astype(str).str.zfill(5)

        def stratum(fips):
            if fips in msa_fips:
                return 'A_msa'
            elif fips in cdc_outside_fips:
                return 'B_vuln_rural'
            else:
                return 'C_other'
        year_df['stratum'] = year_df['fips_padded'].apply(stratum)
        for stratum_name in ['A_msa', 'B_vuln_rural', 'C_other']:
            sub = year_df[year_df['stratum'] == stratum_name]
            total_dx = sub['n_new_dx'].sum(skipna=True)
            total_idu = sub['n_idu_dx'].sum(skipna=True)
            n_reporting = sub['n_new_dx'].notna().sum()
            idu_share = 100 * total_idu / total_dx if total_dx > 0 else 0.0
            rows.append({
                'stratum': stratum_name, 'year': year,
                'total_dx': total_dx, 'total_idu': total_idu,
                'n_counties_reporting': n_reporting,
                'idu_share_pct': round(idu_share, 2),
            })
    return pd.DataFrame(rows)


def compute_statistics(msa_panel, state_panel, strata_agg):
    results = {}

    phis = []
    for msa, sub in msa_panel.groupby('msa'):
        x = sub.sort_values('year')['n_new_dx'].values
        if len(x) < 5 or np.all(np.isnan(x)):
            continue
        x = x[~np.isnan(x)]
        if len(x) < 5:
            continue
        t = np.arange(len(x))
        slope, intercept = np.polyfit(t, x, 1)
        resid = x - (slope * t + intercept)
        try:
            ac = acf(resid, nlags=1, fft=False)
            phis.append(ac[1])
        except Exception:
            continue
    results['ar1_phi_msa_avg'] = float(np.nanmean(phis))
    if 0 < abs(results['ar1_phi_msa_avg']) < 1:
        results['ar1_halflife_years'] = float(-np.log(2) / np.log(abs(results['ar1_phi_msa_avg'])))
    else:
        results['ar1_halflife_years'] = np.nan

    odd_total, even_total, odd_idu, even_idu = [], [], [], []
    for msa, sub in msa_panel.groupby('msa'):
        sub = sub.sort_values('year')
        odd = sub[sub['year'] % 2 == 1]
        even = sub[sub['year'] % 2 == 0]
        if len(odd) > 0 and len(even) > 0:
            o_total = odd['n_new_dx'].mean(skipna=True)
            e_total = even['n_new_dx'].mean(skipna=True)
            o_idu = odd['idu_pct'].mean(skipna=True)
            e_idu = even['idu_pct'].mean(skipna=True)
            if not (np.isnan(o_total) or np.isnan(e_total) or
                    np.isnan(o_idu) or np.isnan(e_idu)):
                odd_total.append(o_total)
                even_total.append(e_total)
                odd_idu.append(o_idu)
                even_idu.append(e_idu)
    r_total, _ = pearsonr(odd_total, even_total)
    r_idu, _ = pearsonr(odd_idu, even_idu)
    results['testretest_r_total_dx'] = float(r_total)
    results['testretest_r_idu_share'] = float(r_idu)

    diffs = []
    for msa, sub in msa_panel.groupby('msa'):
        pre = sub[sub['year'] < EHE_LAUNCH_YEAR]['n_new_dx'].dropna()
        post = sub[sub['year'] >= EHE_LAUNCH_YEAR]['n_new_dx'].dropna()
        if len(pre) > 0 and len(post) > 0:
            diffs.append(post.mean() - pre.mean())
    diffs = np.array(diffs)
    if len(diffs) > 0:
        try:
            stat, p = wilcoxon(diffs)
            results['wilcoxon_n_msas'] = int(len(diffs))
            results['wilcoxon_median_delta'] = float(np.median(diffs))
            results['wilcoxon_mean_delta'] = float(np.mean(diffs))
            results['wilcoxon_p'] = float(p)
        except Exception:
            pass

    def per_unit_slope(panel, unit_col):
        slopes = []
        for unit, sub in panel.groupby(unit_col):
            post = sub[sub['year'] >= EHE_LAUNCH_YEAR].sort_values('year')
            post = post.dropna(subset=['idu_pct'])
            if len(post) < 3:
                continue
            x = post['year'].values - EHE_LAUNCH_YEAR
            y = post['idu_pct'].values
            slope, _ = np.polyfit(x, y, 1)
            slopes.append(slope)
        return np.array(slopes)

    state_slopes = per_unit_slope(state_panel, 'state')
    msa_slopes = per_unit_slope(msa_panel, 'msa')
    results['state_n_units'] = int(len(state_slopes))
    results['state_idu_slope_mean'] = float(np.mean(state_slopes))
    results['state_idu_slope_median'] = float(np.median(state_slopes))
    results['state_idu_slope_p'] = float(ttest_1samp(state_slopes, 0).pvalue)
    results['msa_n_units'] = int(len(msa_slopes))
    results['msa_idu_slope_mean'] = float(np.mean(msa_slopes))
    results['msa_idu_slope_median'] = float(np.median(msa_slopes))
    results['msa_idu_slope_p'] = float(ttest_1samp(msa_slopes, 0).pvalue)

    for stratum_name in ['A_msa', 'B_vuln_rural', 'C_other']:
        sub = strata_agg[strata_agg['stratum'] == stratum_name].sort_values('year')
        if len(sub) >= 2:
            v2014 = sub[sub['year'] == 2014]['total_idu'].iloc[0]
            v2023 = sub[sub['year'] == 2023]['total_idu'].iloc[0]
            results[f'stratum_{stratum_name}_idu_2014'] = float(v2014)
            results[f'stratum_{stratum_name}_idu_2023'] = float(v2023)
            results[f'stratum_{stratum_name}_idu_pct_change'] = (
                float(100 * (v2023 - v2014) / v2014) if v2014 > 0 else np.nan
            )

    return results


# ---------------------------------------------------------------------
# README content (updated for full-schema version)
# ---------------------------------------------------------------------
README_CONTENT = pd.DataFrame({
    'Section': [
        'Title',
        'Version',
        'Source',
        'Period',
        'Files ingested',
        'Compiled by',
        'Compilation date',
        '',
        'METHODOLOGY',
        'Sheet County_Raw',
        'Sheet State_Raw',
        'Sheet MSA_Panel',
        'Sheet State_Panel',
        'Sheet CDC_220_VanHandel',
        'Sheet Stratum_Aggregates',
        'Sheet Statistics_Summary',
        '',
        'COLUMN NAME NORMALIZATION',
        'Newline handling',
        'Whitespace handling',
        '',
        'SUPPRESSION CODES',
        '-1',
        '-2',
        '-9',
        'Application',
        '',
        'CROSSWALK NOTES',
        'CT Planning Regions',
        'LA Parishes',
        'Detroit',
        '',
        'PROVENANCE',
        'AIDSVu',
        'CDC-220 Van Handel',
        'EHE launch',
        '',
        'CITATION',
        'For derived analyses',
        'For raw AIDSVu data',
    ],
    'Detail': [
        'AIDSVu Combined State + County New Diagnoses Panel 2014-2023 (FULL SCHEMA)',
        'Full — all 81 county and 413 state columns preserved',
        'AIDSVu Downloadable Datasets, Rollins School of Public Health, Emory University',
        '2014-2023 (10 calendar years)',
        '20 raw .xlsx files (10 County NewDX + 10 State NewDX)',
        'Nyx Dynamics LLC for Kassanjee letter v7 supplement',
        '2026-05-21',
        '',
        '',
        '~31,200 county-year observations × 81 columns. Demographic stratifications (race × age × sex × transmission route) all preserved.',
        '520 state-year observations × 413 columns. Full intersectional breakdowns preserved.',
        '35 EHE-priority MSAs × 10 years = 350 rows. Aggregates constituent county dx counts. Crosswalk hardcoded; see notes below.',
        '52 state-equivalent units × 10 years = 520 rows. Slim analytic columns; full version in State_Raw.',
        '220 Van Handel et al. 2016 MMWR vulnerable counties with MSA-overlay flag.',
        'Three strata (A=EHE MSA counties, B=Van Handel outside MSAs, C=all other US counties) × 10 years = 30 rows. Used to render Figure 2 in main letter.',
        'AR(1) phi, Wilcoxon pre/post-EHE break-point, state-vs-MSA IDU slope divergence, test-retest reliability, stratum endpoint change.',
        '',
        '',
        "Raw AIDSVu headers contain embedded newlines (e.g., 'New Diagnoses\\nCases'). These have been replaced with single spaces to make column names Excel-readable. No semantic content altered.",
        'Multiple consecutive spaces collapsed to single space; leading/trailing whitespace stripped.',
        '',
        '',
        'Cell size below 5 (case count); value is suppressed',
        'Not applicable (e.g., percentage column when denominator is 0)',
        'Rate not stable enough to report (low denominator)',
        'Suppression codes converted to NaN ONLY on data columns (those whose names contain "Cases", "Rate", or "Percent"). Flag columns like "Correctional Facility Warning" preserve their 0/1 integer values.',
        '',
        '',
        'From 2022 reporting onward, AIDSVu reports Connecticut data by Planning Region (Capitol/Greater Bridgeport/South Central CT) replacing historical counties. Crosswalk includes both naming conventions.',
        'Louisiana data uses Parish nomenclature throughout.',
        'Detroit is in the EHE-priority list but excluded from the Kassanjee 34-MSA analysis cohort. Detroit IS included in this workbook for completeness.',
        '',
        '',
        'https://aidsvu.org — Downloadable datasets, no registration required, freely accessible.',
        'Van Handel MM, Rose CE, Hallisey EJ, et al. JAIDS 2016;73(3):323-331. 220 counties ranked by vulnerability to HIV/HCV outbreaks among PWID.',
        'February 2019 — "Ending the HIV Epidemic in the United States" initiative launched, targeting 48 priority jurisdictions including 35 high-burden MSAs.',
        '',
        '',
        'Demidont AC. Calibration-to-Deployment Mismatch in HIV Prevention Trials (v7). Zenodo. May 2026. doi:10.5281/zenodo.XXXXXXXX',
        'AIDSVu. Emory University Rollins School of Public Health. 2014-2023 data accessed via https://aidsvu.org',
    ],
})


def write_run_metadata(run_dir):
    """Provenance record for this run. Captures timestamp, host, Python/library
    versions, git state, and mtimes of key input files so prior runs can be
    forensically compared without ambiguity."""
    try:
        git_hash = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        git_hash = 'not_a_git_repo_or_git_unavailable'

    try:
        git_porcelain = subprocess.check_output(
            ['git', 'status', '--porcelain'], stderr=subprocess.DEVNULL
        ).decode().strip()
        dirty_flag = 'DIRTY (uncommitted changes)' if git_porcelain else 'clean'
    except (subprocess.CalledProcessError, FileNotFoundError):
        dirty_flag = 'unknown'

    # Capture mtimes of key input files for reproducibility forensics
    input_files = [CDC_220_PATH]
    for f in sorted(Path(DATA_DIR).glob('*AIDSVu_DownloadableDataset*.xlsx')):
        input_files.append(str(f))
    for f in sorted(Path(DATA_DIR).glob('AIDSVu_*.xlsx')):
        input_files.append(str(f))

    lines = [
        f"build_xlxs.py — run provenance metadata",
        f"=" * 64,
        f"Run timestamp:    {RUN_TIMESTAMP}",
        f"Wall time start:  {datetime.now().isoformat()}",
        f"Hostname:         {socket.gethostname()}",
        f"Platform:         {platform.platform()}",
        f"Python:           {sys.version.split()[0]}",
        f"Pandas:           {pd.__version__}",
        f"NumPy:            {np.__version__}",
        f"Working dir:      {Path.cwd()}",
        f"Git HEAD:         {git_hash}",
        f"Git status:       {dirty_flag}",
        f"",
        f"Input files (path : mtime):",
    ]
    for f in input_files:
        p = Path(f)
        if p.exists():
            mtime = datetime.fromtimestamp(p.stat().st_mtime).isoformat()
            lines.append(f"  {f}  :  {mtime}")
        else:
            lines.append(f"  {f}  :  NOT FOUND")

    (run_dir / 'run_metadata.txt').write_text('\n'.join(lines) + '\n')


def main():
    # Create the timestamped run directory before anything else
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    banner = '=' * 72
    print(banner)
    print(f"build_xlxs.py")
    print(f"Run timestamp:    {RUN_TIMESTAMP}")
    print(f"Output directory: {RUN_DIR.absolute()}")
    print(banner)

    print("\n=== Ingesting county raw data, full schema ===")
    county_full = build_county_raw_full()
    print(f"Total: {len(county_full):,} rows × {len(county_full.columns)} columns")

    print("\n=== Ingesting state raw data, full schema ===")
    state_full = build_state_raw_full()
    print(f"Total: {len(state_full):,} rows × {len(state_full.columns)} columns")

    print("\n=== Deriving slim views for panel construction ===")
    county_slim = slim_county_view(county_full)
    state_slim = slim_state_view(state_full)

    print("\n=== Building MSA panel ===")
    msa_panel = build_msa_panel(county_slim)

    print("\n=== Building state panel ===")
    state_panel = build_state_panel(state_slim)

    print("\n=== Building Van Handel overlay ===")
    cdc_overlay = build_vanhandel_overlay()
    n_inside = cdc_overlay['in_msa'].sum()
    print(f"Of 220 CDC-vulnerable counties: {n_inside} inside EHE MSAs")

    print("\n=== Building stratum aggregates ===")
    strata_agg = build_stratum_aggregates(county_slim, cdc_overlay)

    print("\n=== Computing §4.6 statistics ===")
    stats = compute_statistics(msa_panel, state_panel, strata_agg)

    stats_df = pd.DataFrame([
        {'statistic': k, 'value': v} for k, v in stats.items()
    ])

    print("\n=== Writing combined workbook (full schema) ===")
    with pd.ExcelWriter(OUTPUT_PATH, engine='openpyxl') as writer:
        README_CONTENT.to_excel(writer, sheet_name='README', index=False)
        county_full.to_excel(writer, sheet_name='County_Raw', index=False)
        state_full.to_excel(writer, sheet_name='State_Raw', index=False)
        msa_panel.to_excel(writer, sheet_name='MSA_Panel', index=False)
        state_panel.to_excel(writer, sheet_name='State_Panel', index=False)
        cdc_overlay.to_excel(writer, sheet_name='CDC_220_VanHandel', index=False)
        strata_agg.to_excel(writer, sheet_name='Stratum_Aggregates', index=False)
        stats_df.to_excel(writer, sheet_name='Statistics_Summary', index=False)

    size_mb = os.path.getsize(OUTPUT_PATH) / 1e6
    print(f"\nWrote {OUTPUT_PATH} ({size_mb:.2f} MB)")

    # Also export key analytic sheets as standalone CSVs. Two purposes:
    # (1) trivially diff outputs between runs via shell tools (no Excel needed)
    # (2) drop-in candidates for Zenodo deposit without re-extracting from xlsx
    print("\n=== Exporting key sheets as standalone CSVs ===")
    strata_agg.to_csv(RUN_DIR / 'Stratum_Aggregates.csv', index=False)
    msa_panel.to_csv(RUN_DIR / 'MSA_Panel.csv', index=False)
    state_panel.to_csv(RUN_DIR / 'State_Panel.csv', index=False)
    cdc_overlay.to_csv(RUN_DIR / 'CDC_220_VanHandel.csv', index=False)
    stats_df.to_csv(RUN_DIR / 'Statistics_Summary.csv', index=False)
    print(f"  Stratum_Aggregates.csv, MSA_Panel.csv, State_Panel.csv,")
    print(f"  CDC_220_VanHandel.csv, Statistics_Summary.csv")

    # Provenance metadata
    write_run_metadata(RUN_DIR)
    print(f"  run_metadata.txt")

    print(f"\nKey statistics (canonical run against raw AIDSVu):")
    for k, v in stats.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")

    print(f"\n{banner}")
    print(f"Run complete. All outputs in:")
    print(f"  {RUN_DIR.absolute()}")
    print(f"{banner}")


if __name__ == '__main__':
    main()