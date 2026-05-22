"""
compute_covid_deficit.py — COVID counterfactual deficit per stratum, IDU-attributed HIV diagnoses.

Pre-COVID OLS fit window: 2014–2019. Counterfactual projection: 2020–2023.
COVID-caveat window per CDC: 2020–2022 (DiNenno 2022 MMWR; CDC 2020 HIV Surv Report).

Bootstrap 95% CI via 1000-iteration paired resample of pre-COVID years.

MITx-curriculum compliant: scipy.stats.linregress (6.431x), numpy bootstrap (18.6501x).
No scikit-learn, no statsmodels, no compartmental modeling. Stays inside curriculum.

Inputs:
  aidsvu_combined_2014_2023_FULL.xlsx, sheet "Stratum_Aggregates"
  Expected columns: stratum, year, total_idu, n_counties_reporting

Outputs:
  covid_deficit_per_stratum.csv          (per-stratum point estimates + 95% CIs)
  covid_deficit_summary.txt              (tabular summary, paste into §S8.5 supplement)
  fig_covid_counterfactual.png/pdf       (3-panel figure, optional)

Operator: Dr. A.C. Demidont, DO
Date: 2026-05-21
Status: canonical post-audit; corresponds to build_xlxs.py output as authoritative source
"""

import argparse
import sys
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

PRE_COVID_YEARS = np.arange(2014, 2020)   # 2014–2019 inclusive (n=6 pre-COVID)
ALL_YEARS = np.arange(2014, 2024)         # 2014–2023 inclusive (n=10)
COVID_WINDOW = (2020, 2022)               # CDC-caveat 3-year window
N_BOOT = 1000
BOOT_SEED = 42


def fit_and_project(years_obs, y_obs):
    """OLS fit on 2014–2019, project to 2020–2023.

    Returns dict with slope, intercept, r², p, SE(slope), per-year predictions, per-year residuals.
    Residual convention: predicted − observed (positive = observed shortfall against counterfactual).
    """
    years_obs = np.asarray(years_obs, dtype=float)
    y_obs = np.asarray(y_obs, dtype=float)
    pre_mask = (years_obs >= PRE_COVID_YEARS[0]) & (years_obs <= PRE_COVID_YEARS[-1])
    x_pre = years_obs[pre_mask]
    y_pre = y_obs[pre_mask]
    fit = stats.linregress(x_pre, y_pre)
    y_pred = fit.slope * years_obs + fit.intercept
    deficit = y_pred - y_obs
    return {
        'slope': fit.slope, 'intercept': fit.intercept,
        'r2': fit.rvalue ** 2, 'p': fit.pvalue, 'se_slope': fit.stderr,
        'y_pred': y_pred, 'deficit_per_year': deficit,
    }


def bootstrap_cumulative_deficit(years_obs, y_obs, n_boot=N_BOOT,
                                 covid_window=COVID_WINDOW, seed=BOOT_SEED):
    """Paired-resample pre-COVID points, refit OLS, recompute cumulative deficit
    over the COVID window. Return bootstrap distribution of cumulative deficits."""
    rng = np.random.default_rng(seed)
    years_obs = np.asarray(years_obs, dtype=float)
    y_obs = np.asarray(y_obs, dtype=float)
    pre_mask = (years_obs >= PRE_COVID_YEARS[0]) & (years_obs <= PRE_COVID_YEARS[-1])
    x_pre = years_obs[pre_mask]
    y_pre = y_obs[pre_mask]
    n_pre = len(x_pre)
    cw_mask = (years_obs >= covid_window[0]) & (years_obs <= covid_window[1])
    x_cw = years_obs[cw_mask]
    y_obs_cw = y_obs[cw_mask]
    boots = []
    for _ in range(n_boot):
        idx = rng.choice(n_pre, size=n_pre, replace=True)
        if len(np.unique(x_pre[idx])) < 2:
            continue
        slope_b, intercept_b = np.polyfit(x_pre[idx], y_pre[idx], 1)
        y_pred_cw_b = slope_b * x_cw + intercept_b
        boots.append((y_pred_cw_b - y_obs_cw).sum())
    return np.asarray(boots)


def load_stratum_panel(xlsx_path):
    """Read Stratum_Aggregates sheet from build_xlxs.py output workbook.
    Expected schema: stratum, year, total_idu, n_counties_reporting (and optionally total_dx, idu_share_pct)."""
    df = pd.read_excel(xlsx_path, sheet_name='Stratum_Aggregates')
    required = {'stratum', 'year', 'total_idu'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Stratum_Aggregates missing required columns: {missing}")
    df = df.sort_values(['stratum', 'year']).reset_index(drop=True)
    return df


def main(args):
    df = load_stratum_panel(args.input_xlsx)
    strata = ['A_msa', 'B_vuln_rural', 'C_other']

    summary_rows = []
    fig_data = {}
    print("=" * 92)
    print("COVID Counterfactual Deficit Analysis — IDU-attributed HIV diagnoses per stratum")
    print(f"Pre-COVID fit window: {PRE_COVID_YEARS[0]}–{PRE_COVID_YEARS[-1]} (n={len(PRE_COVID_YEARS)} years).")
    print(f"COVID-caveat window: {COVID_WINDOW[0]}–{COVID_WINDOW[1]} (CDC 2020 Surv Report; DiNenno 2022 MMWR).")
    print(f"Bootstrap: {N_BOOT} paired resamples of pre-COVID years; seed = {BOOT_SEED}.")
    print("=" * 92)
    print()

    for stratum in strata:
        sub = df[df['stratum'] == stratum].sort_values('year').reset_index(drop=True)
        if len(sub) < 10:
            print(f"WARNING: Stratum {stratum} has {len(sub)} year-rows; expected 10. Check input.")
        years = sub['year'].values.astype(float)
        y_obs = sub['total_idu'].values.astype(float)

        fit = fit_and_project(years, y_obs)
        boots = bootstrap_cumulative_deficit(years, y_obs)
        ci_lo, ci_hi = np.percentile(boots, [2.5, 97.5])

        cw_mask = (years >= COVID_WINDOW[0]) & (years <= COVID_WINDOW[1])
        cum_def_covid = fit['deficit_per_year'][cw_mask].sum()
        deficit_2023 = fit['deficit_per_year'][years == 2023]
        deficit_2023 = float(deficit_2023[0]) if len(deficit_2023) else float('nan')
        baseline_2019 = float(y_obs[years == 2019][0])
        rel_def_pct = 100.0 * cum_def_covid / baseline_2019

        print(f"--- Stratum {stratum} ---")
        print(f"  Pre-COVID OLS fit: slope = {fit['slope']:+.2f} cases/yr, "
              f"r² = {fit['r2']:.3f}, p = {fit['p']:.4f}, SE(slope) = {fit['se_slope']:.2f}")
        print(f"  Cumulative {COVID_WINDOW[0]}–{COVID_WINDOW[1]} deficit: "
              f"{cum_def_covid:+.0f} IDU dx  [95% boot CI: {ci_lo:+.0f}, {ci_hi:+.0f}]")
        print(f"  Relative to 2019 baseline ({baseline_2019:.0f}): {rel_def_pct:+.1f}%")
        print(f"  2023 single-year deficit (post-caveat): {deficit_2023:+.1f}")
        print()

        summary_rows.append({
            'stratum': stratum,
            'pre_covid_slope': fit['slope'],
            'pre_covid_slope_se': fit['se_slope'],
            'pre_covid_slope_p': fit['p'],
            'pre_covid_r2': fit['r2'],
            'baseline_2019': baseline_2019,
            'cum_deficit_2020_2022': cum_def_covid,
            'cum_deficit_ci_lo': ci_lo,
            'cum_deficit_ci_hi': ci_hi,
            'cum_deficit_pct_of_baseline': rel_def_pct,
            'deficit_2023': deficit_2023,
            'statistically_significant': (ci_lo > 0) or (ci_hi < 0),
        })
        fig_data[stratum] = {'years': years, 'y_obs': y_obs,
                             'y_pred': fit['y_pred'], 'cw_mask': cw_mask}

    out_df = pd.DataFrame(summary_rows)
    out_df.to_csv(args.output_csv, index=False)
    print(f"Wrote per-stratum results: {args.output_csv}")

    # Summary text block for §S8.5
    a = out_df[out_df['stratum'] == 'A_msa'].iloc[0]
    b = out_df[out_df['stratum'] == 'B_vuln_rural'].iloc[0]
    c = out_df[out_df['stratum'] == 'C_other'].iloc[0]
    with open(args.output_txt, 'w') as f:
        f.write("COVID counterfactual deficit decomposition (build_xlxs.py canonical aggregates)\n\n")
        f.write(f"Stratum A (EHE-priority MSA core, n=59 counties constant):\n")
        f.write(f"  Pre-COVID slope: {a['pre_covid_slope']:+.2f} cases/yr (p = {a['pre_covid_slope_p']:.3f}, NS)\n")
        f.write(f"  2020-2022 cumulative deficit: {a['cum_deficit_2020_2022']:+.0f} IDU dx "
                f"[95% CI {a['cum_deficit_ci_lo']:+.0f}, {a['cum_deficit_ci_hi']:+.0f}]\n")
        f.write(f"  Relative to 2019 baseline: {a['cum_deficit_pct_of_baseline']:+.1f}%\n")
        f.write(f"  2023 single-year deficit (post-caveat): {a['deficit_2023']:+.1f}\n\n")
        f.write(f"Stratum B (CDC-220 vulnerable, outside EHE MSAs; n varies 114-130, median 125):\n")
        f.write(f"  Pre-COVID slope: {b['pre_covid_slope']:+.2f} cases/yr (p = {b['pre_covid_slope_p']:.3f})\n")
        f.write(f"  2020-2022 cumulative deficit: {b['cum_deficit_2020_2022']:+.0f} IDU dx "
                f"[95% CI {b['cum_deficit_ci_lo']:+.0f}, {b['cum_deficit_ci_hi']:+.0f}]\n")
        f.write(f"  Relative to 2019 baseline: {b['cum_deficit_pct_of_baseline']:+.1f}%\n")
        f.write(f"  2023 single-year deficit (post-caveat): {b['deficit_2023']:+.1f}\n\n")
        f.write(f"Stratum C (all other US counties; n varies 1,868-1,964, median 1,897):\n")
        f.write(f"  Pre-COVID slope: {c['pre_covid_slope']:+.2f} cases/yr (p = {c['pre_covid_slope_p']:.3f})\n")
        f.write(f"  2020-2022 cumulative deficit: {c['cum_deficit_2020_2022']:+.0f} IDU dx "
                f"[95% CI {c['cum_deficit_ci_lo']:+.0f}, {c['cum_deficit_ci_hi']:+.0f}]\n")
        f.write(f"  Relative to 2019 baseline: {c['cum_deficit_pct_of_baseline']:+.1f}%\n")
        f.write(f"  2023 single-year deficit (post-caveat): {c['deficit_2023']:+.1f}\n")
    print(f"Wrote summary text: {args.output_txt}")

    if args.figure:
        plot_counterfactual(fig_data, args.figure)
        print(f"Wrote figure: {args.figure}")


def plot_counterfactual(fig_data, out_path):
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5))
    labels = {
        'A_msa': 'A. Stratum A (EHE-priority MSAs)',
        'B_vuln_rural': 'B. Stratum B (CDC-220 vulnerable, non-MSA)',
        'C_other': 'C. Stratum C (other US counties)',
    }
    for ax, stratum in zip(axes, ['A_msa', 'B_vuln_rural', 'C_other']):
        d = fig_data[stratum]
        ax.plot(d['years'], d['y_obs'], 'o-', color='#1f77b4', label='Observed', linewidth=1.8, markersize=6)
        ax.plot(d['years'], d['y_pred'], '--', color='#d62728', label='Counterfactual (pre-COVID OLS)', linewidth=1.5)
        ax.axvspan(2020 - 0.5, 2022 + 0.5, alpha=0.15, color='orange', label='COVID caveat window')
        ax.fill_between(d['years'], d['y_obs'], d['y_pred'],
                        where=d['cw_mask'], alpha=0.25, color='red',
                        label='Cumulative deficit')
        ax.set_xlabel('Year')
        ax.set_ylabel('IDU-attributed HIV diagnoses')
        ax.set_title(labels[stratum], loc='left', fontweight='bold', fontsize=10)
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    if out_path.endswith('.png'):
        plt.savefig(out_path.replace('.png', '.pdf'), bbox_inches='tight', facecolor='white')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('--input-xlsx', default='aidsvu_combined_2014_2023_FULL.xlsx',
                        help="Path to build_xlxs.py output workbook")
    parser.add_argument('--output-csv', default='covid_deficit_per_stratum.csv',
                        help="Where to write per-stratum results")
    parser.add_argument('--output-txt', default='covid_deficit_summary.txt',
                        help="Where to write summary text for §S8.5")
    parser.add_argument('--figure', default='fig_covid_counterfactual.png',
                        help="Where to write 3-panel counterfactual figure (or empty string to skip)")
    args = parser.parse_args()
    if args.figure == '':
        args.figure = None
    main(args)
