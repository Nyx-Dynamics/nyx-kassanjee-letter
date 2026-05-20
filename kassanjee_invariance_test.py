"""
kassanjee_invariance_test.py — Kassanjee correction invariance test
across 34 high-burden US MSAs, per Kassanjee letter v7 §4.6 and §S8.4.

Methodology:
  For each of 34 MSAs, runs the policy-iteration MDP described in the
  companion BMC Public Health manuscript twice:
    (a) with γ_city derived from the structural-functions parameterization
        (main letter Eq. 10): γ_city = γ_base · (L_city/L_national)^α
    (b) with γ_city = γ_base (no Kassanjee structural-severity correction)
  Compares optimal cascade policies μ*(·) by direct identity matching and
  Spearman rank correlation on value-function rankings.

Outputs:
  kassanjee_sensitivity_test.csv
    Columns: city, late_dx_pct, kassanjee_factor, V_empty_with,
             V_empty_without, V_ratio, seq_with, seq_without,
             policies_identical, first3_identical, full_seq_identical

Reports:
  - Pearson r between V_empty_with and V_empty_without
  - Spearman ρ on policy rankings
  - n cities with identical optimal sequences
  - Step-by-step policy-match rate across the 5 cascade steps

Dependencies:
  Requires the cascade-blocking MDP framework from
  github.com/Nyx-Dynamics/HIV_Prevention_PWID. Specifically, this script
  imports `run_policy_iteration` from that framework's `mdp_engine` module.
  Adjust the import path below to match your local checkout.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

# ---------------------------------------------------------------------
# Import the MDP framework from the companion repository.
# Adjust the path below to match your local clone of HIV_Prevention_PWID.
# ---------------------------------------------------------------------

COMPANION_REPO = os.path.expanduser("~/gitrepo/HIV_Prevention_PWID")
sys.path.insert(0, COMPANION_REPO)

try:
    from mdp_engine import run_policy_iteration  # noqa: E402
except ImportError:
    print(f"ERROR: Could not import mdp_engine from {COMPANION_REPO}.")
    print("Adjust COMPANION_REPO path or set PYTHONPATH to include the")
    print("companion HIV_Prevention_PWID repository.")
    sys.exit(1)

# ---------------------------------------------------------------------
# Configuration: 34-MSA late-diagnosis percentages from AIDSVu 2023.
# Pulled from Table_34_cities_full.csv in the main repo.
# ---------------------------------------------------------------------

LATE_DX_NATIONAL = 20.0          # National late-dx % reference
GAMMA_BASE = 5e-4                # Base structural hazard per day
ALPHA = 1.2                      # Convexity parameter (main letter Eq. 10)
SELECTION_AMP = 1.5              # 90-day eligibility amplification factor

CITY_LATE_DX = {
    # 34 high-burden MSAs (Detroit excluded from analysis cohort per protocol)
    "Atlanta": 19.4, "Austin": 20.6, "BatonRouge": 15.9, "Bridgeport": 18.7,
    "BrowardCO": 18.7, "Charleston": 22.8, "Charlotte": 20.0, "Columbia": 28.4,
    "Dallas": 20.0, "Denver": 20.8, "ElPaso": 17.7, "FortWorth": 20.0,
    "HamptonRoads": 20.1, "Hartford": 37.2, "Houston": 22.1, "Jackson": 14.3,
    "Jacksonville": 19.8, "KansasCity": 16.7, "LosAngeles": 19.0,
    "MiamiDadeCO": 18.2, "Milwaukee": 14.6, "NewHaven": 28.3, "NewOrleans": 17.5,
    "NewYork": 21.2, "OrangeCO": 23.3, "Orlando": 20.7, "PalmBeachCO": 25.9,
    "Phoenix": 20.2, "Raleigh": 24.1, "Richmond": 21.9, "SanAntonio": 19.9,
    "SanJuan": 16.1, "StLouis": 20.4, "Tampa": 20.0,
}


def kassanjee_factor(late_dx_pct):
    """Main letter Eq. 10: γ_city / γ_base ratio (with selection amplification)."""
    return SELECTION_AMP * (late_dx_pct / LATE_DX_NATIONAL) ** ALPHA


# ---------------------------------------------------------------------
# Main: run MDP twice per city, compare
# ---------------------------------------------------------------------

def main(out_path="kassanjee_sensitivity_test.csv"):
    rows = []
    for city, late_dx in CITY_LATE_DX.items():
        gamma_factor = kassanjee_factor(late_dx)
        gamma_with = GAMMA_BASE * gamma_factor          # Kassanjee correction applied
        gamma_without = GAMMA_BASE                       # No correction (uniform hazard)

        # Run policy iteration MDP twice
        result_with = run_policy_iteration(city=city, gamma=gamma_with)
        result_without = run_policy_iteration(city=city, gamma=gamma_without)

        V_with = result_with["V_empty"]
        V_without = result_without["V_empty"]
        seq_with = " → ".join(result_with["optimal_policy_sequence"])
        seq_without = " → ".join(result_without["optimal_policy_sequence"])

        # Step-by-step comparison
        steps_with = result_with["optimal_policy_sequence"]
        steps_without = result_without["optimal_policy_sequence"]
        all_match = (steps_with == steps_without)
        first3_match = (steps_with[:3] == steps_without[:3])

        rows.append({
            "city": city,
            "late_dx_pct": late_dx,
            "kassanjee_factor": gamma_factor,
            "V_empty_with": V_with,
            "V_empty_without": V_without,
            "V_ratio": V_with / V_without if V_without > 0 else np.nan,
            "seq_with": seq_with,
            "seq_without": seq_without,
            "policies_identical": all_match,
            "first3_identical": first3_match,
            "full_seq_identical": all_match,
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)

    # Diagnostics
    r, p_r = pearsonr(df["V_empty_without"], df["V_empty_with"])
    rho, p_rho = spearmanr(df["V_empty_without"], df["V_empty_with"])
    n_identical = df["full_seq_identical"].sum()
    n = len(df)

    print(f"\nKassanjee invariance test results:")
    print(f"  n cities: {n}")
    print(f"  Pearson r  = {r:.4f}  (p = {p_r:.2e})")
    print(f"  Spearman ρ = {rho:.4f}  (p = {p_rho:.2e})")
    print(f"  Identical optimal policies: {n_identical}/{n}")
    print(f"  V_with / V_without inflation range: "
          f"{(df['V_ratio'].min() - 1) * 100:.1f}% – "
          f"{(df['V_ratio'].max() - 1) * 100:.1f}%")
    print(f"\nOutput written to {out_path}")


if __name__ == "__main__":
    main()
