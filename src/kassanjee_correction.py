"""
Kassanjee Estimator Survival-Bias Correction
=============================================

Formalizes the Demidont extension of the Kassanjee estimator to account for
structural censoring in both the screening cohort (via MDRI deflation) and
the LEN arm (via detection-window depletion). Produces joint bias factor and
corrected ceiling thresholds.

FRAMEWORK (Demidont A.C., extending Kassanjee 2012 / Gao 2021):

  Effective MDRI under structural censoring:
    Ω*(γ) = ∫₀^T P_R(t) · S_c(t) dt
          ≈ Ω / (1 + γτ)   under exponential P_R(t) basis (Eq. 3, main letter)

  Screening cohort observation probability (given recent infection):
    ρ_screen(γ)  ≈ exp(−γ · τ/2),   τ ≈ 173 d (Eq. 7, uniform-window basis,
                                     small-γτ approximation)

  LEN-arm observation probability (given true infection during follow-up):
    ρ_LEN(γ, ret) ≈ ρ_retention · exp(−γ · d_visit/2),   d_visit/2 ≈ 22.5 d
    where ρ_retention is retention-weighted person-time fraction (Eq. 6)

  Joint IRR bias factor:
    B_IRR(γ, ret) = ρ_LEN / ρ_screen  (Eq. 8)

  Reported IRR = True IRR × B_IRR(γ, ret)
  If B_IRR < 1: drug looks artificially superior (reported IRR < true IRR)
  If B_IRR > 1: drug looks artificially inferior

  Note on basis projection (Supplement S2.3): Eq. 3 (Ω*) and Eq. 7 (ρ_screen)
  use different P_R(t) basis projections. Both are first-order consistent in
  γτ within the empirical AIDSVu range; their basis difference is treated as
  an explicit limitation in the main letter.
"""
import os
import numpy as np
import pandas as pd

# Time constants
TAU_LAG      = 173.0   # days; LAg-EIA MDRI
D_VISIT_HALF = 22.5    # days; mean infection-to-detection delay (13-week visits)
TAU_HALF     = TAU_LAG / 2.0   # effective half-window for screening cohort

def rho_screen(gamma_per_day):
    """Screening-cohort observation probability given recent infection."""
    return np.exp(-gamma_per_day * TAU_HALF)

def rho_LEN(gamma_per_day, retention_fraction):
    """LEN-arm observation probability: retention × per-visit detection."""
    rho_retention_weighted = 1 - (1 - retention_fraction)/2   # time-weighted average
    return rho_retention_weighted * np.exp(-gamma_per_day * D_VISIT_HALF)

def bias_factor(gamma_per_day, retention_fraction):
    """IRR reported = IRR true × this factor."""
    return rho_LEN(gamma_per_day, retention_fraction) / rho_screen(gamma_per_day)

# =========================================================================
# Per-population parameterization from published mortality/incarceration data
# =========================================================================
# gamma_per_day captures combined hazard of structural censoring (death,
# incarceration, displacement, non-participation)
# retention_fraction is the LEN-arm week-52 retention from PURPOSE publications

populations = [
    {
        "label": "AGYW (PURPOSE 1, SA/UG)",
        "gamma": 5e-5,         # Low; mostly IPV femicide + pregnancy mortality
        "retention": 0.933,    # PURPOSE 1 NEJM week-52 retention
        "notes": "SA young women all-cause mortality ~5-10/1000 PY + IPV attrition"
    },
    {
        "label": "CGM US well-resourced (PURPOSE 2)",
        "gamma": 8e-5,         # Urban MSM, good healthcare access
        "retention": 0.94,     # PURPOSE 2 reported retention
        "notes": "Urban cis MSM with insurance, low structural hazard"
    },
    {
        "label": "TGW global (PURPOSE 2)",
        "gamma": 3e-4,         # Elevated: TGW homicide, housing instability, SW
        "retention": 0.90,     # Slightly lower retention in TGW subgroup
        "notes": "TGW face elevated hazard: femicide ~1.3/1000 PY in US, plus housing/SW"
    },
    {
        "label": "Black MSM US South (PURPOSE 2)",
        "gamma": 4e-4,         # Elevated: incarceration, structural racism impact
        "retention": 0.88,     # Lower retention documented in this subpop
        "notes": "Incarceration hazard ~0.10/yr, displacement, insurance gaps"
    },
    {
        "label": "PWID US (PURPOSE 4 projected)",
        "gamma": 1.2e-3,       # High: overdose + incarceration + housing
        "retention": 0.75,     # Projected from real-world LAI observational data
        "notes": "US PWID mortality ~2-3/100 PY + incarceration + displacement"
    },
    {
        "label": "PWID severe structural (Hartford-like)",
        "gamma": 2e-3,         # Worst-case
        "retention": 0.65,
        "notes": "Compounded: high IDU prevalence + criminalization + housing"
    },
]

rows = []
for p in populations:
    r_s = rho_screen(p["gamma"])
    r_L = rho_LEN(p["gamma"], p["retention"])
    B = r_L / r_s
    deflation_bHIV = (1 - r_s) * 100
    pct_IRR_shift = (B - 1) * 100
    rows.append({
        "Population":             p["label"],
        "γ (per day)":            p["gamma"],
        "Retention 52w":          p["retention"],
        "ρ_screen":               round(r_s, 4),
        "ρ_LEN":                  round(r_L, 4),
        "B_IRR":                  round(B, 4),
        "bHIV deflation %":       round(deflation_bHIV, 2),
        "IRR shift %":            round(pct_IRR_shift, 2),
        "Direction":              "drug looks better" if B < 1 else "drug looks worse" if B > 1.01 else "neutral"
    })

df = pd.DataFrame(rows)
print("=" * 115)
print("KASSANJEE SURVIVAL-BIAS CORRECTION BY PURPOSE SUBPOPULATION")
print("=" * 115)
print(df.to_string(index=False))

# =========================================================================
# Apply the bias correction to reported PURPOSE IRRs and compare to ceiling
# =========================================================================
print()
print("=" * 115)
print("APPLICATION TO PURPOSE PUBLISHED IRRs AND CEILING COMPARISON")
print("=" * 115)

# Reported IRRs
irr_P1 = 0.00   # PURPOSE 1 point est; CI upper 0.04
irr_P2 = 0.04   # PURPOSE 2 point est; CI upper 0.18

# Per-population: reported → true IRR via B_IRR, compare to ceiling floor
pop_to_reported = {
    "AGYW (PURPOSE 1, SA/UG)":              irr_P1,
    "CGM US well-resourced (PURPOSE 2)":    irr_P2,
    "TGW global (PURPOSE 2)":               irr_P2,
    "Black MSM US South (PURPOSE 2)":       irr_P2,
}

# Biological ceiling floors from Phase 1b
ceiling_floors = {
    "AGYW (PURPOSE 1, SA/UG)":              0.020,
    "CGM US well-resourced (PURPOSE 2)":    0.002,
    "TGW global (PURPOSE 2)":               0.016,
    "Black MSM US South (PURPOSE 2)":       0.036,
}

for pop in pop_to_reported:
    # lookup bias factor
    row = next(r for r in rows if r["Population"] == pop)
    B = row["B_IRR"]
    IRR_rep = pop_to_reported[pop]
    IRR_true = IRR_rep / B   # invert: reported = true × B, so true = reported/B
    ceil = ceiling_floors[pop]
    consistent = IRR_true >= ceil
    print(f"\n{pop}")
    print(f"  Reported IRR:            {IRR_rep:.3f}")
    print(f"  B_IRR (bias factor):     {B:.3f}")
    print(f"  TRUE IRR (bias-corrected): {IRR_true:.3f}")
    print(f"  Ceiling floor (Phase 1b):  {ceil:.3f}")
    print(f"  Consistent with ceiling:   {'YES' if consistent else 'NO — TRUE IRR below biological floor'}")

# PWID case
print()
print("=" * 115)
print("PWID PROJECTION (PURPOSE 4): worst case with structural bias")
print("=" * 115)
for pop_name in ["PWID US (PURPOSE 4 projected)", "PWID severe structural (Hartford-like)"]:
    row = next(r for r in rows if r["Population"] == pop_name)
    B = row["B_IRR"]
    # If PURPOSE 4 reports same pooled 0.04
    hypothetical_reported = 0.04
    true_irr = hypothetical_reported / B
    print(f"\n{pop_name}:")
    print(f"  B_IRR = {B:.3f}, bHIV deflation = {row['bHIV deflation %']:.1f}%")
    print(f"  If PURPOSE 4 reports IRR = 0.04 (pooled-compatible),")
    print(f"  the TRUE IRR (bias-corrected) = {true_irr:.3f}")
    print(f"  Ceiling floor (Phase 1b, best US city PWID):  0.122")
    print(f"  Ceiling floor (Phase 1b, Hartford-type PWID): 0.387")
    print(f"  Consistent with Milwaukee-tier ceiling? {'YES' if true_irr >= 0.122 else 'NO'}")
    print(f"  Consistent with Hartford-tier ceiling?  {'YES' if true_irr >= 0.387 else 'NO'}")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'kassanjee_bias_by_pop.csv')

os.makedirs(DATA_DIR, exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False)
print(f"\nSaved: {OUTPUT_FILE}")
