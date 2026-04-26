import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import os

# Use absolute paths relative to the script location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'city_gamma_table.csv')
FIGURE_PATH = os.path.join(BASE_DIR, 'figures', 'fig_phase1c_v2.png')

df = pd.read_csv(DATA_PATH)

fig = plt.figure(figsize=(17, 10))
gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.28,
                      left=0.07, right=0.97, top=0.93, bottom=0.08,
                      height_ratios=[1, 1])

# ===================================================================
# Panel A: City-level γ distribution with trial site overlay
# ===================================================================
ax = fig.add_subplot(gs[0, :])
df_s = df.sort_values('gamma_per_day')
n = len(df_s)
df_s['trial_sites'] = df_s['trial_sites'].fillna('')
colors = []
for _, r in df_s.iterrows():
    ts = str(r['trial_sites'])
    if 'PURPOSE_4' in ts: c = '#b2182b'
    elif 'LEN_Impl' in ts: c = '#d95f0e'
    elif 'PURPOSE_2' in ts: c = '#2166ac'
    elif 'PrEP4U' in ts: c = '#4daf4a'
    else: c = '#888'
    colors.append(c)

bars = ax.barh(range(n), df_s['gamma_per_day'], color=colors, edgecolor='black', lw=0.3, alpha=0.88)
ax.set_yticks(range(n))
ax.set_yticklabels([c.replace('\\n', ' ') for c in df_s['city']], fontsize=8.5)
ax.set_xscale('log')
ax.set_xlim(2e-4, 5e-3)

# Anchor vertical lines
anchor_labels = [
    (2e-4,  'Low (≈MGH)',      '#2ca25f'),
    (5e-4,  'Moderate',         '#feb24c'),
    (8e-4,  'Moderate-high',    '#fd8d3c'),
    (1.1e-3,'Severe',           '#b2182b'),
]
for ag, lbl, col in anchor_labels:
    ax.axvline(ag, color=col, linestyle='--', lw=1.4, alpha=0.65)
    ax.text(ag, n-0.5, f' {lbl}', fontsize=8.5, rotation=0, color=col,
            fontweight='bold', va='top', ha='left')

ax.set_xlabel(r'Competing-risk hazard $\gamma$ (per day, log scale)', fontsize=11)
ax.set_title('A. Site-level γ across 34 AIDSVu MSAs, overlaid with LEN-program trial footprint '
             '(Multivariate barrier-composite severity parameterization, γ_base = 2×10⁻⁴/day)',
             fontsize=10.5, loc='left', fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')

# Legend
legend_elements = [
    Patch(facecolor='#b2182b', label='PURPOSE 4 site (PWID)'),
    Patch(facecolor='#d95f0e', label='LEN Implementation site'),
    Patch(facecolor='#2166ac', label='PURPOSE 2 site'),
    Patch(facecolor='#4daf4a', label='PrEP4U site (Boston)'),
    Patch(facecolor='#888',    label='No LEN trial site'),
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=9, framealpha=0.95)

# ===================================================================
# Panel B: Correction factor vs γ (with abstract severity scenarios)
# ===================================================================
ax = fig.add_subplot(gs[1, 0])

g_range = np.logspace(np.log10(1e-4), np.log10(5e-3), 200)
TAU = 173
corr_range = 1 + g_range * TAU  # Ω/Ω* = 1 + γτ

ax.plot(g_range, corr_range, 'k-', lw=2, alpha=0.8, label=r'$\Omega/\Omega^*$ = 1+γτ (τ=173d)')

# Mark each AIDSVu city
ax.scatter(df['gamma_per_day'], df['correction_factor'],
           s=60, c='#2166ac', edgecolor='black', lw=0.4, alpha=0.75, zorder=4,
           label='AIDSVu MSA')

# Mark the four anchor scenarios
anchor_g = [2e-4, 5e-4, 8e-4, 1.1e-3]
anchor_C = [1 + g*TAU for g in anchor_g]
anchor_names = ['Low', 'Moderate', 'Moderate-high', 'Severe']
for g, C, nm, col in zip(anchor_g, anchor_C,
                          ['Low','Moderate','Moderate-high','Severe'],
                          ['#2ca25f','#feb24c','#fd8d3c','#b2182b']):
    ax.scatter([g], [C], s=180, marker='*', c=col, edgecolor='black', lw=0.8, zorder=5)
    ax.annotate(f'{nm}\n({(C-1)*100:.1f}% defl)',
                (g, C), xytext=(8, -18), textcoords='offset points',
                fontsize=8, fontweight='bold', color=col)

# Label some notable cities
for _, r in df.iterrows():
    if r['city'] in ['Hartford', 'SanJuan', 'NewHaven', 'KansasCity', 'Atlanta']:
        ax.annotate(r['city'].replace('\\n', ' '),
                    (r['gamma_per_day'], r['correction_factor']),
                    xytext=(-35, 8), textcoords='offset points',
                    fontsize=8.5, fontweight='bold')

ax.set_xscale('log')
ax.set_xlabel(r'Competing-risk hazard $\gamma$ (per day)', fontsize=10.5)
ax.set_ylabel(r'Kassanjee correction factor  $\Omega/\Omega^*$', fontsize=10.5)
ax.set_title('B. Incidence deflation as function of γ — AIDSVu MSAs and severity-scenario anchors',
             fontsize=10, loc='left', fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(loc='upper left', fontsize=9, framealpha=0.95)

# ===================================================================
# Panel C: Four-scenario severity sensitivity (abstract, no city labels)
# ===================================================================
ax = fig.add_subplot(gs[1, 1])

scenarios = [
    ('Low',           2e-4,  '#2ca25f'),
    ('Moderate',      5e-4,  '#feb24c'),
    ('Moderate-high', 8e-4,  '#fd8d3c'),
    ('Severe',        1.1e-3,'#b2182b'),
]
labels = [s[0] for s in scenarios]
gammas = [s[1] for s in scenarios]
colors_s = [s[2] for s in scenarios]

omegas = [TAU/(1+g*TAU) for g in gammas]
corrs = [TAU/o for o in omegas]
defls = [(c-1)*100 for c in corrs]

x = np.arange(len(scenarios))
bars = ax.bar(x, defls, color=colors_s, edgecolor='black', lw=0.5, alpha=0.88)
for i, (b, d, o) in enumerate(zip(bars, defls, omegas)):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.5,
            f'{d:.1f}%\nΩ*={o:.1f}d',
            ha='center', fontsize=9, fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels([f'{l}\n(γ={g:.0e})' for l, g in zip(labels, gammas)], fontsize=9)
ax.set_ylabel('Kassanjee incidence deflation (%)', fontsize=10.5)
ax.set_title('C. Abstracted severity sensitivity panel — no city attribution',
             fontsize=10, loc='left', fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')
ax.set_ylim(0, 24)

plt.suptitle('Phase 1c-v2 — Site-Level Kassanjee Survival-Bias Correction from AIDSVu + Multivariate Barrier-Composite Severity Parameterization',
             fontsize=12, fontweight='bold', y=0.99)

os.makedirs(os.path.dirname(FIGURE_PATH), exist_ok=True)
plt.savefig(FIGURE_PATH, dpi=200, bbox_inches='tight')
print(f"Saved: {FIGURE_PATH}")
