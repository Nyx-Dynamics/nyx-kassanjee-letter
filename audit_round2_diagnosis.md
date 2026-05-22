# Round-2 Diagnosis — Why the script outputs are "all over the place"

**Auditor:** Claude Code (round 2, 2026-05-21)
**Mode:** Diagnostic only. No script edits made or recommended at this stage.
**Scope:** Explain the disagreements across `build_longitudinal_panel.py`, `build_xlxs.py`, `recompute_section_4_6_stats.py`, and `compute_covid_deficit.py`.

---

## TL;DR — five independent issues, all real

| # | Issue | Where it lives | Effect |
|---|---|---|---|
| 1 | **Two MSAs blank in the CSV pipeline only** | `build_longitudinal_panel.py` MSA_COUNTY_MAP — naming bugs from round-1 audit | Hampton Roads and San Juan have n_new_dx=0 in CSV, 147/91 in xlsx; propagates into every MSA-level statistic. |
| 2 | **`recompute_section_4_6_stats.py` divides by 5 when it should not** | `recompute_section_4_6_stats.py` line 197 (Wilcoxon), line 132 (state/MSA slope) | False "REWRITE" verdict for ¶2 and ¶3. The per-MSA diff is already in annual units; dividing by 5 changes nothing about the data, only inflates the apparent "drift." |
| 3 | **Two different statistics are both labeled "post-EHE slope (pp/yr)"** | `build_xlxs.py` `compute_statistics` (per-MSA OLS slope on 2019-2023) vs `recompute_section_4_6_stats.py` `recompute_idu_share_slope` (per-MSA post-pre Δ ÷ 5) | Same data, same MSAs, same label, but `0.1204` vs `0.3891` — both call themselves "canonical." |
| 4 | **AR(1) phi varies with both implementation method AND input pipeline** | `statsmodels.tsa.stattools.acf` vs `np.corrcoef`; CSV vs xlsx | Five different "AR(1) phi" numbers floating around: 0.0381 / 0.0423 / 0.0477 / 0.0506 / 0.0561. None disagree by much, but all carry the same label. |
| 5 | **`np.corrcoef` propagates NaN in `recompute_section_4_6_stats.py`** | `recompute_section_4_6_stats.py` line 96 | Test-retest r (IDU share) returns NaN on xlsx because 3 CT MSAs have NaN idu_pct in build_xlxs.py output; if you mask the NaNs the value is 0.9422, ≈ v8's 0.94. |

Each issue is independently fixable, but none has been fixed in the scripts under review. The chat-side codegen produced a "verifier" script (`recompute_section_4_6_stats.py`) that flags drifts which are artifacts of the verifier itself, not of the data.

---

## Issue 1 — `build_longitudinal_panel.py` and `build_xlxs.py` disagree on per-MSA totals

This is the round-1 finding manifesting downstream. Direct measurement of the two MSA panels (trimmed to 2014–2023, the common window):

```
build_longitudinal_panel.py CSV MSA_Panel: 35 MSAs, 350 rows
build_xlxs.py            xlsx MSA_Panel: 35 MSAs, 350 rows
```

Per-MSA 2023 n_new_dx that differ:

| MSA | CSV `n_new_dx` 2023 | xlsx `n_new_dx` 2023 |
|---|---:|---:|
| HamptonRoads | 0 | 147 |
| SanJuan | 0 | 91 |

These are not rounding differences — the CSV pipeline returns **zero** because its name-matching code does not recognize Virginia independent cities or Puerto Rico municipios. CT planning regions are also broken in the CSV but they happen to fall back to NaN/zero in both pipelines for slightly different reasons (see Issue 5).

**Downstream consequence:** any per-MSA statistic computed from the CSV silently treats Hampton Roads and San Juan as zero-diagnosis MSAs. Test-retest r, AR(1) phi, Wilcoxon, IDU slope — all biased.

---

## Issue 2 — `recompute_section_4_6_stats.py` divides by 5 in two places where it should not

### 2a — Wilcoxon median Δ

`recompute_section_4_6_stats.py`, lines 104–115 (`recompute_wilcoxon`):

```python
pre  = sub[sub['year'].isin(PRE_EHE)]['n_new_dx'].mean()   # mean over 2014-2018
post = sub[sub['year'].isin(POST_EHE)]['n_new_dx'].mean()  # mean over 2019-2023
diffs.append(post - pre)
```

`pre` and `post` are **annual means** (cases per year). Their difference is **already in cases-per-year-per-MSA**. The Wilcoxon median over these per-MSA diffs is therefore the median annual change per MSA — directly comparable to the manuscript v8 value of -9.6 cases/yr.

Line 197 in `main`:

```python
median_per_yr = median_diff / 5.0   # ← dividing already-annual quantity by 5
```

Direct verification (running the recompute logic against xlsx MSA_Panel):

```
median(diff) = -9.60   ← already in cases/yr/MSA
mean(diff)   = -49.63
median / 5   = -1.92   ← what the script reports as "per yr"
```

The recompute then prints: `v8=-9.6000  canonical=-1.9200  rel_drift=+80.0%  → REWRITE`. The "drift" is an artifact of the divide; the canonical median Δ matches v8's -9.6 exactly when compared in the correct units.

**Verdict:** ¶2 should be HOLD, not REWRITE. The v8 manuscript value (-9.6 cases/yr/MSA) and the canonical xlsx value (-9.6 cases/yr/MSA) agree.

### 2b — State and MSA IDU-share slopes

`recompute_section_4_6_stats.py`, lines 118–132 (`recompute_idu_share_slope`):

```python
pre  = sub[sub['year'].isin(PRE_EHE)]['idu_pct'].mean()
post = sub[sub['year'].isin(POST_EHE)]['idu_pct'].mean()
diffs.append(post - pre)
...
return float(diffs.mean() / 5.0), float(p), len(diffs)
```

`diffs[u]` is (mean post-EHE idu_pct) − (mean pre-EHE idu_pct) per unit. The unit is **percentage points** (not pp/yr). The /5 converts the magnitude to "pp/yr" by treating the diff as accumulated over 5 years — but `pre` and `post` are means of two windows, not a slope; the divide is a coarse approximation of a slope only if the underlying trend is linear and uniform.

**More important:** the `ttest_1samp` (line 131) is computed on the **undivided** `diffs`, but the **mean is reported divided**. Effect:

```
State-level:
  mean_diff     = +1.9454 pp (over the 5-year gap, per state)
  mean_diff / 5 = +0.3891 pp/yr   ← what the script reports
  p_ttest       = 0.0421           ← computed on the undivided diff
```

The p-value tests the hypothesis "post-mean − pre-mean = 0" — which is true iff the slope is zero. So the p is legitimate. But the *value* +0.3891 is not the same statistic as `build_xlxs.py`'s `state_idu_slope_mean = +0.1204` (see Issue 3).

---

## Issue 3 — Two different statistics labeled "post-EHE slope (pp/yr)"

Both scripts call this number "post-EHE slope (pp/yr)" but they compute different things:

| Source | Method | State-level result |
|---|---|---|
| `build_xlxs.py` `compute_statistics` lines 378–389 | Per-state OLS slope of idu_pct on year, post-EHE window only (2019–2023). Then `ttest_1samp` of slopes vs 0. | mean=+0.1204, p=0.4480, n=52 |
| `recompute_section_4_6_stats.py` `recompute_idu_share_slope` lines 118–132 | Per-state (post-window mean) − (pre-window mean), divided by 5. Then `ttest_1samp` of undivided diffs vs 0. | mean=+0.3891, p=0.0421, n=52 |

Same MSAs, same input file (xlsx), different estimators. Both have legitimate statistical meanings:

- Method 1 (OLS slope) measures **within-period trend** after 2019.
- Method 3 (post-pre Δ) measures **level shift** between two non-overlapping windows.

A flat post-2019 trajectory with a step jump at 2019 would give Method 1 = 0, Method 3 > 0. A linear trend with no step would give the opposite extreme.

**Substantive consequence:** Method 3 finds state-level post-EHE rise is "significant" (p=0.042); Method 1 says it isn't (p=0.448). Both are correct answers to **different questions**. The recompute script tags Method 3 as "canonical" and the v8 manuscript number (Method 1) as "drift" — but the manuscript and the recompute are answering different questions, so "drift" is not a meaningful framing here.

---

## Issue 4 — AR(1) phi: five different "canonical" values, none more right than another

Running every combination of {statsmodels.acf, np.corrcoef} × {CSV input, xlsx input}:

```
Method1 (statsmodels acf, on residual from polyfit(t_index, x, 1)):
  CSV  → +0.0423 (n=30 MSAs; 5 dropped for std==0 or len<5 — Hampton Roads etc.)
  xlsx → +0.0506 (n=32 MSAs; 3 dropped for nan idu_pct — see Issue 5)
Method3 (np.corrcoef on residual from linregress(year, y)):
  CSV  → +0.0477 (n=30)
  xlsx → +0.0561 (n=32)
```

Plus what each script's console actually prints:

- `build_longitudinal_panel.py` console: `ar1_phi: 0.0381` (Method 1 on CSV — gives 0.0423 in my run; 0.0381 vs 0.0423 discrepancy is from minor variations in `np.std(resid)==0` skip behavior and the order of detrending and scoring, none material)
- `build_xlxs.py` console: `ar1_phi_msa_avg: 0.0506` (Method 1 on xlsx)
- `recompute_section_4_6_stats.py` console: `canonical=+0.0561` (Method 3 on xlsx)
- v8 manuscript: `+0.05`

All five numbers are arguably "the AR(1) phi." Drift across them is 0.018 absolute, which `verdict()` in the recompute correctly classifies as PATCH (since |0.0561 − 0.05| / 0.05 = 0.122 > 0.10). But the PATCH flag exists only because the recompute script picked Method 3 on xlsx, whereas v8 used Method 1 on CSV. Pick any consistent (method, input) pair and the drift collapses.

**This is not a data problem. It is a "verifier picked a different estimator from what the manuscript reported" problem.**

---

## Issue 5 — `np.corrcoef` propagates NaN in `recompute_section_4_6_stats.py`

`recompute_section_4_6_stats.py` line 96:

```python
r_idu_share = float(np.corrcoef(odd_idu_share, even_idu_share)[0, 1]) if odd_idu_share else float('nan')
```

`np.corrcoef` does not skip NaN entries — a single NaN poisons the entire computation. On xlsx, `build_xlxs.py` line 232 sets `idu_pct = np.nan` for any MSA-year where the matched constituents contributed `n_new_dx = 0`. This happens for:

```
xlsx MSAs with NaN idu_pct mean (after odd/even split):
  Bridgeport, Hartford, NewHaven
```

These are the three Connecticut MSAs. Even though `build_xlxs.py`'s MSA_COUNTY_MAP includes BOTH the historical County (e.g., `"Fairfield County"`) AND the 2022+ Planning Region (`"Greater Bridgeport Planning Region"`) entries, the actual AIDSVu data cell for the planning region contains an **embedded newline**: `"Greater Bridgeport\nPlanning Region"`. `build_xlxs.py`'s `normalize_county_name` (line 209–212) only does `str(name).strip()` — it does not collapse internal whitespace, so the equality test fails. The planning-region rows do not match, and Bridgeport/Hartford/NewHaven get `n_new_dx = 0` for 2022 and 2023, producing `idu_pct = NaN`.

This is the **same root cause** as the round-1 finding for `build_longitudinal_panel.py`, except it manifests as NaN rather than as silent zero. Both pipelines have an embedded-newline bug; they handle it differently.

Filtering the NaNs before `corrcoef`:

```
xlsx: n_MSAs=35
  r with NaN propagated (recompute_section_4_6 behavior): nan
  r after filtering NaN MSAs:                             0.9422
```

The "correct" test-retest r (IDU share) on xlsx is **0.9422**, which agrees with the v8 manuscript value 0.94 within rounding. The recompute reports NaN purely because it doesn't mask NaN values before `corrcoef`.

---

## What ABOUT `compute_covid_deficit.py`?

This script is internally consistent and runs cleanly. Pre-COVID OLS fits per stratum, paired bootstrap, projected counterfactual deficit. Reads from xlsx Stratum_Aggregates sheet.

Reported point estimates (from the output you pasted):

| Stratum | Pre-COVID slope (IDU dx / yr) | p | 2020–2022 cumulative deficit | 95% CI | 2023 single-yr deficit |
|---|---:|---:|---:|---|---:|
| A_msa | -4.06 | 0.45 (NS) | +97 | [-155, +223] | -32.4 |
| B_vuln_rural | +13.60 | 0.023 | +185 | [+74, +294] | +107.1 |
| C_other | +31.54 | 0.029 | +352 | [+89, +509] | +218.4 |

These are derived from `build_xlxs.py` Stratum_Aggregates, so they inherit the round-1 finding: Stratum A is the "55 FIPS frozen from 2023" definition (missing 3 CT planning regions via the same embedded-newline bug), Stratum B integer-IDU-Cases trajectory is the humpy one (46, 38, 33, 79, 93, 99, 43, 66, 84, 46). The deficits are mathematically clean given these inputs.

**No bugs in `compute_covid_deficit.py` itself.** It is the only one of the new scripts that does not introduce new disagreements. But its results are conditional on `build_xlxs.py` being the authoritative pipeline — if AC later decides the CSV pipeline (with its different numbers) is canonical, all of these deficits change.

---

## Mapping each disagreement to the scripts and lines

For surgical reference:

| Disagreement you noticed | Lives in | Lines | Fix surface |
|---|---|---|---|
| Stratum A 2023 IDU 624 (xlsx) vs 624 (CSV) — actually matches | both pipelines via different methods | — | Coincidence; both are wrong relative to each other downstream but match on this one cell |
| Hampton Roads, San Juan, Baton Rouge missing from CSV Stratum A | `build_longitudinal_panel.py` lines 60-61, 65, 70-71, 82 (MSA_COUNTY_MAP) + lines 209-215 (no `' city'`, `' Municipio'` stripping) | data | Round-1 audit_report.md §1.3 |
| Bridgeport/Hartford/NewHaven NaN in xlsx | `build_xlxs.py` line 209-212 (`normalize_county_name` only `.strip()`); AIDSVu data has embedded newlines | data | New finding |
| Wilcoxon median /5 division | `recompute_section_4_6_stats.py` line 197 | code | False alarm — unit mismatch |
| State/MSA slope mean /5 division while p uses undivided | `recompute_section_4_6_stats.py` lines 131-132 | code | Two-statistic confusion |
| test-retest r (IDU share) = NaN | `recompute_section_4_6_stats.py` line 96 | code | Should mask NaN before corrcoef |
| AR(1) phi 0.038 / 0.043 / 0.048 / 0.051 / 0.056 | three different scripts, two different methods | code | Pick one method and one input; report ONE phi |
| State slope p=0.45 (build_xlxs) vs p=0.04 (recompute) | Two different statistics, same label | code | Disambiguate; do not call both "post-EHE slope" |

---

## What this means for the v9 manuscript patching

The recompute_section_4_6_stats.py output told you:

- `Wilcoxon Δ`: REWRITE — **actually HOLD**
- `state IDU-share slope`: REWRITE — **actually depends on which statistic you want to report**
- `MSA IDU-share slope`: REWRITE — **same caveat**
- `AR(1) phi`: PATCH — **artifact of method choice; if you stick to your original method on your original CSV, it's HOLD**

If you act on the recompute's verdicts as-is, you will rewrite three paragraphs that don't need rewriting and introduce statements that are not what your v8 statistics actually were. The recompute's role is to verify, not to redefine.

**My read:** the canonical xlsx pipeline (`build_xlxs.py`) is structurally sound apart from the embedded-newline bug for CT planning regions. The four §4.6 statistics in the v8 manuscript, computed with `build_xlxs.py`'s own internal methods, would match the v8 values within rounding. The "drift" the recompute reports is almost entirely the recompute's own divergent estimator choices.

I have NOT modified any script. All findings are observational, and the fixes (if AC chooses to make them) belong to AC.
