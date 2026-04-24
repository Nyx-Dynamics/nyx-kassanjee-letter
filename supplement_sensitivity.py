"""Sensitivity analyses for the supplement: vary alpha, gamma_base, selection factor, retention coupling."""
import numpy as np
import pandas as pd
from scipy import stats

df_base = pd.read_csv('/mnt/project/city_pep_efficacy_results.csv')

TAU = 173.0
D_VISIT_HALF = 22.5
LATE_DX_REF = 20.0

def run_parameterization(df, gamma_base, alpha, selection_amp, retention_fn):
    df = df.copy()
    df['gamma_city'] = gamma_base * (df['late_dx_pct'] / LATE_DX_REF) ** alpha
    df['gamma_enrolled'] = selection_amp * df['gamma_city']
    df['retention'] = df['late_dx_pct'].apply(retention_fn)
    df['Omega_star'] = TAU / (1 + df['gamma_enrolled'] * TAU)
    df['deflation_pct'] = (TAU / df['Omega_star'] - 1) * 100
    df['rho_screen'] = np.exp(-df['gamma_enrolled'] * TAU / 2)
    df['rho_ret'] = (1 + df['retention']) / 2
    df['rho_int'] = df['rho_ret'] * np.exp(-df['gamma_enrolled'] * D_VISIT_HALF)
    df['B_IRR'] = df['rho_int'] / df['rho_screen']
    df['IRR_atten_pct'] = (1 - df['B_IRR']) * 100
    return df

# Retention functions
def retention_coupled(late_dx):  # Primary: severity-coupled
    return max(0.93 - 0.008*(late_dx-15), 0.70)
def retention_fixed_93(late_dx):  # Fixed high (trial-setting)
    return 0.93
def retention_fixed_85(late_dx):  # Fixed moderate
    return 0.85
def retention_steep(late_dx):  # Steeper coupling
    return max(0.95 - 0.012*(late_dx-15), 0.65)

# Sensitivity grid
scenarios = []

# Primary (as in main letter)
d = run_parameterization(df_base, 5e-4, 1.2, 1.5, retention_coupled)
scenarios.append(('Primary', d))

# Vary alpha
for alpha in [1.0, 1.5]:
    d = run_parameterization(df_base, 5e-4, alpha, 1.5, retention_coupled)
    scenarios.append((f'alpha={alpha}', d))

# Vary gamma_base
for gb, lbl in [(3e-4, 'γ_base=3e-4'), (8e-4, 'γ_base=8e-4')]:
    d = run_parameterization(df_base, gb, 1.2, 1.5, retention_coupled)
    scenarios.append((lbl, d))

# Vary selection amplification
for sa, lbl in [(1.2, 'sel=1.2×'), (2.0, 'sel=2.0×')]:
    d = run_parameterization(df_base, 5e-4, 1.2, sa, retention_coupled)
    scenarios.append((lbl, d))

# Vary retention
scenarios.append(('r=0.93 fixed', run_parameterization(df_base, 5e-4, 1.2, 1.5, retention_fixed_93)))
scenarios.append(('r=0.85 fixed', run_parameterization(df_base, 5e-4, 1.2, 1.5, retention_fixed_85)))
scenarios.append(('r steep coupling', run_parameterization(df_base, 5e-4, 1.2, 1.5, retention_steep)))

# Summarize each scenario
print(f"{'Scenario':<22} {'Ω* min':<8} {'Ω* max':<8} {'defl min%':<11} {'defl max%':<11} {'B_IRR min':<11} {'B_IRR max':<11} {'atten max %':<12}")
print("-" * 100)
rows = []
for name, d in scenarios:
    row = {
        'Scenario': name,
        'Omega*_min': d['Omega_star'].min(),
        'Omega*_max': d['Omega_star'].max(),
        'defl_min': d['deflation_pct'].min(),
        'defl_max': d['deflation_pct'].max(),
        'B_IRR_min': d['B_IRR'].min(),
        'B_IRR_max': d['B_IRR'].max(),
        'atten_max_pct': d['IRR_atten_pct'].max(),
    }
    rows.append(row)
    print(f"{name:<22} {row['Omega*_min']:<8.1f} {row['Omega*_max']:<8.1f} "
          f"{row['defl_min']:<11.2f} {row['defl_max']:<11.2f} "
          f"{row['B_IRR_min']:<11.4f} {row['B_IRR_max']:<11.4f} {row['atten_max_pct']:<12.2f}")

pd.DataFrame(rows).to_csv('/home/claude/letter/sensitivity_summary.csv', index=False)

# Also compute Pearson correlation for the primary scenario
primary = scenarios[0][1]
r_defl, p_defl = stats.pearsonr(primary['late_dx_pct'], primary['deflation_pct'])
r_birr, p_birr = stats.pearsonr(primary['late_dx_pct'], primary['B_IRR'])
print(f"\nPrimary scenario correlations:")
print(f"  late-dx vs deflation%: r = {r_defl:.4f}, p = {p_defl:.2e}")
print(f"  late-dx vs B_IRR:      r = {r_birr:.4f}, p = {p_birr:.2e}")
