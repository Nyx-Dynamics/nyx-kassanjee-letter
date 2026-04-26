"""
Phase 1c figure: Joint effect of Kassanjee survival bias + biological ceiling
"""
import os
import numpy as np
import matplotlib.pyplot as plt

# Path handling
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(BASE_DIR, 'Figures')
os.makedirs(FIG_DIR, exist_ok=True)

pops = [
    ("AGYW\n(PURPOSE 1)",   5e-5,  0.933, 0.020, 0.00,  "mucosal"),
    ("CGM US\n(PURPOSE 2)", 8e-5,  0.940, 0.002, 0.04,  "mucosal"),
    ("TGW global\n(PURPOSE 2)", 3e-4,  0.900, 0.016, 0.04,  "mucosal"),
    ("Black MSM\nUS South",  4e-4,  0.880, 0.036, 0.04,  "mucosal"),
    ("PWID\n(projected)",    1.2e-3, 0.75, 0.122, None, "parenteral"),
    ("PWID severe\n(Hartford-like)", 2e-3,  0.65, 0.387, None, "parenteral"),
]

TAU_HALF = 173/2
D_HALF = 22.5

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel A: Bias factor vs population
ax = axes[0]
labels = [p[0] for p in pops]
Bs = []
rho_s_list = []
rho_L_list = []
for _, g, r, _, _, _ in pops:
    rs = np.exp(-g*TAU_HALF)
    rL = (1+r)/2 * np.exp(-g*D_HALF)
    Bs.append(rL/rs)
    rho_s_list.append(rs)
    rho_L_list.append(rL)

x = np.arange(len(labels))
width = 0.35
ax.bar(x - width/2, rho_s_list, width, color='#2166ac', alpha=0.85, 
       edgecolor='black', lw=0.5, label=r'$\rho_{\mathrm{screen}}$ (screening cohort retention of recency)')
ax.bar(x + width/2, rho_L_list, width, color='#b2182b', alpha=0.85,
       edgecolor='black', lw=0.5, label=r'$\rho_{\mathrm{LEN}}$ (LEN-arm detection of infection)')

# B_IRR annotation above each pair
for i, B in enumerate(Bs):
    ax.text(i, max(rho_s_list[i], rho_L_list[i]) + 0.015,
            f'$B_{{IRR}}$={B:.3f}', ha='center', fontsize=8.5, fontweight='bold')
ax.axhline(1.0, color='black', lw=0.8, linestyle=':', alpha=0.6)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=8.5)
ax.set_ylabel('Observation probability', fontsize=11)
ax.set_ylim(0.7, 1.05)
ax.set_title(r'A. Survival-bias decomposition per subpopulation: $\rho_{\mathrm{LEN}} < \rho_{\mathrm{screen}}$ in every regime',
             fontsize=10.5, loc='left', fontweight='bold')
ax.legend(loc='lower left', fontsize=9, framealpha=0.95)
ax.grid(True, alpha=0.3, axis='y')

# Panel B: combined ceiling + bias view for each pop
ax = axes[1]
for i, (lbl, g, ret, ceil_floor, reported, route) in enumerate(pops):
    rs = np.exp(-g*TAU_HALF)
    rL = (1+ret)/2 * np.exp(-g*D_HALF)
    B = rL/rs
    color = '#2166ac' if route == 'mucosal' else '#b2182b'
    # ceiling floor as red triangle
    ax.scatter([i], [ceil_floor], marker='v', s=180, color=color, edgecolor='black', lw=0.8, zorder=5, 
               label='Biological ceiling floor' if i == 0 else None)
    if reported is not None:
        # reported IRR as square
        ax.scatter([i], [reported], marker='s', s=100, color='gray', edgecolor='black', lw=0.5, zorder=4,
                   label='Reported IRR' if i == 1 else None)
        # bias-corrected true IRR as diamond
        true_irr = reported / B
        ax.scatter([i], [true_irr], marker='D', s=80, color='white', edgecolor='black', lw=1.5, zorder=5,
                   label='Bias-corrected true IRR' if i == 1 else None)
        # connector between reported and true
        ax.plot([i, i], [reported, true_irr], 'k-', lw=0.6, alpha=0.5)
    else:
        # hypothetical 0.04 projection
        ax.scatter([i], [0.04], marker='s', s=100, color='gray', alpha=0.3, edgecolor='black', lw=0.5, zorder=4)
        true_irr = 0.04 / B
        ax.scatter([i], [true_irr], marker='D', s=80, color='white', alpha=0.3, edgecolor='black', lw=1.5, zorder=5)
        ax.annotate('projection\nif pooled', (i, 0.04), xytext=(0, -18), textcoords='offset points',
                    ha='center', fontsize=7, color='gray', style='italic')

ax.set_yscale('log')
ax.set_ylim(1e-3, 1.0)
ax.set_xticks(range(len(pops)))
ax.set_xticklabels([p[0] for p in pops], fontsize=8.5)
ax.set_ylabel('IRR (log scale)', fontsize=11)
ax.set_title('B. Joint test: reported IRR, bias-corrected true IRR, and ceiling floor',
             fontsize=10.5, loc='left', fontweight='bold')
ax.legend(loc='lower right', fontsize=9, framealpha=0.95)
ax.grid(True, alpha=0.3, which='major')
ax.axhline(0.04, color='black', lw=0.8, linestyle='--', alpha=0.5)
ax.text(5.5, 0.045, 'PURPOSE\npooled\nIRR 0.04', fontsize=8, ha='right', style='italic')

# Shade PWID region 
ax.axvspan(3.5, 5.5, alpha=0.08, color='red')
ax.text(4.5, 0.0015, 'PWID regime: TRUE IRR (even after bias correction)\nremains 3–9× below biological ceiling',
        ha='center', fontsize=9, fontweight='bold', color='#b2182b',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#b2182b'))

plt.suptitle('Phase 1c — Kassanjee Survival-Bias Correction + Biological Ceiling (Integrated)',
             fontsize=12, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig_phase1c.png'), dpi=200, bbox_inches='tight')
print(f"Saved: {os.path.join(FIG_DIR, 'fig_phase1c.png')}")
