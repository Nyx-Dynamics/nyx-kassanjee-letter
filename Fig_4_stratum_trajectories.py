"""
Figure 4 — Longitudinal HIV diagnosis trajectories by vulnerability stratum, 2014–2023.

Generates main-letter Figure 2 (renamed Figure_2.png/pdf for LaTeX integration).

Three vertical panels with shared x-axis (year):
  A. Total HIV diagnoses (aggregate per stratum, log-scale y)
  B. IDU-attributed HIV diagnoses (aggregate per stratum, linear y)
  C. IDU share of new diagnoses, % (linear y)

Strata:
  A. 35 EHE-priority MSAs (84 constituent counties)
  B. CDC-220 vulnerable counties outside MSAs (rural)
  C. All other US counties (~2,918)

EHE launch (Feb 2019) marked as vertical dashed line; pre-EHE period shaded light gray.

Input:
  aidsvu_220_overlay_annual_agg.csv
    columns: stratum, year, total_dx, total_idu, n_counties_reporting, idu_share_pct

Output:
  Fig_2_stratum_trajectories.png  (300 dpi)
  Fig_2_stratum_trajectories.pdf  (vector)
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# ---- Load aggregate panel ----
agg = pd.read_csv('aidsvu_220_overlay_annual_agg.csv')

# ---- Style configuration ----
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 9,
    'axes.labelsize': 9,
    'axes.titlesize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'figure.dpi': 100,
})

STRATA = [
    ('A_msa',        '35 EHE-priority MSAs (n=84 counties)',     '#1f77b4', 'o', '-'),
    ('B_vuln_rural', 'CDC-220 vulnerable, outside MSAs (n=220)', '#d62728', 's', '--'),
    ('C_other',      'All other US counties (n=2,918)',          '#2ca02c', '^', '-'),
]

EHE_LAUNCH = 2019
PRE_EHE_MIN = 2014

fig, axes = plt.subplots(3, 1, figsize=(7.0, 8.5), sharex=True)

# ---- Panel A: Total HIV diagnoses ----
ax = axes[0]
for stratum, label, color, marker, ls in STRATA:
    sub = agg[agg['stratum'] == stratum].sort_values('year')
    ax.plot(sub['year'], sub['total_dx'], color=color, marker=marker,
            linestyle=ls, linewidth=1.5, markersize=5, label=label)
ax.set_yscale('log')
ax.set_ylabel('Total HIV diagnoses\n(log scale)')
ax.set_title('A. Total new HIV diagnoses, aggregate per stratum, 2014–2023',
             loc='left', fontweight='bold')
ax.axvspan(PRE_EHE_MIN - 0.5, EHE_LAUNCH - 0.5, alpha=0.08, color='gray', zorder=0)
ax.axvline(EHE_LAUNCH - 0.5, color='black', linestyle=':', linewidth=1, alpha=0.6)
ax.text(EHE_LAUNCH - 0.55, ax.get_ylim()[1] * 0.7, 'EHE launch',
        ha='right', va='top', fontsize=7, alpha=0.7, rotation=0)
ax.legend(loc='center left', bbox_to_anchor=(1.005, 0.5), frameon=False, fontsize=7.5)
ax.grid(True, alpha=0.25, which='both')

# ---- Panel B: IDU-attributed HIV diagnoses ----
ax = axes[1]
for stratum, label, color, marker, ls in STRATA:
    sub = agg[agg['stratum'] == stratum].sort_values('year')
    ax.plot(sub['year'], sub['total_idu'], color=color, marker=marker,
            linestyle=ls, linewidth=1.5, markersize=5, label=label)
ax.set_ylabel('IDU-attributed\nHIV diagnoses')
ax.set_title('B. IDU-attributed HIV diagnoses, aggregate per stratum',
             loc='left', fontweight='bold')
ax.axvspan(PRE_EHE_MIN - 0.5, EHE_LAUNCH - 0.5, alpha=0.08, color='gray', zorder=0)
ax.axvline(EHE_LAUNCH - 0.5, color='black', linestyle=':', linewidth=1, alpha=0.6)
ax.grid(True, alpha=0.25)

# ---- Panel C: IDU share % ----
ax = axes[2]
for stratum, label, color, marker, ls in STRATA:
    sub = agg[agg['stratum'] == stratum].sort_values('year')
    ax.plot(sub['year'], sub['idu_share_pct'], color=color, marker=marker,
            linestyle=ls, linewidth=1.5, markersize=5, label=label)
ax.set_ylabel('IDU share\nof new dx (%)')
ax.set_xlabel('Calendar year')
ax.set_title('C. IDU share of new HIV diagnoses (%)', loc='left', fontweight='bold')
ax.axvspan(PRE_EHE_MIN - 0.5, EHE_LAUNCH - 0.5, alpha=0.08, color='gray', zorder=0)
ax.axvline(EHE_LAUNCH - 0.5, color='black', linestyle=':', linewidth=1, alpha=0.6)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.grid(True, alpha=0.25)
ax.set_xticks(range(2014, 2024))
ax.set_xlim(2013.5, 2023.5)

# ---- Caption-style annotation at bottom ----
fig.text(0.5, 0.005,
         'Gray-shaded region (2014–2018): pre-EHE period.  Dotted vertical line: EHE launch (Feb 2019).',
         ha='center', fontsize=7, style='italic', color='#555555')

plt.tight_layout(rect=[0, 0.02, 0.78, 1.0])
plt.savefig('Fig_2_stratum_trajectories.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('Fig_2_stratum_trajectories.pdf', bbox_inches='tight', facecolor='white')
print('Saved: Fig_2_stratum_trajectories.png and Fig_2_stratum_trajectories.pdf')
print(f'Panel A range: total dx {agg["total_dx"].min():.0f} – {agg["total_dx"].max():.0f}')
print(f'Panel B range: IDU dx  {agg["total_idu"].min():.0f} – {agg["total_idu"].max():.0f}')
print(f'Panel C range: IDU %   {agg["idu_share_pct"].min():.2f} – {agg["idu_share_pct"].max():.2f}')