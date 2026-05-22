"""
rebuild_figures.py — Regenerate Figure 2 (stratum trajectories) and Figure 3
(COVID-19 counterfactual deficit) for the Kassanjee v9 manuscript submission.

Reads from aidsvu_combined_2014_2023_FULL.xlsx (post-CT-fix canonical workbook,
regenerated 2026-05-21 after the build_xlxs.py normalize_county_name fix that
restored CT-MSA inclusion in the panel).

Outputs:
  Figure_2_stratum_trajectories.png + .pdf
  Figure_3_covid_counterfactual.png + .pdf

MITx-curriculum compliant: matplotlib, pandas, numpy, scipy.

Operator: Dr. A.C. Demidont, DO
Date: 2026-05-21
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# ----- Publication settings -----
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8,
    'figure.dpi': 100,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# ----- Stratum metadata -----
STRATUM_INFO = {
    'A_msa': {
        'panel_label': 'A',
        'short_name': 'EHE-priority MSAs',
        'n_label': 'n = 59 counties',
        'color': '#1f77b4',
    },
    'B_vuln_rural': {
        'panel_label': 'B',
        'short_name': 'CDC-220 vulnerable, non-MSA',
        'n_label': 'n varies 114–130, median 125',
        'color': '#d62728',
    },
    'C_other': {
        'panel_label': 'C',
        'short_name': 'Other US counties',
        'n_label': 'n varies 1,868–1,964, median 1,897',
        'color': '#2ca02c',
    }
}

PRE_COVID_YEARS = list(range(2014, 2020))     # 2014–2019 (n=6)
COVID_CAVEAT_YEARS = list(range(2020, 2023))  # 2020–2022 (n=3)
ALL_YEARS = list(range(2014, 2024))           # 2014–2023 (n=10)


# ----- Data loading -----
def load_stratum_data(xlsx_path):
    df = pd.read_excel(xlsx_path, sheet_name='Stratum_Aggregates')
    return df


def bootstrap_deficit_ci(years, idu, pre_years, caveat_years, n_boot=1000, seed=42):
    """Paired bootstrap of pre-COVID years for cumulative-deficit CI."""
    rng = np.random.default_rng(seed)
    pre_mask = np.isin(years, pre_years)
    caveat_mask = np.isin(years, caveat_years)
    deficits = []
    pre_x = years[pre_mask]
    pre_y = idu[pre_mask]
    n_pre = len(pre_x)
    obs_caveat = idu[caveat_mask]
    for _ in range(n_boot):
        idx = rng.integers(0, n_pre, n_pre)
        fit = stats.linregress(pre_x[idx], pre_y[idx])
        cf = fit.slope * years[caveat_mask] + fit.intercept
        deficits.append(float(np.sum(cf - obs_caveat)))
    return np.percentile(deficits, [2.5, 97.5])


# ----- Figure 2: Stratum trajectories -----
def make_figure_2(stratum_data, output_prefix='Figure_2_stratum_trajectories'):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for ax, (stratum, info) in zip(axes, STRATUM_INFO.items()):
        sub = stratum_data[stratum_data['stratum'] == stratum].sort_values('year')
        years = sub['year'].values.astype(int)
        idu = sub['total_idu'].values.astype(float)

        # COVID caveat shaded band
        ax.axvspan(2019.5, 2022.5, color='wheat', alpha=0.4,
                   label='COVID caveat window (2020–2022)')

        # Trajectory line
        ax.plot(years, idu, marker='o', color=info['color'], linewidth=2,
                markersize=7, label='IDU-attributed dx', zorder=3)

        # Endpoint labels
        ax.annotate(f'{int(idu[0])}', xy=(years[0], idu[0]),
                    xytext=(-3, 8), textcoords='offset points',
                    fontsize=9, ha='right', fontweight='bold')
        ax.annotate(f'{int(idu[-1])}', xy=(years[-1], idu[-1]),
                    xytext=(3, 8), textcoords='offset points',
                    fontsize=9, ha='left', fontweight='bold')

        # Peak label for Stratum B
        if stratum == 'B_vuln_rural':
            peak_idx = int(np.argmax(idu))
            ax.annotate(f'peak: {int(idu[peak_idx])}',
                        xy=(years[peak_idx], idu[peak_idx]),
                        xytext=(0, 14), textcoords='offset points',
                        fontsize=9, ha='center',
                        arrowprops=dict(arrowstyle='->', color='gray',
                                        lw=0.5, shrinkA=2, shrinkB=2))

        title = (f"{info['panel_label']}. Stratum {info['panel_label']} "
                 f"({info['short_name']})\n{info['n_label']}")
        ax.set_title(title, fontsize=10.5, loc='left')
        ax.set_xlabel('Year')
        ax.set_ylabel('IDU-attributed HIV diagnoses')
        ax.set_xticks(years)
        ax.set_xticklabels([str(y) if (y % 2 == 0 or y == years[-1]) else ''
                             for y in years])
        ax.grid(True, alpha=0.3, linestyle=':')
        ax.legend(loc='best', framealpha=0.9)

    plt.tight_layout()
    plt.savefig(f'{output_prefix}.png', dpi=300)
    plt.savefig(f'{output_prefix}.pdf')
    print(f'  Saved: {output_prefix}.png + .pdf')
    plt.close()


# ----- Figure 3: COVID counterfactual -----
def make_figure_3(stratum_data, output_prefix='Figure_3_covid_counterfactual'):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    summary = []

    for ax, (stratum, info) in zip(axes, STRATUM_INFO.items()):
        sub = stratum_data[stratum_data['stratum'] == stratum].sort_values('year')
        years = sub['year'].values.astype(int)
        idu = sub['total_idu'].values.astype(float)

        # Pre-COVID OLS fit
        pre_mask = np.isin(years, PRE_COVID_YEARS)
        fit = stats.linregress(years[pre_mask], idu[pre_mask])
        counterfactual = fit.slope * years + fit.intercept

        # Cumulative caveat-window deficit
        caveat_mask = np.isin(years, COVID_CAVEAT_YEARS)
        cumulative_deficit = float(np.sum(counterfactual[caveat_mask] - idu[caveat_mask]))
        ci_lo, ci_hi = bootstrap_deficit_ci(years, idu, PRE_COVID_YEARS,
                                            COVID_CAVEAT_YEARS, n_boot=1000, seed=42)
        baseline_2019 = float(idu[years == 2019][0])
        pct_baseline = 100.0 * cumulative_deficit / baseline_2019

        # Shaded caveat window
        ax.axvspan(2019.5, 2022.5, color='wheat', alpha=0.4,
                   label='COVID caveat window')

        # Counterfactual line
        ax.plot(years, counterfactual, '--', color='crimson', linewidth=1.5,
                alpha=0.85, label='Counterfactual (pre-COVID OLS)', zorder=2)

        # Cumulative deficit area
        ax.fill_between(years[caveat_mask], idu[caveat_mask],
                        counterfactual[caveat_mask],
                        where=counterfactual[caveat_mask] > idu[caveat_mask],
                        color='salmon', alpha=0.5, label='Cumulative deficit')

        # Observed trajectory
        ax.plot(years, idu, marker='o', color=info['color'], linewidth=2,
                markersize=7, label='Observed', zorder=3)

        title = (f"{info['panel_label']}. Stratum {info['panel_label']} "
                 f"({info['short_name']})")
        ax.set_title(title, fontsize=10.5, loc='left')
        ax.set_xlabel('Year')
        ax.set_ylabel('IDU-attributed HIV diagnoses')
        ax.set_xticks(years)
        ax.set_xticklabels([str(y) if (y % 2 == 0 or y == years[-1]) else ''
                             for y in years])
        ax.grid(True, alpha=0.3, linestyle=':')
        ax.legend(loc='best', framealpha=0.9, fontsize=8)

        summary.append({
            'stratum': stratum,
            'pre_slope': fit.slope,
            'pre_r2': fit.rvalue ** 2,
            'pre_p': fit.pvalue,
            'deficit': cumulative_deficit,
            'ci_lo': ci_lo,
            'ci_hi': ci_hi,
            'pct_2019_baseline': pct_baseline,
            'baseline_2019': baseline_2019,
        })

    plt.tight_layout()
    plt.savefig(f'{output_prefix}.png', dpi=300)
    plt.savefig(f'{output_prefix}.pdf')
    print(f'  Saved: {output_prefix}.png + .pdf')
    plt.close()

    # Summary text for verification
    print()
    print('  Stratum-level deficit summary (for caption / Table 4 verification):')
    for s in summary:
        print(f"    {s['stratum']:<14} slope={s['pre_slope']:+6.2f} cases/yr  "
              f"r²={s['pre_r2']:.3f}  p={s['pre_p']:.4f}  "
              f"deficit={s['deficit']:+6.0f}  [95% CI {s['ci_lo']:+.0f}, {s['ci_hi']:+.0f}]  "
              f"({s['pct_2019_baseline']:+.1f}% of 2019 baseline {s['baseline_2019']:.0f})")


def main(args):
    print('=' * 80)
    print('Rebuilding Kassanjee v9 manuscript figures from canonical workbook')
    print('=' * 80)
    print(f'Source: {args.input_xlsx}')
    print()
    stratum_data = load_stratum_data(args.input_xlsx)
    print(f'Loaded {len(stratum_data)} stratum-year rows '
          f'({stratum_data["stratum"].nunique()} strata × '
          f'{stratum_data["year"].nunique()} years).')
    print()
    print('Generating Figure 2 (stratum trajectories)...')
    make_figure_2(stratum_data, 'Figure_2_stratum_trajectories')
    print()
    print('Generating Figure 3 (COVID counterfactual)...')
    make_figure_3(stratum_data, 'Figure_3_covid_counterfactual')
    print()
    print('Done. Both figures saved as PNG (300 DPI) + PDF in current directory.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('--input-xlsx', default='aidsvu_combined_2014_2023_FULL.xlsx',
                        help='Path to canonical workbook (post-CT-fix)')
    args = parser.parse_args()
    main(args)
