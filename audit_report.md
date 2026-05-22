# Audit Report — `build_longitudinal_panel.py` Data Ingestion Pipeline

**Auditor:** Claude Code (session opened 2026-05-21)
**Operator:** Dr. A.C. Demidont, DO
**Repo:** `~/gitrepo/nyx-kassanjee-letter` (commit pending)
**Scope:** Forensic. Surface; do not fix. No LaTeX or pipeline edits made.

---

## Top-line finding — pipeline is NOT stable per audit definition

Of the four stability conditions in the handoff (determinism / transparency / honest counts / anchored constants), only #1 passes cleanly.

| # | Condition | Result |
|---|---|---|
| 1 | Determinism | **PASS** — two consecutive runs of `build_longitudinal_panel.py` produce byte-identical CSVs across all 4 outputs. |
| 2 | Transparency | **PARTIAL FAIL** — Fig_4 has hard-coded n-labels that do not match the CSV it reads; `build_figure.py` reads from `/mnt/project/...` (Anthropic compute path) and writes to `/home/claude/...`, neither of which exists locally. |
| 3 | Honest counts | **FAIL** — `n_counties_reporting` does NOT reflect "reporting"; it reflects rows surviving a buggy name-match + a NaN-coerce that LEAVES integer suppression codes (-1, -2, -9) in the data. Both `total_dx` and `total_idu` are contaminated. |
| 4 | Anchored constants | **PARTIAL FAIL** — `ALPHA=1.2` and `SELECTION_AMP=1.5` in `build_figure.py` have informal in-comment references but no resolvable citation key. Retention function constants match §4.1 of the manuscript spec. No per-city conditional branches found. |

**Bottom line:** the freshly-uploaded canonical CSVs are reproducible — but reproducing a broken aggregation does not make the numbers right. The handoff JSON's numbers are NOT a triangulation; they are the output of a DIFFERENT script (`build_xlxs.py`) with cleaner aggregation logic. The two pipelines disagree because they implement materially different methods, not because of rounding.

---

## Task 1 — Inventory of `build_longitudinal_panel.py`

### 1.1 IDU computation method — PRODUCT, not integer sum

Line 142 (county) and line 183 (state):

```python
df["n_idu_dx"] = df["n_new_dx"] * df["idu_pct"] / 100.0
```

The script computes IDU diagnoses as `Cases × IDU_Percent / 100`. It does **NOT** sum the integer `New Diagnoses IDU Cases` column. AC's hypothesis is confirmed.

This is also why the canonical CSV shows fractional endpoints (628.418, 43.534, 42.168) while AC's manual rebuild from the integer column gave whole numbers (628, 46, 46).

### 1.2 Suppression code handling — BROKEN

Line 140–141:

```python
df["n_new_dx"] = pd.to_numeric(df["n_new_dx"], errors="coerce")
df["idu_pct"]  = pd.to_numeric(df["idu_pct"],  errors="coerce").fillna(0.0)
```

`pd.to_numeric` coerces **only non-numeric strings** to NaN. AIDSVu's suppression codes `-1`, `-2`, `-9` are integers — they survive `to_numeric` unchanged. The line 144 `dropna(subset=["n_new_dx"])` only drops genuine NaN; the integer −1 rows remain.

Direct measurement on `AIDSVu_County_NewDX_2023-20250726.xlsx`:

| Quantity | Count |
|---|---|
| County rows kept by read_aidsvu_county_newdx | 3,222 |
| Rows where `n_new_dx == -1` (suppressed but retained) | **1,170** |
| Rows where `idu_pct == -1` (suppressed but retained) | **1,425** |
| Rows where any `idu_pct < 0` (codes -1, -2, -9 etc.) | **2,830** |
| Rows where computed `n_idu_dx < 0` | **436** |
| Net negative contribution to total_idu (2023, nationwide) | **−106.5** |
| Bias to total_dx from −1 rows (2023, nationwide) | **−1,170** |

**Effect on stratum sums:** every county where `idu_pct` is suppressed and `n_new_dx` is positive contributes `n_new_dx × (-1) / 100` — i.e., a negative IDU count proportional to the actual diagnosis count. This systematically depresses both `total_dx` (via −1 rows summed in) and `total_idu` (via the products).

The peer script `build_xlxs.py` handles this correctly (line 39, 117): defines `SUPPRESSION_CODES = [-1, -2, -9]` and applies `df[col].where(~df[col].isin(SUPPRESSION_CODES), np.nan)` on data columns.

### 1.3 Stratum A definition — name-matched MSA constituency, NOT "reporting" counties

Lines 286–328 (`build_stratum_aggregates`):

- `msa_keys` is built from `MSA_COUNTY_MAP` (line 292–296) by stripping `" County"` and `" Parish"` from each entry.
- For each AIDSVu row, the script tests membership of `(state, name)` in `msa_keys`. Match → Stratum A.
- `n_counties_reporting` is just `("n_new_dx", "size")` — count of rows in each (stratum, year) bucket.

The MSA_COUNTY_MAP literal contains **59** county-tuples (counted directly from the dict at lines 40–85). The canonical CSV reports `n_counties_reporting = 51` constant across all 11 years. The 8-county gap is **systematic name-matching failure**, not annual reporting variance:

| MSA-map entry | AIDSVu actual name | Failure mechanism |
|---|---|---|
| `("Virginia", "Norfolk")` | `"Norfolk city"` | Script strips ` County`/` Parish` only; does NOT strip ` city` |
| `("Virginia", "Virginia Beach")` | `"Virginia Beach city"` | same |
| `("Virginia", "Chesapeake")` | `"Chesapeake city"` | same |
| `("Louisiana", "East Baton Rouge")` | `"East Baton Rouge\nParish"` | Embedded newline breaks string equality even though ` Parish` strip would otherwise match |
| `("Puerto Rico", "San Juan")` | `"San Juan Municipio"` | Script does not strip ` Municipio` |
| `("Connecticut", "Greater Bridgeport Planning Region")` | `"Greater Bridgeport\nPlanning Region"` | Embedded newline |
| `("Connecticut", "Capitol Planning Region")` | `"Capitol Planning\nRegion"` | Embedded newline |
| `("Connecticut", "South Central Connecticut Planning Region")` | `"South Central\nConnecticut Planning\nRegion"` | Embedded newlines |

**Epidemiological consequence:** the entire Hampton Roads MSA, all three Connecticut MSAs, Baton Rouge, and San Juan PR are silently dropped from Stratum A diagnosis aggregation. San Juan PR alone reported `n_new_dx = 91` in 2023 — a non-trivial omission for a manuscript invoking PWID epidemiology.

The constancy of `n=51` across years is not "reporting subset by year" — it is "fixed set of MSA constituents whose AIDSVu name matches naively." Stratum A is effectively **27 of 35 MSAs**, not 35.

For comparison, `build_xlxs.py` MSA_COUNTY_MAP keeps the ` County`/` Parish`/` city`/` Municipio` suffixes AS LITERAL DICT KEYS (lines 45–98 of that file) and matches by raw equality, which avoids all 8 of these failures. It also includes both the historical County name and the 2022+ Planning Region name for each CT MSA.

### 1.4 CDC-220 duplicate FIPS handling

AC's check confirmed locally:

```
total rows: 220, unique FIPS: 216, unique (state,county): 216
in_msa=False rows: 219, unique FIPS: 215, unique (state,county): 215
```

But the duplicate sets are not the same:

| Duplicate type | Pairs |
|---|---|
| Duplicate by **FIPS** (in_msa=False) | KY 21235 Whitley ×2, TN 47049 Fentress+Hancock, TN 47087 Jackson+Macon, TN 47095 Lake ×2 |
| Duplicate by **(state, county_name)** (in_msa=False) | KY Whitley ×2 (FIPS 21235), **PA Schuylkill** (FIPS 42107 + 42135), TN Lake ×2 (FIPS 47095), **WV Boone** (FIPS 54009 + 54005) |

Two facts the handoff missed:

- The TN FIPS misalignment (Hancock at 47049, Macon at 47087) does NOT silently drop those counties from Stratum B sums — because the script keys on `(state, county_name)`, not FIPS, and the AIDSVu data carries the correct names. Hancock TN and Macon TN are counted via name match.
- There are TWO additional `(state, county_name)` duplicates that AC's analysis did not flag: **PA Schuylkill** appears twice with different FIPS (42107 + 42135), and **WV Boone** appears twice with different FIPS (54009 + 54005). One member of each pair has a wrong FIPS. These collapse to one entry in the script's set, so stratum sums are unaffected, but they are data-quality flags in `cdc_220_counties_with_msa_flag.csv`.

The script's name-keyed set collapses all dup-by-name pairs to single entries. There is no double-counting in Stratum B.

The **2-county gap** between "215 unique (state, name)" and the CSV's `n_counties_reporting = 213` likely reflects 2 cdc_220 counties whose `(state, name)` simply does not appear in AIDSVu's county file. Could be naming variants (e.g., a county that AIDSVu lists with a ` city`/territory suffix) — same root cause as the Stratum A misses.

### 1.5 Wake County NC (FIPS 37183) — assigned to Stratum A

Line 79 of MSA_COUNTY_MAP: `"Raleigh": [("North Carolina", "Wake")]`. Lines 309–314 check `msa_keys` FIRST in the stratum-assignment cascade, so Wake → `A_msa`. The overlay file correctly flags it `in_msa=True, msa_name=Raleigh`. There is no Stratum B / Stratum C double-counting risk for Wake. ✓

---

## Task 2 — `build_xlxs.py` exists and IS the source of the handoff numbers

The file is named `build_xlxs.py` (typo for "xlsx") — almost certainly the script the handoff referenced as `build_combined_xlsx_full.py` (its module docstring opens with that exact name on line 1–2). It writes `aidsvu_combined_2014_2023_FULL.xlsx`.

Reading that workbook's `Stratum_Aggregates` sheet:

| Stratum | year | total_dx | total_idu | n_counties_reporting | idu_share_pct |
|---|---|---|---|---|---|
| A_msa | 2014 | 15789 | **636** | 55 | 4.03 |
| A_msa | 2023 | 14275 | **631** | 55 | 4.42 |
| B_vuln_rural | 2014 | 1186 | **46** | 126 | 3.88 |
| B_vuln_rural | 2023 | 1125 | **46** | 125 | 4.09 |
| C_other | 2014 | 20686 | **561** | 1968 | 2.71 |
| C_other | 2023 | 21264 | **646** | 1872 | 3.04 |

The IDU endpoints `636 / 631 / 46 / 46 / 561 / 646` exactly match the "Handoff JSON claimed" column. **The handoff numbers came from `build_xlxs.py`, not from triangulation.** The "84 / 219 / 2918" county counts in the handoff do NOT match this output either — the xlsx reports 55 / ~125 / ~1900. Where the 84/219/2918 came from is unclear; possibly an upstream "intended count" rather than a measured count.

### Where the two scripts diverge

| Aspect | `build_longitudinal_panel.py` | `build_xlxs.py` | Effect |
|---|---|---|---|
| Suppression codes -1/-2/-9 | Kept as numeric data | Converted to NaN on Cases/Rate/Percent columns | Major: contaminates sums in build_longitudinal_panel |
| IDU computation | `Cases × Percent / 100` | Sums integer `New Diagnoses IDU Cases` column directly | Different cells contribute |
| MSA_COUNTY_MAP keys | Bare county names ("Norfolk", "Capitol Planning Region") | Full keys with suffixes ("Norfolk city", "East Baton Rouge Parish", "San Juan Municipio") | build_longitudinal_panel misses 8 MSA constituents |
| CT MSAs | Planning Region name only | Historical County + Planning Region (handles 2022+ transition) | build_longitudinal_panel misses CT throughout |
| Stratum A definition | Per-year name match | FIPS set frozen from 2023 match | Different per-year populations |
| `n_counties_reporting` | Row count after dropna (includes -1 rows!) | Count of non-NaN after suppression cleaning | Different semantics |

### Stratum B trajectory shape — both pipelines confirm a hump, but different magnitudes

| Year | build_longitudinal_panel CSV | build_xlxs.py xlsx | AC manual integer rebuild |
|---|---|---|---|
| 2014 | 43.5 | 46 | 46 |
| 2015 | 36.0 | 38 | 38 |
| 2016 | 28.8 | 33 | 33 |
| 2017 | 74.0 | 79 | 79 |
| 2018 | 89.0 | 93 | 93 |
| 2019 | 94.5 | **99** | **99** |
| 2020 | 40.4 | 43 | 43 |
| 2021 | 63.1 | 66 | 66 |
| 2022 | 80.5 | 84 | 84 |
| 2023 | 42.2 | 46 | 46 |

`build_xlxs.py` and AC's manual integer rebuild MATCH EXACTLY across all 10 years. `build_longitudinal_panel.py` is systematically lower by 2.5–5 IDU/year (suppression contamination subtracting). **Both pipelines agree on the qualitative shape: humpy, peak at 2019 (EHE launch year), post-launch decline to 2020.**

The "flat 46→46" claim from the prior handoff is an endpoint cherry-pick that ignores the 2× variation between 2016 (33) and 2019 (99) — it survives only because the 2014 and 2023 values are coincidentally identical (46 in xlsx). It is misleading framing, not a triangulation.

---

## Task 3 — `Fig_4_stratum_trajectories.py`

- Reads `aidsvu_220_overlay_annual_agg.csv` (line 32) — the **non-timestamped** filename. Both `aidsvu_220_overlay_annual_agg.csv` and `aidsvu_220_overlay_annual_agg_2013_2023.csv` exist locally and are **byte-identical** (`diff` reports no differences). No stale-file risk at the moment, but the pipeline currently writes BOTH filenames; if a future run with a different year range only updates the timestamped variant, Fig_4 will silently read stale data.
- **Hard-coded legend strings (lines 47–49):** `n=84 counties`, `n=220`, `n=2,918`. None match the CSV's `n_counties_reporting` (51, 213, 2958), and none match `build_xlxs.py`'s output (55, ~125, ~1900). These are **divorced from data** — they are inherited literals from an earlier session. Stability condition #3 (honest counts) fails here independently of any pipeline bug.

---

## Task 4 — `Fig_5_kassanjee_invariance.py` + `build_figure.py`

### Fig_5 — reproducible ✓

Reads `kassanjee_sensitivity_test.csv` (locally present, 11,006 bytes, last modified 2026-05-20). Running `Fig_5_kassanjee_invariance.py` locally reproduces:

```
n = 34 MSAs
Pearson r  = 0.9998  (p = 3.32e-55)
Spearman rho = 0.9979  (p = 1.74e-39)
Identical policies (all steps): 34/34 (100.0%)
Step-by-step match %: [100. 100. 100. 100. 100.]
```

The Kassanjee invariance numbers in the handoff are stable. `kassanjee_sensitivity_test.csv` is generated by `kassanjee_invariance_test.py` (line 88 default path; line 125 writes).

### build_figure.py — will NOT run locally as-is

Hard-coded paths:

- Line 6: `df = pd.read_csv('/mnt/project/city_pep_efficacy_results.csv')` — **/mnt/project does not exist locally.** This is an Anthropic compute path.
- Line 38, 111, 112: writes to `/home/claude/letter/...` — also non-local.

Local candidate inputs (column-compatible):

- `city_gamma_table.csv` — has `city, state, gamma_per_day, late_dx_pct, ...` columns. Looks like the actual source.
- `Table_34_cities_full.csv` — has the OUTPUT columns of `build_figure.py` (`Omega_star, deflation_pct, B_IRR, IRR_attenuation_pct`). This is a snapshot of a prior `build_figure.py` run, captured locally.

Constants (lines 8–13):
```
TAU = 173.0
GAMMA_BASE = 5e-4
ALPHA = 1.2
SELECTION_AMP = 1.5
LATE_DX_REF = 20.0
D_VISIT_HALF = 22.5
```

None carry an inline citation key. The header comment (lines 15–17) reads:
```
# Milwaukee-tier (low-late-dx) ≈ 0.93 (PURPOSE 1/2 aggregate)
# Hartford-tier (high-late-dx) ≈ 0.75 (real-world LAI in marginalized cohorts)
```
These are anchors but not citations; they reference cohorts informally without a bibliographic key.

Retention function (line 18–19):
```python
def retention_city(late_dx_pct):
    return max(0.93 - 0.008 * (late_dx_pct - 15.0), 0.70)
```
Matches the §4.1 manuscript specification exactly (`r_city = max(0.93 − 0.008·(late_dx_city − 15), 0.70)`). ✓

No per-city conditional branches (`if city == 'Hartford': retention = X`) anywhere in `build_figure.py`. ✓

---

## What is right and what is broken — short version

**Right:**
- Determinism of `build_longitudinal_panel.py` output.
- Wake County partition (Stratum A via msa_keys precedence).
- Kassanjee invariance numbers (ρ=0.9979, r=0.9998, 34/34).
- Retention function structure.

**Broken or misleading:**
1. `build_longitudinal_panel.py` treats AIDSVu suppression codes (-1, -2, -9) as numeric data, depressing both `total_dx` (by ~1,000–1,200/yr) and `total_idu` (by ~100+/yr nationwide).
2. `build_longitudinal_panel.py` MSA name-matching silently drops 8 of 59 MSA constituents (all of Hampton Roads VA, all of CT, Baton Rouge LA, San Juan PR).
3. Stratum B's "n=213 reporting" is constant across 11 years because it counts rows surviving a buggy filter — including −1-suppressed rows; the actual reporting count is year-varying.
4. Stratum C's "n=2,958" reflects ~3,200 county rows minus those dropped to NaN. Not all 2,958 actually report non-zero data in any given year.
5. `Fig_4_stratum_trajectories.py` legend labels (84 / 220 / 2,918) match NEITHER the script that feeds it (51/213/2958) NOR the alternative pipeline output (55/~125/~1900). They are stale literals.
6. `build_figure.py` hard-codes `/mnt/project/` and `/home/claude/` paths and will not run locally without edits.
7. The "Handoff JSON's canonical numbers" are not triangulated — they are the output of `build_xlxs.py`, while the freshly-uploaded CSVs are the output of `build_longitudinal_panel.py`. The two scripts implement materially different methods.

**Recommendation (informational only, no edits made):**
The "right" reading of AIDSVu, in my view, would be: (a) clean -1/-2/-9 to NaN BEFORE any arithmetic; (b) sum the integer `New Diagnoses IDU Cases` column directly when available, falling back to `Cases × Percent / 100` only where the integer column is suppressed AND the percent is not; (c) report `n_counties_reporting` as `notna().sum()` AFTER suppression cleaning; (d) use the build_xlxs.py MSA_COUNTY_MAP keys (with literal suffixes) and handle embedded newlines in AIDSVu column entries. None of this is patched in this audit — it is AC's call whether to (i) adopt `build_xlxs.py` as the canonical pipeline, (ii) fix the bugs in `build_longitudinal_panel.py` to reconcile with it, or (iii) accept the canonical CSV's numbers as-is and document the limitations.
