import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import lognorm

# Path handling
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(BASE_DIR, 'Figures')
os.makedirs(FIG_DIR, exist_ok=True)

def F_access(t, med, gsd):
    return lognorm.cdf(t, s=np.log(gsd), scale=med)

def ceiling(Fcov, tcrit, acc_med, acc_gsd):
    Facc = F_access(tcrit, acc_med, acc_gsd)
    return Fcov + (1 - Fcov) * Facc

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

# ===================================================================
# Panel A: Ceiling eta vs F_cov for mucosal vs parenteral
# ===================================================================
ax = axes[0]
Fcov_range = np.linspace(0.5, 1.0, 200)

# Mucosal (t_crit=72h) — good access (CGM US), moderate access (Black MSM South),
# poor access (AGYW rural SA/UG)
ceiling_mucosal_good = [ceiling(f, 72, 24, 1.8) for f in Fcov_range]
ceiling_mucosal_mod  = [ceiling(f, 72, 48, 2.0) for f in Fcov_range]
ceiling_mucosal_poor = [ceiling(f, 72, 72, 2.2) for f in Fcov_range]
# Parenteral (t_crit=24h) — PWID access (median 72h, Taylor 2019)
ceiling_parenteral   = [ceiling(f, 24, 72, 2.0) for f in Fcov_range]

ax.plot(Fcov_range, ceiling_mucosal_good, '-',  color='#2166ac', lw=2.5,
        label='Mucosal, urban access (median 24h)')
ax.plot(Fcov_range, ceiling_mucosal_mod,  '--', color='#4393c3', lw=2,
        label='Mucosal, moderate access (48h)')
ax.plot(Fcov_range, ceiling_mucosal_poor, ':',  color='#92c5de', lw=2,
        label='Mucosal, poor access (72h)')
ax.plot(Fcov_range, ceiling_parenteral,   '-',  color='#b2182b', lw=2.5,
        label='Parenteral PWID (median 72h access)')

# Annotate reported IRRs as horizontal reference lines (efficacy = 1-IRR)
# PURPOSE 1: IRR 0.00 (CI 0-0.04)
ax.axhline(1.00, color='#555', lw=1, alpha=0.6)
ax.text(0.51, 1.005, 'PURPOSE 1 AGYW: 100% (95% CI 96-100%)', fontsize=8, color='#333')
# PURPOSE 2: IRR 0.04 (CI 0.01-0.18)
ax.axhline(0.96, color='#555', lw=1, alpha=0.6)
ax.text(0.51, 0.965, 'PURPOSE 2 pooled: 96% (95% CI 82-99%)', fontsize=8, color='#333')

# Annotate subpopulation ceiling points
annotations = [
    (0.93, ceiling(0.93, 72, 24, 1.8), 'CGM US (MSM)',      '#2166ac', (8, -12)),
    (0.90, ceiling(0.90, 72, 36, 2.0), 'TGW',                '#4393c3', (8, 6)),
    (0.88, ceiling(0.88, 72, 48, 2.2), 'Black MSM US South', '#92c5de', (-120, -10)),
    (0.93, ceiling(0.93, 72, 48, 2.0), 'AGYW (SA/UG)',       '#4393c3', (8, -18)),
    (0.90, ceiling(0.90, 24, 72, 2.0), 'PWID best-case',     '#b2182b', (8, -4)),
    (0.80, ceiling(0.80, 24, 72, 2.0), 'PWID plausible',     '#b2182b', (8, -4)),
    (0.70, ceiling(0.70, 24, 72, 2.0), 'PWID realistic',     '#b2182b', (-80, -20)),
]
for fx, fy, name, col, (dx, dy) in annotations:
    ax.scatter([fx], [fy], s=50, color=col, zorder=5, edgecolor='black', lw=0.6)
    ax.annotate(name, (fx, fy), xytext=(fx + dx*0.002, fy + dy*0.005),
                fontsize=8, ha='left',
                arrowprops=dict(arrowstyle='-', color='gray', lw=0.5))

ax.set_xlabel(r'Coverage fraction $F_{\mathrm{cov}}$  (PrEP tissue level $\geq$ protective threshold)', fontsize=11)
ax.set_ylabel(r'Ceiling on PrEP efficacy  $\bar\eta_r$', fontsize=11)
ax.set_title('A. Route-specific PrEP efficacy ceiling as function of coverage',
             fontsize=11, loc='left', fontweight='bold')
ax.set_xlim(0.5, 1.0)
ax.set_ylim(0.50, 1.02)
ax.grid(True, alpha=0.3)
ax.legend(loc='lower right', fontsize=9, framealpha=0.95)

# ===================================================================
# Panel B: Joint (F_cov, F_access) parameter space for PWID
# with PURPOSE pooled 96% isocline and Taylor 2019 reference point
# ===================================================================
ax = axes[1]
fcov_grid = np.linspace(0.5, 1.0, 200)
facc_grid = np.linspace(0.0, 1.0, 200)
FCOV, FACC = np.meshgrid(fcov_grid, facc_grid)
CEIL = FCOV + (1 - FCOV) * FACC

# Contour plot of ceiling
levels = [0.60, 0.70, 0.80, 0.85, 0.90, 0.92, 0.94, 0.96, 0.98]
cs = ax.contourf(FCOV, FACC, CEIL, levels=levels, cmap='RdYlGn', alpha=0.85, extend='both')
cs2 = ax.contour(FCOV, FACC, CEIL, levels=[0.96], colors='black', linewidths=2.5)
ax.clabel(cs2, inline=True, fmt={0.96: 'PURPOSE pooled 96%'}, fontsize=9)

# Plausible parameter region for PWID (Taylor 2019 anchored)
# F_cov ∈ [0.70, 0.90] per published LAI adherence in marginalized cohorts
# F_access(24h) ∈ [0.01, 0.05] per Taylor 2019 JAIDS
from matplotlib.patches import Rectangle
rect = Rectangle((0.70, 0.01), 0.20, 0.04, fill=False, edgecolor='black',
                 linewidth=2, linestyle='--', zorder=5)
ax.add_patch(rect)
ax.annotate('PWID plausible\nparameter region\n(Taylor 2019,\nlow-LAI-adherence)',
            xy=(0.80, 0.03), xytext=(0.55, 0.25), fontsize=9, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

# Specific Taylor-2019 reference point: F_access(24h) = 0.02
ax.scatter([0.85], [0.02], s=120, color='black', marker='*', zorder=6,
           edgecolor='white', lw=1.5,
           label=r'Best-guess PWID (F$_{\mathrm{cov}}$=0.85, F$_{\mathrm{acc}}$=0.02)')

cbar = plt.colorbar(cs, ax=ax)
cbar.set_label(r'Ceiling $\bar\eta_r$  (max achievable PrEP efficacy)', fontsize=10)

ax.set_xlabel(r'Coverage fraction $F_{\mathrm{cov}}$', fontsize=11)
ax.set_ylabel(r'$F_{\mathrm{access}}(24\,\mathrm{h})$  (PEP salvage availability during gap)', fontsize=11)
ax.set_title('B. Parenteral ceiling: where the PURPOSE pooled claim transports',
             fontsize=11, loc='left', fontweight='bold')
ax.set_xlim(0.5, 1.0)
ax.set_ylim(0.0, 0.5)
ax.legend(loc='upper left', fontsize=9, framealpha=0.95)

plt.suptitle('Biological Ceiling on PrEP Efficacy — Phase 1 Extension of Demidont 2026 Finite Windows',
             fontsize=12, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'ceiling_phase1.png'), dpi=200, bbox_inches='tight')
print(f"Saved: {os.path.join(FIG_DIR, 'ceiling_phase1.png')}")
