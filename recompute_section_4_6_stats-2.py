"""
recompute_section_4_6_stats.py — Verify §4.6 ¶1-¶3 statistics against build_xlxs.py canonical.

v2 (2026-05-21, post-Claude-Code-audit):
  - Removed spurious /5.0 divisions on already-per-year Wilcoxon delta and slope means
  - Added NaN masking to all np.corrcoef calls
  - Surfaces which MSAs are dropped from AR(1) due to zero-variance / NaN residuals
  - Added absolute-magnitude floor to verdict bands (no false REWRITE on small-magnitude noise)
  - Added zero-variance smoke-test to surface upstream pipeline bugs (e.g., CT MSAs all zero)

Reads from aidsvu_combined_2014_2023_FULL.xlsx with schema:
  MSA_Panel:    msa, year, n_new_dx, n_idu_dx, idu_pct, n_counties_found, n_counties_total
  State_Panel:  state, year, n_new_dx, n_idu_dx, idu_pct
  Stratum_Aggregates: stratum, year, total_dx, total_idu, n_counties_reporting, idu_share_pct

MITx-curriculum compliant: scipy.stats.linregress, scipy.stats.wilcoxon,
scipy.stats.ttest_1samp, pandas.

Operator: Dr. A.C. Demidont, DO
"""

import argparse
import warnings
import pandas as pd
import numpy as np
from scipy import stats

PRE_EHE = list(range(2014, 2019))   # 2014-2018
POST_EHE = list(range(2019, 2024))  # 2019-2023

V8 = {
    'ar1_phi': 0.05,
    'r_total': 0.999,
    'r_idu_share': 0.94,
    'wilcoxon_delta': -9.6,
    'wilcoxon_p': 0.0002,
    'state_slope_pp': 0.12,
    'state_slope_p': 0.45,
    'msa_slope_pp': -0.08,
    'msa_slope_p': 0.26,
}


def detrend_linear(years, y):
    fit = stats.linregress(years, y)
    return y - (fit.slope * years + fit.intercept)


def lag1_autocorr(x):
    """Lag-1 autocorrelation. Returns NaN for zero-variance or len<3."""
    x = np.asarray(x)
    if len(x) < 3:
        return float('nan')
    if np.std(x[1:]) == 0 or np.std(x[:-1]) == 0:
        return float('nan')
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return float(np.corrcoef(x[1:], x[:-1])[0, 1])


def nan_safe_corrcoef(x, y):
    """Pearson r with NaN masking. Returns (r, n_effective)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    if mask.sum() < 2:
        return float('nan'), int(mask.sum())
    if np.std(x[mask]) == 0 or np.std(y[mask]) == 0:
        return float('nan'), int(mask.sum())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        r = float(np.corrcoef(x[mask], y[mask])[0, 1])
    return r, int(mask.sum())


def smoke_test_msa_panel(msa_panel):
    """Surface MSAs with suspicious data: all-zero n_new_dx, all-NaN idu_pct, etc."""
    issues = []
    for msa_id, sub in msa_panel.groupby('msa'):
        sub = sub.sort_values('year')
        n_total = sub['n_new_dx'].sum()
        n_zero_yrs = (sub['n_new_dx'] == 0).sum()
        n_nan_yrs = sub['n_new_dx'].isna().sum()
        idu_nan_yrs = sub['idu_pct'].isna().sum()
        if n_total == 0:
            issues.append((msa_id, 'ALL_ZERO_n_new_dx', 'every year is zero — likely upstream MSA-crosswalk bug'))
        elif n_zero_yrs > 3:
            issues.append((msa_id, f'MANY_ZERO_yrs={n_zero_yrs}', 'multiple zero years — verify crosswalk'))
        elif n_nan_yrs > 0:
            issues.append((msa_id, f'NAN_n_new_dx_yrs={n_nan_yrs}', 'NaN diagnoses — verify upstream'))
        elif idu_nan_yrs > 3:
            issues.append((msa_id, f'NAN_idu_pct_yrs={idu_nan_yrs}', 'many NaN IDU share — verify upstream'))
    return issues


def recompute_ar1_and_test_retest(msa_panel):
    """AR(1) phi on detrended n_new_dx (mean across MSAs with valid residuals).
    Test-retest r between odd vs even-year aggregates per MSA, across MSAs."""
    phis = []
    dropped_phi = []   # SURFACE which MSAs are dropped
    odd_totals, even_totals = [], []
    odd_idu_share, even_idu_share = [], []
    msa_list_retest = []
    for msa_id, sub in msa_panel.groupby('msa'):
        sub = sub.sort_values('year')
        years = sub['year'].values.astype(float)
        y = sub['n_new_dx'].values.astype(float)
        if np.any(np.isnan(y)) or len(y) < 4:
            dropped_phi.append((msa_id, 'NaN_or_short'))
            continue
        if np.std(y) == 0:
            dropped_phi.append((msa_id, 'ZERO_VARIANCE'))
            continue
        y_detrended = detrend_linear(years, y)
        phi = lag1_autocorr(y_detrended)
        if np.isnan(phi):
            dropped_phi.append((msa_id, 'NaN_from_autocorr'))
            continue
        phis.append(phi)
        odd = sub[sub['year'] % 2 == 1]
        even = sub[sub['year'] % 2 == 0]
        if len(odd) and len(even):
            odd_totals.append(float(odd['n_new_dx'].mean()))
            even_totals.append(float(even['n_new_dx'].mean()))
            odd_idu_share.append(float(odd['idu_pct'].mean()))
            even_idu_share.append(float(even['idu_pct'].mean()))
            msa_list_retest.append(msa_id)
    phi_avg = float(np.mean(phis)) if phis else float('nan')
    r_total, n_total = nan_safe_corrcoef(odd_totals, even_totals)
    r_idu_share, n_idu = nan_safe_corrcoef(odd_idu_share, even_idu_share)
    return phi_avg, r_total, r_idu_share, len(phis), n_total, n_idu, dropped_phi


def recompute_wilcoxon(msa_panel):
    """Within-MSA paired difference (post mean − pre mean) on n_new_dx.
    Wilcoxon signed-rank on resulting differences. Returns median, p, n, mean.
    NOTE: post-pre difference of annual means IS already per-year; no /5 division."""
    diffs = []
    msa_diffs_list = []
    for msa_id, sub in msa_panel.groupby('msa'):
        pre = sub[sub['year'].isin(PRE_EHE)]['n_new_dx'].mean()
        post = sub[sub['year'].isin(POST_EHE)]['n_new_dx'].mean()
        if not (np.isnan(pre) or np.isnan(post)):
            diffs.append(post - pre)
            msa_diffs_list.append((msa_id, post - pre))
    if len(diffs) < 6:
        return float('nan'), float('nan'), len(diffs), float('nan'), msa_diffs_list
    median_diff = float(np.median(diffs))
    mean_diff = float(np.mean(diffs))
    w_stat, p = stats.wilcoxon(diffs)
    return median_diff, float(p), len(diffs), mean_diff, msa_diffs_list


def recompute_idu_share_slope(panel, group_col):
    """Per-unit post-mean minus pre-mean of idu_pct.
    NOTE: post-pre difference of annual means IS already pp/yr; no /5 division.
    Returns mean of per-unit diffs, ttest p-value, n_units."""
    diffs = []
    for unit_id, sub in panel.groupby(group_col):
        pre = sub[sub['year'].isin(PRE_EHE)]['idu_pct'].mean()
        post = sub[sub['year'].isin(POST_EHE)]['idu_pct'].mean()
        if not (np.isnan(pre) or np.isnan(post)):
            diffs.append(post - pre)
    if not diffs:
        return float('nan'), float('nan'), 0
    diffs = np.array(diffs)
    t_stat, p = stats.ttest_1samp(diffs, 0.0)
    return float(diffs.mean()), float(p), len(diffs)


def stratum_county_ranges(stratum_panel):
    out = {}
    for stratum, sub in stratum_panel.groupby('stratum'):
        sub = sub.sort_values('year')
        out[stratum] = {
            'min': int(sub['n_counties_reporting'].min()),
            'max': int(sub['n_counties_reporting'].max()),
            'median': int(sub['n_counties_reporting'].median()),
            '2014': int(sub[sub['year'] == 2014]['n_counties_reporting'].iloc[0]),
            '2023': int(sub[sub['year'] == 2023]['n_counties_reporting'].iloc[0]),
        }
    return out


def fmt_compare(canonical, v8_val):
    if v8_val == 0:
        return f"v8={v8_val:+.4f}  canonical={canonical:+.4f}"
    rel = 100.0 * (canonical - v8_val) / abs(v8_val)
    return f"v8={v8_val:+.4f}  canonical={canonical:+.4f}  rel_drift={rel:+.1f}%"


def verdict(canonical, v8_val, small_magnitude_threshold=0.10,
            small_abs_hold=0.05, small_abs_patch=0.15):
    """Decision rule for HOLD / PATCH / REWRITE.

    For statistics with |v8| >= small_magnitude_threshold:
      |rel_drift| < 10%       → HOLD
      10% <= |rel_drift| < 30% → PATCH
      |rel_drift| >= 30%       → REWRITE

    For small-magnitude statistics (|v8| < small_magnitude_threshold):
      use ABSOLUTE drift bands to avoid false REWRITE on estimator noise.
      |abs_drift| < small_abs_hold  → HOLD
      |abs_drift| < small_abs_patch → PATCH
      otherwise                     → REWRITE
    """
    if v8_val == 0 or np.isnan(canonical):
        return "UNDEFINED"
    abs_drift = abs(canonical - v8_val)
    if abs(v8_val) < small_magnitude_threshold:
        if abs_drift < small_abs_hold:
            return f"HOLD (abs drift {abs_drift:.3f}, small-magnitude band)"
        elif abs_drift < small_abs_patch:
            return f"PATCH (abs drift {abs_drift:.3f}, small-magnitude band)"
        else:
            return f"REWRITE (abs drift {abs_drift:.3f}, small-magnitude band)"
    rel = abs_drift / abs(v8_val)
    if rel < 0.10:
        return f"HOLD ({rel*100:.1f}% rel drift)"
    elif rel < 0.30:
        return f"PATCH ({rel*100:.1f}% rel drift)"
    else:
        return f"REWRITE ({rel*100:.1f}% rel drift)"


def main(args):
    msa_panel = pd.read_excel(args.input_xlsx, sheet_name='MSA_Panel')
    state_panel = pd.read_excel(args.input_xlsx, sheet_name='State_Panel')
    stratum_panel = pd.read_excel(args.input_xlsx, sheet_name='Stratum_Aggregates')

    n_msas = msa_panel['msa'].nunique()
    n_states = state_panel['state'].nunique()
    print("=" * 96)
    print(f"§4.6 ¶1-¶3 recompute vs build_xlxs.py canonical "
          f"(MSA_Panel: {n_msas} MSAs × 10 yr; State_Panel: {n_states} jurisdictions × 10 yr)")
    print("=" * 96)
    print()

    # ---- Smoke test for upstream pipeline bugs ----
    issues = smoke_test_msa_panel(msa_panel)
    if issues:
        print("!! UPSTREAM PIPELINE SMOKE TEST — issues found:")
        for msa_id, kind, note in issues:
            print(f"   {msa_id:<20} {kind:<26} {note}")
        print(f"   Total MSAs flagged: {len(issues)} of {n_msas}")
        print("   If any MSA is ALL_ZERO_n_new_dx, the upstream build_xlxs.py bug is NOT yet fixed.")
        print()
    else:
        print("✓ Upstream smoke test passed: all MSAs report non-zero n_new_dx across the panel")
        print()

    # ¶1
    phi_avg, r_total, r_idu_share, n_phi, n_retest_total, n_retest_idu, dropped_phi = \
        recompute_ar1_and_test_retest(msa_panel)
    print("¶1 — Temporal stability:")
    print(f"  AR(1) phi (detrended n_new_dx, avg across MSAs):")
    print(f"    {fmt_compare(phi_avg, V8['ar1_phi'])}  n_MSAs={n_phi}")
    if dropped_phi:
        print(f"    Dropped MSAs (n={len(dropped_phi)}): {[(m, r) for m, r in dropped_phi]}")
    print(f"    → {verdict(phi_avg, V8['ar1_phi'])}")
    print(f"  Test-retest r (total dx, odd vs even year):")
    print(f"    {fmt_compare(r_total, V8['r_total'])}  n_MSAs_effective={n_retest_total}")
    print(f"    → {verdict(r_total, V8['r_total'])}")
    print(f"  Test-retest r (IDU share, odd vs even year):")
    print(f"    {fmt_compare(r_idu_share, V8['r_idu_share'])}  n_MSAs_effective={n_retest_idu}")
    print(f"    → {verdict(r_idu_share, V8['r_idu_share'])}")
    print()

    # ¶2
    median_diff, wilcoxon_p, n_diffs, mean_diff, msa_diffs_list = recompute_wilcoxon(msa_panel)
    print("¶2 — Pre-EHE vs post-EHE Wilcoxon signed-rank:")
    print(f"  Median within-MSA Δ (post 5-yr mean − pre 5-yr mean, per-year):")
    print(f"    {fmt_compare(median_diff, V8['wilcoxon_delta'])}")
    print(f"    Mean within-MSA Δ: {mean_diff:+.2f}")
    print(f"  Wilcoxon p:             canonical={wilcoxon_p:.4f}, v8={V8['wilcoxon_p']:.4f}")
    print(f"  n MSAs:                 {n_diffs}")
    print(f"  → {verdict(median_diff, V8['wilcoxon_delta'])}")
    print()

    # ¶3
    state_slope, state_p, n_state_units = recompute_idu_share_slope(state_panel, 'state')
    msa_slope, msa_p, n_msa_units = recompute_idu_share_slope(msa_panel, 'msa')
    print("¶3 — Aggregate post-EHE IDU-share slopes (pp/yr; ttest vs 0):")
    print(f"  State-level: {fmt_compare(state_slope, V8['state_slope_pp'])}")
    print(f"               p_canonical={state_p:.3f}  p_v8={V8['state_slope_p']:.3f}  n={n_state_units}")
    print(f"               → {verdict(state_slope, V8['state_slope_pp'])}")
    print(f"  MSA-level:   {fmt_compare(msa_slope, V8['msa_slope_pp'])}")
    print(f"               p_canonical={msa_p:.3f}  p_v8={V8['msa_slope_p']:.3f}  n={n_msa_units}")
    print(f"               → {verdict(msa_slope, V8['msa_slope_pp'])}")
    print()

    # Stratum n_counties_reporting bonus
    ranges = stratum_county_ranges(stratum_panel)
    print("=" * 96)
    print("BONUS — Stratum n_counties_reporting range across 2014-2023")
    print("=" * 96)
    for stratum in ['A_msa', 'B_vuln_rural', 'C_other']:
        r = ranges[stratum]
        if r['min'] == r['max']:
            print(f"  {stratum:<14}: n = {r['min']} (constant)")
        else:
            print(f"  {stratum:<14}: range {r['min']}-{r['max']}, median {r['median']}, "
                  f"2014={r['2014']}, 2023={r['2023']}")
    print()

    # Stratum A IDU shift sanity check
    sa = stratum_panel[stratum_panel['stratum']=='A_msa'].sort_values('year')
    a_2014 = float(sa[sa['year']==2014]['total_idu'].iloc[0])
    a_2023 = float(sa[sa['year']==2023]['total_idu'].iloc[0])
    print(f"Stratum A IDU 2014 = {a_2014:.0f}  (v8 manuscript: 636)")
    print(f"Stratum A IDU 2023 = {a_2023:.0f}  (v8 manuscript: 631)")
    if abs(a_2014 - 636) > 30 or abs(a_2023 - 631) > 30:
        print("!! Stratum A totals have shifted >30 cases from v8 — COVID deficit numbers need refresh.")
    print()

    # Summary
    print("=" * 96)
    print("PATCH-SET IMPACT SUMMARY")
    print("=" * 96)
    items = [
        ('AR(1) phi',                     phi_avg,        V8['ar1_phi']),
        ('test-retest r (total dx)',      r_total,        V8['r_total']),
        ('test-retest r (IDU share)',     r_idu_share,    V8['r_idu_share']),
        ('Wilcoxon Δ (cases/yr)',         median_diff,    V8['wilcoxon_delta']),
        ('state IDU-share slope (pp/yr)', state_slope,    V8['state_slope_pp']),
        ('MSA IDU-share slope (pp/yr)',   msa_slope,      V8['msa_slope_pp']),
    ]
    holds, patches, rewrites = [], [], []
    for name, can, v8 in items:
        v = verdict(can, v8)
        if v.startswith("HOLD"):
            holds.append((name, can, v8))
        elif v.startswith("PATCH"):
            patches.append((name, can, v8))
        elif v.startswith("REWRITE"):
            rewrites.append((name, can, v8))
    print(f"  HOLDS ({len(holds)}):   {[name for name, _, _ in holds]}")
    print(f"  PATCHES ({len(patches)}): {[name for name, _, _ in patches]}")
    print(f"  REWRITES ({len(rewrites)}): {[name for name, _, _ in rewrites]}")
    if patches:
        print()
        print("  PATCH ITEMS (apply new value, no rewrite):")
        for name, can, v8 in patches:
            print(f"     {name}: v8={v8:+.3f}, canonical={can:+.3f}")
    if rewrites:
        print()
        print("!!  REWRITE ITEMS REQUIRE FULL ¶ REWRITE BEFORE v9 SUBMISSION:")
        for name, can, v8 in rewrites:
            print(f"     {name}: v8={v8:+.3f}, canonical={can:+.3f}")

    with open(args.output_txt, 'w') as f:
        f.write("§4.6 ¶1-¶3 canonical values from build_xlxs.py:\n\n")
        f.write(f"AR(1) phi:                      {phi_avg:+.4f}  (v8: {V8['ar1_phi']:+.4f}, n_MSAs={n_phi})\n")
        f.write(f"Test-retest r (total dx):       {r_total:.4f}  (v8: {V8['r_total']:.4f}, n_effective={n_retest_total})\n")
        f.write(f"Test-retest r (IDU share):      {r_idu_share:.4f}  (v8: {V8['r_idu_share']:.4f}, n_effective={n_retest_idu})\n")
        f.write(f"Wilcoxon Δ (cases/yr):          {median_diff:+.2f}, p={wilcoxon_p:.4f}  "
                f"(v8: {V8['wilcoxon_delta']:+.1f}, p={V8['wilcoxon_p']:.4f})\n")
        f.write(f"State IDU-share slope (pp/yr):  {state_slope:+.3f}, p={state_p:.3f}  "
                f"(v8: {V8['state_slope_pp']:+.2f}, p={V8['state_slope_p']:.3f})\n")
        f.write(f"MSA IDU-share slope (pp/yr):    {msa_slope:+.3f}, p={msa_p:.3f}  "
                f"(v8: {V8['msa_slope_pp']:+.2f}, p={V8['msa_slope_p']:.3f})\n\n")
        f.write(f"Stratum A IDU 2014: {a_2014:.0f}  (v8: 636)\n")
        f.write(f"Stratum A IDU 2023: {a_2023:.0f}  (v8: 631)\n\n")
        f.write("Stratum n_counties_reporting:\n")
        for stratum in ['A_msa', 'B_vuln_rural', 'C_other']:
            r = ranges[stratum]
            if r['min'] == r['max']:
                f.write(f"  {stratum}: n = {r['min']} (constant)\n")
            else:
                f.write(f"  {stratum}: range {r['min']}-{r['max']}, median {r['median']}, "
                        f"2014={r['2014']}, 2023={r['2023']}\n")
        if issues:
            f.write("\nUPSTREAM smoke-test issues:\n")
            for msa_id, kind, note in issues:
                f.write(f"  {msa_id}: {kind} — {note}\n")
        if dropped_phi:
            f.write(f"\nMSAs dropped from AR(1) (n={len(dropped_phi)}):\n")
            for msa_id, reason in dropped_phi:
                f.write(f"  {msa_id}: {reason}\n")
    print()
    print(f"Wrote summary to {args.output_txt}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('--input-xlsx', default='aidsvu_combined_2014_2023_FULL.xlsx')
    parser.add_argument('--output-txt', default='section_4_6_recomputed.txt')
    args = parser.parse_args()
    main(args)
