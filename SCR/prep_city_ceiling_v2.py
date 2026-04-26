"""
PrEP Ceiling by City × Subpopulation — v2 with proper population stratification

TWO SUBPOPULATION MODELS per city:
  General population:    uses city structural_delay_h directly
  PWID subpopulation:    additional delay per Taylor 2019 (median 72h anchored)

CALIBRATION:
  F_cov,PrEP (general,X)   = 0.93 − 0.007·(Δt_X−2) − 0.05·IDU_frac_X
  F_cov,PrEP (PWID,X)      = 0.85 − 0.010·(Δt_X−2) − 0.15·IDU_frac_X
     (PWID baseline 0.85 from open-label LAI persistence in marginalized cohorts;
      stronger IDU weighting because PWID are directly exposed to IDU-associated
      network-level structural violence)

  Median access delay (general, X)   = Δt_X
  Median access delay (PWID, X)       = max(40, Δt_X·3)
     (PWID face ≥40h baseline delay per Taylor 2019 + multiplicative scaling
      with city structural severity; the 3× scaling approximates the PWID-to-
      general ratio documented in Rapoport 2020 and Mayer 2022)

CEILINGS:
  η̄_gen(X)  = F_cov,gen(X)  + (1 − F_cov,gen)  · F_access(72h | median_gen)
  η̄_PWID(X) = F_cov,PWID(X) + (1 − F_cov,PWID) · F_access(24h | median_PWID)

COMPARISONS:
  PURPOSE 2 pooled IRR = 0.04 (96% efficacy, mucosal-dominant)
  PURPOSE 4 pending; ceiling prediction delivered here
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import lognorm

# Path handling
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'Data')
INPUT_FILE = os.path.join(DATA_DIR, 'city_pep_efficacy_results.csv')
OUTPUT_FILE = os.path.join(DATA_DIR, 'city_prep_ceiling_v2.csv')

if not os.path.exists(INPUT_FILE):
    # Fallback to current dir Data
    INPUT_FILE = 'Data/city_pep_efficacy_results.csv'
    OUTPUT_FILE = 'Data/city_prep_ceiling_v2.csv'

df = pd.read_csv(INPUT_FILE)
df['idu_frac'] = df['idu_prevalence_pct'] / 100.0

GSD = 2.0
EPS_MAX = 1.0

# -----------------------------------------------------------------------------
# General-population model (mucosal-dominant, PURPOSE 1/2-relevant)
# -----------------------------------------------------------------------------
def compute_general_params(df):
    struct_delay = df['structural_delay_h']
    idu_frac = df['idu_frac']
    
    # Vectorized F_cov_gen
    f_cov = 0.93 - 0.007 * np.maximum(struct_delay - 2, 0) - 0.05 * idu_frac
    df['F_cov_gen'] = np.maximum(f_cov, 0.65)
    
    # Vectorized median_access_gen
    df['median_access_gen'] = np.maximum(struct_delay, 0.5)
    
    # Vectorized F_access_72h_gen
    df['F_access_72h_gen'] = lognorm.cdf(72, s=np.log(GSD), scale=df['median_access_gen'])
    
    df['ceiling_gen'] = df['F_cov_gen'] + (1 - df['F_cov_gen']) * df['F_access_72h_gen'] * EPS_MAX
    df['irr_floor_gen'] = 1 - df['ceiling_gen']

compute_general_params(df)

# -----------------------------------------------------------------------------
# PWID subpopulation model (parenteral, PURPOSE 4-relevant)
# -----------------------------------------------------------------------------
def compute_pwid_params(df):
    struct_delay = df['structural_delay_h']
    idu_frac = df['idu_frac']
    
    # Vectorized F_cov_PWID
    f_cov = 0.85 - 0.010 * np.maximum(struct_delay - 2, 0) - 0.15 * idu_frac
    df['F_cov_PWID'] = np.maximum(f_cov, 0.55)
    
    # Vectorized median_access_PWID
    df['median_access_PWID'] = np.maximum(40.0, struct_delay * 3.0)
    
    # Vectorized F_access
    log_gsd = np.log(GSD)
    df['F_access_24h_PWID'] = lognorm.cdf(24, s=log_gsd, scale=df['median_access_PWID'])
    df['F_access_72h_PWID'] = lognorm.cdf(72, s=log_gsd, scale=df['median_access_PWID'])
    
    df['ceiling_PWID'] = df['F_cov_PWID'] + (1 - df['F_cov_PWID']) * df['F_access_24h_PWID'] * EPS_MAX
    df['irr_floor_PWID'] = 1 - df['ceiling_PWID']

compute_pwid_params(df)

# -----------------------------------------------------------------------------
# Transportability test
# -----------------------------------------------------------------------------
PURPOSE_POOLED_IRR = 0.04

df['PURPOSE_transports_gen']  = df['irr_floor_gen']  <= PURPOSE_POOLED_IRR
df['PURPOSE_transports_PWID'] = df['irr_floor_PWID'] <= PURPOSE_POOLED_IRR

df_sorted = df.sort_values('structural_delay_h')

print("=" * 130)
print("CITY-STRATIFIED PrEP CEILING — TWO-POPULATION MODEL (n=34 AIDSVu MSAs)")
print("=" * 130)
print(f"{'City':<13} {'ΔtStr':<6} {'IDU%':<6} {'Fcv_gen':<8} {'F72gen':<7} {'Ceil_gen':<9} "
      f"{'Fcv_PWID':<9} {'MedPWID':<8} {'F24_PWID':<9} {'Ceil_PWID':<10} {'IRR_PWID':<9} "
      f"{'P2→gen?':<9} {'P2→PWID?':<9}")
print("-" * 130)
for _, r in df_sorted.iterrows():
    print(f"{r['city'][:12]:<13} {r['structural_delay_h']:<6.1f} {r['idu_prevalence_pct']:<6.1f} "
          f"{r['F_cov_gen']:<8.3f} {r['F_access_72h_gen']:<7.3f} {r['ceiling_gen']:<9.3f} "
          f"{r['F_cov_PWID']:<9.3f} {r['median_access_PWID']:<8.1f} {r['F_access_24h_PWID']:<9.3f} "
          f"{r['ceiling_PWID']:<10.3f} {r['irr_floor_PWID']:<9.3f} "
          f"{'YES' if r['PURPOSE_transports_gen'] else 'NO':<9} "
          f"{'YES' if r['PURPOSE_transports_PWID'] else 'NO':<9}")

print()
print("=" * 100)
print("SUMMARY — TRANSPORTABILITY OF POOLED PURPOSE IRR = 0.04")
print("=" * 100)
n_gen = df['PURPOSE_transports_gen'].sum()
n_pwid = df['PURPOSE_transports_PWID'].sum()
print(f"General population (mucosal): transports to {n_gen}/34 cities ({100*n_gen/34:.0f}%)")
print(f"PWID (parenteral):            transports to {n_pwid}/34 cities ({100*n_pwid/34:.0f}%)")
print()
print(f"General ceiling range: {df['ceiling_gen'].min():.3f} – {df['ceiling_gen'].max():.3f}")
print(f"PWID ceiling range:    {df['ceiling_PWID'].min():.3f} – {df['ceiling_PWID'].max():.3f}")
print()
print(f"IRR floor range (general, mucosal): {df['irr_floor_gen'].min():.4f} – {df['irr_floor_gen'].max():.4f}")
print(f"IRR floor range (PWID, parenteral): {df['irr_floor_PWID'].min():.4f} – {df['irr_floor_PWID'].max():.4f}")

try:
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved: {OUTPUT_FILE}")
except Exception as e:
    print(f"\nError saving to {OUTPUT_FILE}: {e}")

# -----------------------------------------------------------------------------
# Visualization
# -----------------------------------------------------------------------------
def plot_results(df):
    FIG_DIR = os.path.join(BASE_DIR, 'Figures')
    os.makedirs(FIG_DIR, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    df_sorted = df.sort_values('ceiling_PWID')
    y_pos = np.arange(len(df_sorted))
    
    ax.barh(y_pos - 0.2, df_sorted['ceiling_gen'], height=0.4, label='General (Mucosal)', color='skyblue')
    ax.barh(y_pos + 0.2, df_sorted['ceiling_PWID'], height=0.4, label='PWID (Parenteral)', color='salmon')
    
    ax.axvline(0.96, color='red', linestyle='--', label='PURPOSE Pooled (96%)')
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted['city'])
    ax.set_xlabel('Biological Efficacy Ceiling')
    ax.set_title('PrEP Efficacy Ceiling by City and Population')
    ax.legend()
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    fig_path = os.path.join(FIG_DIR, 'prep_ceiling_summary.png')
    plt.savefig(fig_path, dpi=300)
    print(f"Saved summary figure to: {fig_path}")

plot_results(df)
