import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# Path handling
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'Data')
FIG_DIR = os.path.join(BASE_DIR, 'Figures')
os.makedirs(FIG_DIR, exist_ok=True)

INPUT_FILE = os.path.join(DATA_DIR, 'city_prep_ceiling_v2.csv')
if not os.path.exists(INPUT_FILE):
    INPUT_FILE = 'Data/city_prep_ceiling_v2.csv'
    FIG_DIR = 'Figures'

df = pd.read_csv(INPUT_FILE)
df = df.sort_values('ceiling_PWID')

fig = plt.figure(figsize=(17, 11))
gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.30,
                      left=0.06, right=0.96, top=0.92, bottom=0.08)

# ============================================================
# Panel A: Ceiling comparison across cities
# ============================================================
ax = fig.add_subplot(gs[0, :])
y_pos = np.arange(len(df))
bar_h = 0.36

# PWID ceiling bars
bars_pwid = ax.barh(y_pos - bar_h/2, df['ceiling_PWID'], height=bar_h,
                     color='#b2182b', alpha=0.82, edgecolor='black', lw=0.3,
                     label='PWID (parenteral) ceiling')
# General ceiling bars
bars_gen  = ax.barh(y_pos + bar_h/2, df['ceiling_gen'], height=bar_h,
                     color='#2166ac', alpha=0.82, edgecolor='black', lw=0.3,
                     label='General (mucosal) ceiling')

# PURPOSE pooled efficacy line (96%)
ax.axvline(0.96, color='black', lw=2.5, linestyle='--', alpha=0.8,
           label='PURPOSE pooled efficacy (96%)')
ax.text(0.962, len(df)-1, '← PURPOSE pooled\n   96% efficacy', fontsize=9,
        va='top', fontweight='bold')

ax.set_yticks(y_pos)
ax.set_yticklabels([c.replace('\\n', ' ') for c in df['city']], fontsize=8.5)
ax.set_xlabel('Biological ceiling on PrEP efficacy  $\\bar\\eta$', fontsize=11)
ax.set_xlim(0.55, 1.02)
ax.set_title('A. City-stratified PrEP efficacy ceiling: PURPOSE pooled claim transports for mucosal but fails for all 34 MSAs in PWID',
             fontsize=11, loc='left', fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')
ax.legend(loc='lower left', fontsize=10, framealpha=0.95)
ax.axvspan(0, 0.65, alpha=0.04, color='red')

# ============================================================
# Panel B: IRR floor for PWID vs city structural severity
# ============================================================
ax = fig.add_subplot(gs[1, 0])
scatter = ax.scatter(df['structural_delay_h'], df['irr_floor_PWID'],
                     s=60 + df['idu_prevalence_pct']*8,
                     c=df['viral_suppression_pct'], cmap='RdYlGn',
                     edgecolor='black', lw=0.5, alpha=0.88)
cb = plt.colorbar(scatter, ax=ax)
cb.set_label('Viral suppression %', fontsize=9)

# PURPOSE pooled IRR reference
ax.axhline(0.04, color='black', lw=2, linestyle='--', alpha=0.8)
ax.text(2, 0.055, 'PURPOSE pooled IRR = 0.04 (96% efficacy)', fontsize=9, fontweight='bold')

# Annotate extreme cities
for _, r in df.iterrows():
    if r['city'] in ['Hartford', 'SanJuan', 'NewHaven', 'Milwaukee', 'Bridgeport']:
        name = r['city'].replace('\\n', ' ')
        ax.annotate(name, (r['structural_delay_h'], r['irr_floor_PWID']),
                    xytext=(5, 5), textcoords='offset points', fontsize=8,
                    fontweight='bold')

ax.set_xlabel('City structural delay $\\Delta t_{\\mathrm{struct}}$ (h) [from AIDSVu 2023]', fontsize=10)
ax.set_ylabel('PWID parenteral IRR floor  (biological minimum)', fontsize=10)
ax.set_title('B. PWID ceiling vs structural severity\n(bubble size = IDU prevalence %)',
             fontsize=10, loc='left', fontweight='bold')
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 27)
ax.set_ylim(0, 0.45)

# ============================================================
# Panel C: Decomposition — F_cov vs F_access contribution
# ============================================================
ax = fig.add_subplot(gs[1, 1])

# For each city, show the contributions
df_pl = df.sort_values('ceiling_PWID', ascending=True)
top_bottom = pd.concat([df_pl.head(6), df_pl.tail(6)])
y = np.arange(len(top_bottom))

F_cov_contrib = top_bottom['F_cov_PWID']
F_salvage_contrib = (1 - top_bottom['F_cov_PWID']) * top_bottom['F_access_24h_PWID']
gap_loss = (1 - top_bottom['F_cov_PWID']) * (1 - top_bottom['F_access_24h_PWID'])

ax.barh(y, F_cov_contrib, color='#2a9d8f', label='F_cov contribution', edgecolor='black', lw=0.3)
ax.barh(y, F_salvage_contrib, left=F_cov_contrib, color='#e9c46a',
        label='PEP salvage contribution', edgecolor='black', lw=0.3)
ax.barh(y, gap_loss, left=F_cov_contrib + F_salvage_contrib, color='#e76f51',
        label='Unsalvageable gap (efficacy lost)', edgecolor='black', lw=0.3)

ax.axvline(0.96, color='black', lw=2, linestyle='--', alpha=0.8)
ax.text(0.965, len(top_bottom)-1, 'PURPOSE 96%', fontsize=8, va='top', fontweight='bold')

ax.set_yticks(y)
ax.set_yticklabels([c.replace('\\n', ' ') for c in top_bottom['city']], fontsize=9)
ax.set_xlabel('Cumulative efficacy decomposition (PWID)', fontsize=10)
ax.set_title('C. Efficacy decomposition — bottom 6 and top 6 cities\n(F_cov + PEP salvage + unsalvageable gap = 1)',
             fontsize=10, loc='left', fontweight='bold')
ax.set_xlim(0, 1.02)
ax.legend(loc='lower right', fontsize=8, framealpha=0.95)
ax.grid(True, alpha=0.3, axis='x')

plt.suptitle('PrEP Barrier Extrapolation from AIDSVu PEP Data — 34 High-Burden US MSAs',
             fontsize=13, fontweight='bold', y=0.98)

plt.savefig(os.path.join(FIG_DIR, 'city_prep_ceiling.png'), dpi=200, bbox_inches='tight')
print(f"Saved: {os.path.join(FIG_DIR, 'city_prep_ceiling.png')}")
