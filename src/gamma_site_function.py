"""
Phase 1c-v2: Site-level competing-risk hazard γ(X) for 34 AIDSVu MSAs

Derivation:
  γ_site = γ_base · M(severity_substrate)

where severity_substrate is the multivariate barrier-composite parameterization developed in companion work (Demidont, Structural Barriers preprint, doi:10.20944/preprints202601.0948.v1), and M is a
multiplicative severity index that produces γ in per-day units.

Anchors (from published US cohort hazard data):
  γ_base = 2e-4 /day    — well-resourced urban catchment baseline
                          (mortality + modest displacement + low incarceration)

Multiplier composition (additive, starting at 1.0):
  +1.0 × criminalization_excess       (late_dx above 15% threshold / 10%)
  +0.8 × housing_gap                  (Gini above 0.45, normalized to [0,1])
  +0.6 × ssp_gap                      (1 − SSP access modifier)
  +0.4 × VS_gap                       (1 − viral suppression fraction)
  +2.0 × idu_excess                   (IDU prevalence above 5% national, scaled)

Calibration check (against the user's four-site anchor values):
  Low severity (Boston-MGH-like):  M≈1.0  → γ≈2e-4
  Moderate (Phila-like):           M≈2.5  → γ≈5e-4
  Moderate-high (Miami-like):      M≈4.0  → γ≈8e-4
  Severe (Atlanta-LEN-impl-like):  M≈5.5  → γ≈1.1e-3
"""
import os
import pandas as pd
import numpy as np
from scipy.stats import lognorm

GAMMA_BASE_PER_DAY = 2.0e-4

def severity_multiplier(vs_pct, late_dx_pct, linkage_pct, idu_pct,
                         gini, poverty_pct):
    """Multivariate barrier-composite severity multiplier M(X)."""
    crim_excess     = max((late_dx_pct - 15.0) / 10.0, 0.0)
    housing_gap     = max((gini - 0.45) / 0.15, 0.0)
    # SSP access modifier (copied from city_to_model_params logic, inverted)
    ssp_access      = 1.0 - (poverty_pct/100.0/0.25)*0.3 - (1-linkage_pct/100.0)*0.3
    ssp_gap         = max(1.0 - max(ssp_access, 0.0), 0.0)
    vs_gap          = max(1.0 - vs_pct/100.0, 0.0)
    idu_excess      = max((idu_pct - 5.0) / 5.0, 0.0)

    M = 1.0 + (1.0 * crim_excess +
               0.8 * housing_gap +
               0.6 * ssp_gap +
               0.4 * vs_gap +
               2.0 * idu_excess)
    return M, {
        'crim_excess': round(crim_excess, 3),
        'housing_gap': round(housing_gap, 3),
        'ssp_gap':     round(ssp_gap, 3),
        'vs_gap':      round(vs_gap, 3),
        'idu_excess':  round(idu_excess, 3),
    }

def gamma_from_aidsvu(row):
    M, comp = severity_multiplier(
        row['viral_suppression_pct'], row['late_dx_pct'],
        row['linkage_to_care_pct'], row['idu_prevalence_pct'],
        row.get('gini', 0.47), row.get('poverty_pct', 15.0)
    )
    return GAMMA_BASE_PER_DAY * M, M, comp

# =============================================================================
# Apply to 34 AIDSVu MSAs
# =============================================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
data_path = os.path.join(project_root, 'data', 'city_pep_efficacy_results.csv')

df = pd.read_csv(data_path)
print(f"Loaded {len(df)} AIDSVu MSAs\n")

results = []
for _, row in df.iterrows():
    gamma, M, comp = gamma_from_aidsvu(row)
    results.append({
        'city': row['city'],
        'state': row['state'].replace('\\n', ' '),
        'gamma_per_day': round(gamma, 6),
        'severity_M': round(M, 3),
        **comp
    })
gdf = pd.DataFrame(results)
gdf = gdf.merge(df[['city', 'viral_suppression_pct', 'late_dx_pct',
                     'linkage_to_care_pct', 'idu_prevalence_pct',
                     'structural_delay_h']], on='city', how='left')

# =============================================================================
# Ω*, correction factor
# =============================================================================
TAU_LAG = 173.0  # days
gdf['Omega_star'] = TAU_LAG / (1 + gdf['gamma_per_day'] * TAU_LAG)
gdf['correction_factor'] = TAU_LAG / gdf['Omega_star']
gdf['incidence_deflation_pct'] = (gdf['correction_factor'] - 1) * 100

# =============================================================================
# PURPOSE/LEN trial site overlay
# =============================================================================
import json
trial_sites = {}
for jf, trial_label in [
    ('purpose_2_full.json', 'PURPOSE_2'),
    ('purpose_4.json',       'PURPOSE_4'),
    ('PrEP4U_sameday_start.json', 'PrEP4U'),
    ('LEN_implementation.json',   'LEN_Impl'),
]:
    json_path = os.path.join(project_root, 'data', jf)
    if os.path.exists(json_path):
        with open(json_path) as f:
            d = json.load(f)
        locs = d.get('protocolSection', {}).get('contactsLocationsModule', {}).get('locations', [])
        for l in locs:
            city = l.get('city', '')
            state = l.get('state', '')
            key = (city.lower(), state.lower())
            trial_sites.setdefault(key, set()).add(trial_label)
    else:
        print(f"Warning: {jf} not found in Data/")

# Map AIDSVu city names to trial site lookup
def match_trials(aidsvu_city, aidsvu_state):
    """Match AIDSVu city to trial sites; handles naming variations."""
    c = aidsvu_city.lower().replace(' ', '')
    s = aidsvu_state.lower().replace('\\n', '')
    labels = set()
    for (tc, ts), trials in trial_sites.items():
        tc_norm = tc.replace(' ', '')
        if tc_norm == c or (c in tc_norm and len(c) > 4) or (tc_norm in c and len(tc_norm) > 4):
            if s in ts or ts in s or not s or not ts:
                labels |= trials
        # Special matches: MiamiDadeCO = Miami sites, BrowardCO = Fort Lauderdale, etc
        if c == 'miamidadeco' and tc_norm in ('miami', 'miamigardens'):
            labels |= trials
        if c == 'browardco' and 'fortlauderdale' in tc_norm:
            labels |= trials
        if c == 'palmbeachco' and 'ftpierce' in tc_norm:
            labels |= trials
    return '|'.join(sorted(labels)) if labels else ''

gdf['trial_sites'] = gdf.apply(lambda r: match_trials(r['city'], r['state']), axis=1)

# Sort by gamma
gdf_sorted = gdf.sort_values('gamma_per_day').reset_index(drop=True)

# =============================================================================
# Display
# =============================================================================
print("=" * 120)
print("SITE-LEVEL γ AND Ω* FOR 34 AIDSVu MSAs")
print("=" * 120)
print(f"{'city':<13} {'state':<14} {'γ (/day)':>11} {'M':>6} {'Ω*':>7} {'Corr×':>7} {'Defl%':>7} {'Trials':<25}")
print("-" * 120)
for _, r in gdf_sorted.iterrows():
    print(f"{r['city'][:12]:<13} {r['state'][:13]:<14} {r['gamma_per_day']:>11.2e} {r['severity_M']:>6.2f} "
          f"{r['Omega_star']:>7.1f} {r['correction_factor']:>7.3f} {r['incidence_deflation_pct']:>7.2f} "
          f"{r['trial_sites']:<25}")

print()
print(f"γ range: {gdf['gamma_per_day'].min():.2e} – {gdf['gamma_per_day'].max():.2e}")
print(f"Ω* range: {gdf['Omega_star'].min():.1f} – {gdf['Omega_star'].max():.1f} days")
print(f"Correction factor range: {gdf['correction_factor'].min():.3f} – {gdf['correction_factor'].max():.3f}")
print(f"Incidence deflation range: {gdf['incidence_deflation_pct'].min():.2f}% – {gdf['incidence_deflation_pct'].max():.2f}%")

# Save
output_path = os.path.join(project_root, 'data', 'city_gamma_table.csv')
gdf_sorted.to_csv(output_path, index=False)
print(f"\nSaved: {output_path}")

# =============================================================================
# Calibration check against user's four anchor values
# =============================================================================
print()
print("=" * 120)
print("CALIBRATION AGAINST USER'S FOUR-SITE SEVERITY ANCHOR VALUES")
print("=" * 120)
anchors = [
    ("Low severity (Boston-MGH-like)",          2e-4,  167.2, 1.035, 3.5),
    ("Moderate (Phila-like)",                   5e-4,  159.2, 1.086, 8.6),
    ("Moderate-high (Miami-like)",              8e-4,  151.9, 1.139, 13.9),
    ("Severe (Atlanta-LEN-Impl-like)",          1.1e-3,145.3, 1.191, 19.1),
]
print(f"{'Scenario':<40} {'γ anchor':>10} {'Ω*':>7} {'Corr×':>7} {'Defl%':>7}")
print("-" * 120)
for name, g, O, C, D in anchors:
    print(f"{name:<40} {g:>10.2e} {O:>7.1f} {C:>7.3f} {D:>7.2f}")

# How do actual AIDSVu MSAs compare to these anchors?
print()
print("AIDSVu MSAs in each severity band:")
for lo_name, lo_g, hi_name, hi_g in [
    ('Low (<3e-4)',       0,    'Moderate',     3e-4),
    ('Moderate (3-6e-4)', 3e-4, 'Moderate-high',6e-4),
    ('Moderate-high (6-9e-4)', 6e-4, 'Severe',9e-4),
    ('Severe (>9e-4)',    9e-4, 'Off-scale',    np.inf),
]:
    mask = (gdf['gamma_per_day'] >= lo_g) & (gdf['gamma_per_day'] < hi_g)
    cities = gdf[mask]['city'].tolist()
    print(f"  {lo_name}: n={len(cities)}, cities = {cities}")
