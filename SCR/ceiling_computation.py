"""Phase 1 Ceiling — v3 with eps_max = 1.0 (theoretical upper bound during coverage)."""
import os
import numpy as np
import pandas as pd
from scipy.stats import lognorm

TCRIT_MUCOSAL_H    = 72.0
TCRIT_PARENTERAL_H = 24.0
EPS_MAX = 1.0     # theoretical ceiling: perfect suppression during coverage
ETA_MIN = 0.0     # post-integration: zero salvage

def F_access(t_hours, median_h, gsd):
    return lognorm.cdf(t_hours, s=np.log(gsd), scale=median_h)

def ceiling_eta(F_cov, t_crit_h, access_median_h, access_gsd,
                eps_max=EPS_MAX, eta_min=ETA_MIN):
    F_acc = F_access(t_crit_h, access_median_h, access_gsd)
    eta_gap = F_acc * eps_max + (1 - F_acc) * eta_min
    return F_cov * eps_max + (1 - F_cov) * eta_gap, F_acc, eta_gap

subpops = [
    # F_cov values: PURPOSE 1/2 pop-PK appendix reports >95% of participants
    # maintain LEN above PA-IC_95. I use 0.93–0.95 for well-resourced cohorts,
    # lower for populations with documented structural access issues.
    # access_median: from Taylor 2019 JAIDS and Demidont FW S6.1 fits.
    {"label": "AGYW (SA/UG)",        "trial": "PURPOSE 1", "route": "mucosal",
     "tcrit_h": 72.0, "F_cov": 0.93, "access_median_h": 48, "access_gsd": 2.0,
     "reported_irr_vs_bhiv": 0.00},
    {"label": "CGM US (MSM)",        "trial": "PURPOSE 2", "route": "mucosal",
     "tcrit_h": 72.0, "F_cov": 0.93, "access_median_h": 24, "access_gsd": 1.8,
     "reported_irr_vs_bhiv": 0.04},
    {"label": "TGW (global)",        "trial": "PURPOSE 2", "route": "mucosal",
     "tcrit_h": 72.0, "F_cov": 0.90, "access_median_h": 36, "access_gsd": 2.0,
     "reported_irr_vs_bhiv": 0.04},
    {"label": "Black MSM US South",  "trial": "PURPOSE 2", "route": "mucosal",
     "tcrit_h": 72.0, "F_cov": 0.88, "access_median_h": 48, "access_gsd": 2.2,
     "reported_irr_vs_bhiv": 0.04},
    {"label": "PWID US (best-case)", "trial": "PURPOSE 4", "route": "parenteral",
     "tcrit_h": 24.0, "F_cov": 0.90, "access_median_h": 72, "access_gsd": 2.0,
     "reported_irr_vs_bhiv": None},
    {"label": "PWID US (plausible)", "trial": "PURPOSE 4", "route": "parenteral",
     "tcrit_h": 24.0, "F_cov": 0.80, "access_median_h": 72, "access_gsd": 2.0,
     "reported_irr_vs_bhiv": None},
    {"label": "PWID US (realistic)", "trial": "PURPOSE 4", "route": "parenteral",
     "tcrit_h": 24.0, "F_cov": 0.70, "access_median_h": 72, "access_gsd": 2.0,
     "reported_irr_vs_bhiv": None},
]

rows = []
for s in subpops:
    eta_c, F_acc, eta_gap = ceiling_eta(s["F_cov"], s["tcrit_h"],
                                         s["access_median_h"], s["access_gsd"])
    irr_floor = 1 - eta_c
    rep = s["reported_irr_vs_bhiv"]
    if rep is not None:
        violates = rep < irr_floor
        reported_str = f"{rep:.3f}"
        verdict = "VIOLATED" if violates else "consistent"
    else:
        reported_str = "(pending)"
        verdict = "—"
    rows.append({
        "Subpopulation": s["label"],
        "Trial": s["trial"],
        "Route": s["route"],
        "t_crit_h": s["tcrit_h"],
        "F_cov": s["F_cov"],
        "F_access(t_crit)": round(F_acc, 3),
        "Ceiling eta": round(eta_c, 3),
        "IRR floor": round(irr_floor, 3),
        "Reported IRR": reported_str,
        "Verdict": verdict
    })

df = pd.DataFrame(rows)
print("=" * 110)
print("BIOLOGICAL CEILING ON PrEP EFFICACY BY SUBPOPULATION (v3, eps_max = 1.0)")
print("Ceiling:  eta_bar_r  <=  F_cov  +  (1-F_cov) * F_access(t_crit_r)")
print("=" * 110)
print(df.to_string(index=False))
print()

# PWID counterfactual: what would it take to match PURPOSE pooled 96%?
print("=" * 110)
print("IF PURPOSE 4 PWID READOUT MATCHES POOLED 96% CLAIM, IT REQUIRES:")
print("=" * 110)
target_eta = 0.96
print(f"Target efficacy = {target_eta*100:.0f}%. For parenteral (t_crit = 24h):")
print(f"Ceiling = F_cov + (1-F_cov) * F_access(24h) >= {target_eta}")
print()
print(f"  {'F_cov':<10} {'Min F_access(24h) required':<30} {'Plausible for US PWID?':<30}")
print("-" * 110)
# F_cov + (1-F_cov) F_access = 0.96 → F_access = (0.96 - F_cov)/(1-F_cov)
for fcov in [0.99, 0.97, 0.95, 0.90, 0.85, 0.80, 0.75]:
    if fcov >= target_eta:
        req = 0.0
        plausible = "F_cov alone sufficient"
    elif fcov < target_eta:
        req = (target_eta - fcov) / (1 - fcov)
        # Per Taylor 2019: F_access(24h) ≈ 0.02 for PWID
        plausible = f"NO (observed F_access(24h) ≈ 0.02)"
        if req <= 0.10:
            plausible += " — tight"
    print(f"  {fcov:<10.2f} {req:<30.3f} {plausible:<30}")

print()
print("=" * 110)
print("CEILING FOR PWID AT REPORTED F_access(24h) = 0.02 (Taylor 2019)")
print("=" * 110)
print(f"  {'F_cov':<10} {'Ceiling eta':<15} {'Implied IRR floor':<20}")
print("-" * 110)
for fcov in [0.99, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70]:
    eta_c = fcov + (1 - fcov) * 0.02
    print(f"  {fcov:<10.2f} {eta_c:<15.3f} {1-eta_c:<20.3f}")

# Path handling
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'Data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'ceiling_table.csv')

try:
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved: {OUTPUT_FILE}")
except Exception as e:
    # Fallback to current dir if absolute path fails
    df.to_csv("Data/ceiling_table.csv", index=False)
    print(f"\nSaved: Data/ceiling_table.csv (fallback)")
