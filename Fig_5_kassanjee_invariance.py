"""
Figure 5 — Kassanjee correction invariance across 34 US MSAs.

Two-panel figure demonstrating that the optimal cascade policy is invariant to
the application of the Kassanjee structural-severity correction, even though
the underlying value function magnitudes scale with the correction factor.

Panel A: Value function comparison.
    X-axis: V_empty without Kassanjee correction (baseline value function)
    Y-axis: V_empty with    Kassanjee correction (inflated value function)
    34 points, one per MSA.
    Identity line shown.
    Pearson r and Spearman rho annotated.
    Points colored by full_seq_identical (all 34 are True, so all green).

Panel B: Step-by-step policy invariance.
    For each of the 5 cascade steps, fraction of MSAs with identical
    optimal action with vs. without correction.
    All 5 bars at 100% — visualizing the 34/34 result.

Inputs:
  kassanjee_sensitivity_test.csv

Output:
  Fig_3_kassanjee_invariance.png  (300 dpi)
  Fig_3_kassanjee_invariance.pdf  (vector)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

# ---- Load data ----
df = pd.read_csv('kassanjee_sensitivity_test.csv')
n = len(df)

# Pre-compute correlations and invariance counts
r, p_r = pearsonr(df['V_empty_without'], df['V_empty_with'])
rho, p_rho = spearmanr(df['V_empty_without'], df['V_empty_with'])
n_identical = df['full_seq_identical'].sum()
pct_identical = 100 * n_identical / n

# Step-by-step invariance: split the policy strings and compare per step
def parse_seq(s):
    return [x.strip() for x in s.split('→')]

step_match = []
max_steps = 5
for _, row in df.iterrows():
    seq_w = parse_seq(row['seq_with'])
    seq_wo = parse_seq(row['seq_without'])
    match_row = []
    for k in range(max_steps):
        if k < len(seq_w) and k < len(seq_wo):
            match_row.append(seq_w[k] == seq_wo[k])
        else:
            match_row.append(False)
    step_match.append(match_row)
step_match = np.array(step_match)
step_pct = 100 * step_match.mean(axis=0)

STEP_LABELS = ['Step 1', 'Step 2', 'Step 3', 'Step 4', 'Step 5']

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

fig, axes = plt.subplots(1, 2, figsize=(11.0, 5.0), gridspec_kw={'width_ratios': [1.3, 1.0]})

# ---- Panel A: Value function scatter ----
ax = axes[0]
colors = ['#2ca02c' if v else '#d62728' for v in df['full_seq_identical']]
ax.scatter(df['V_empty_without'] / 1e6, df['V_empty_with'] / 1e6,
           c=colors, s=55, alpha=0.75, edgecolor='black', linewidth=0.5, zorder=3)

# Identity line
lim_lo = min(df['V_empty_without'].min(), df['V_empty_with'].min()) / 1e6 * 0.95
lim_hi = max(df['V_empty_without'].max(), df['V_empty_with'].max()) / 1e6 * 1.05
ax.plot([lim_lo, lim_hi], [lim_lo, lim_hi], 'k--', alpha=0.4, linewidth=1, zorder=2, label='Identity')
ax.set_xlim(lim_lo, lim_hi)
ax.set_ylim(lim_lo, lim_hi)
ax.set_xlabel(r'$V_{\mathrm{empty}}$ without Kassanjee correction (millions, USD)')
ax.set_ylabel(r'$V_{\mathrm{empty}}$ with Kassanjee correction (millions, USD)')
ax.set_title('A. Value function: with vs. without Kassanjee correction',
             loc='left', fontweight='bold')

# Annotations
ann = (f'$n$ = {n} MSAs\n'
       f'Pearson $r$ = {r:.4f}\n'
       f'Spearman $\\rho$ = {rho:.4f}\n'
       f'Identical policies: {n_identical}/{n} ({pct_identical:.0f}%)')
ax.text(0.04, 0.96, ann, transform=ax.transAxes, fontsize=8.5,
        va='top', ha='left',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#888', alpha=0.92))

# Label cities with extreme values (top 3 highest)
top_indices = df.nlargest(3, 'V_empty_with').index
for idx in top_indices:
    ax.annotate(df.loc[idx, 'city'],
                xy=(df.loc[idx, 'V_empty_without'] / 1e6, df.loc[idx, 'V_empty_with'] / 1e6),
                xytext=(7, -3), textcoords='offset points',
                fontsize=7.5, alpha=0.8)

ax.grid(True, alpha=0.25)
ax.set_aspect('equal', adjustable='box')

# ---- Panel B: Step-by-step invariance bars ----
ax = axes[1]
bars = ax.bar(STEP_LABELS, step_pct, color='#2ca02c', alpha=0.85,
              edgecolor='black', linewidth=0.5)
ax.set_ylim(0, 110)
ax.set_ylabel('% MSAs with identical optimal action\n(with vs. without correction)')
ax.set_title('B. Cascade-step-level policy invariance, $n=34$ MSAs',
             loc='left', fontweight='bold')
ax.axhline(100, color='black', linestyle=':', alpha=0.4, linewidth=1)
ax.grid(True, alpha=0.25, axis='y')

# Annotate bar tops with absolute counts
for bar, pct in zip(bars, step_pct):
    n_match = int(round(pct * n / 100))
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
            f'{n_match}/{n}\n({pct:.0f}%)',
            ha='center', va='bottom', fontsize=8, fontweight='bold')

plt.tight_layout()
plt.savefig('Fig_3_kassanjee_invariance.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('Fig_3_kassanjee_invariance.pdf', bbox_inches='tight', facecolor='white')
print('Saved: Fig_3_kassanjee_invariance.png and Fig_3_kassanjee_invariance.pdf')
print(f'\nDiagnostic output:')
print(f'  n = {n} MSAs')
print(f'  Pearson r  = {r:.4f}  (p = {p_r:.2e})')
print(f'  Spearman rho = {rho:.4f}  (p = {p_rho:.2e})')
print(f'  Identical policies (all steps): {n_identical}/{n} ({pct_identical:.1f}%)')
print(f'  Step-by-step match %: {step_pct.round(1)}')
