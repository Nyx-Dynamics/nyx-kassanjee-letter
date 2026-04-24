"""Figure 1 v2: retention r scaled with late-dx severity."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('/mnt/project/city_pep_efficacy_results.csv')

TAU = 173.0
GAMMA_BASE = 5e-4
ALPHA = 1.2
SELECTION_AMP = 1.5
LATE_DX_REF = 20.0
D_VISIT_HALF = 22.5

# City-specific retention: empirical pattern from published LAI-PrEP cohorts
# Milwaukee-tier (low-late-dx) ≈ 0.93 (PURPOSE 1/2 aggregate)
# Hartford-tier (high-late-dx) ≈ 0.75 (real-world LAI in marginalized cohorts)
def retention_city(late_dx_pct):
    return max(0.93 - 0.008 * (late_dx_pct - 15.0), 0.70)

df['gamma_city'] = GAMMA_BASE * (df['late_dx_pct'] / LATE_DX_REF) ** ALPHA
df['gamma_enrolled'] = SELECTION_AMP * df['gamma_city']
df['retention'] = df['late_dx_pct'].apply(retention_city)

df['Omega_star'] = TAU / (1 + df['gamma_enrolled'] * TAU)
df['deflation_pct'] = (TAU / df['Omega_star'] - 1) * 100

df['rho_screen'] = np.exp(-df['gamma_enrolled'] * TAU / 2)
df['rho_ret'] = (1 + df['retention']) / 2
df['rho_int'] = df['rho_ret'] * np.exp(-df['gamma_enrolled'] * D_VISIT_HALF)
df['B_IRR'] = df['rho_int'] / df['rho_screen']
df['IRR_attenuation_pct'] = (1 - df['B_IRR']) * 100

df = df.sort_values('late_dx_pct').reset_index(drop=True)

df[['city', 'state', 'late_dx_pct', 'gamma_enrolled', 'retention',
    'Omega_star', 'deflation_pct', 'B_IRR', 'IRR_attenuation_pct']].to_csv(
    '/home/claude/letter/table_34_cities.csv', index=False)

print(f"n cities: {len(df)}")
print(f"Late-dx range: {df['late_dx_pct'].min():.1f}% – {df['late_dx_pct'].max():.1f}%")
print(f"Retention range: {df['retention'].min():.3f} – {df['retention'].max():.3f}")
print(f"Deflation range: {df['deflation_pct'].min():.1f}% – {df['deflation_pct'].max():.1f}%")
print(f"B_IRR range: {df['B_IRR'].min():.4f} – {df['B_IRR'].max():.4f}")
print(f"IRR attenuation range: {df['IRR_attenuation_pct'].min():.2f}% – {df['IRR_attenuation_pct'].max():.2f}%")

# Figure
fig, axes = plt.subplots(1, 2, figsize=(12, 5.4))

# Panel A
ax = axes[0]
sc = ax.scatter(df['late_dx_pct'], df['deflation_pct'], s=72,
                c=df['late_dx_pct'], cmap='YlOrRd', edgecolor='black', lw=0.6,
                alpha=0.9, zorder=3)

for city_name in ['Milwaukee', 'Atlanta', 'SanJuan', 'Columbia',
                  'NewHaven', 'PalmBeachCO', 'Hartford', 'Charleston']:
    r = df[df['city'] == city_name]
    if len(r):
        r = r.iloc[0]
        nm = city_name.replace('CO', ' Co').replace('San', 'San ').replace('New', 'New ')
        off = (5, 5) if city_name != 'Hartford' else (-55, -2)
        ax.annotate(nm, (r['late_dx_pct'], r['deflation_pct']),
                    xytext=off, textcoords='offset points',
                    fontsize=8.5, fontweight='bold')

z = np.polyfit(df['late_dx_pct'], df['deflation_pct'], 1)
xs = np.linspace(df['late_dx_pct'].min(), df['late_dx_pct'].max(), 100)
ax.plot(xs, np.polyval(z, xs), '--', color='gray', alpha=0.6, lw=1.2, zorder=2)

ax.set_xlabel('Late-diagnosis percentage (AIDSVu 2023)', fontsize=11)
ax.set_ylabel(r'Kassanjee denominator inflation  $100\times(\Omega/\Omega^* - 1)$ [%]',
              fontsize=11)
ax.set_title(r'A. $\Omega^*(\gamma)$ deflation across 34 AIDSVu MSAs',
             fontsize=11, loc='left', fontweight='bold')
ax.grid(True, alpha=0.3)
ax.axhline(0, color='black', lw=0.5, alpha=0.5)

# Panel B
ax = axes[1]
ax.scatter(df['late_dx_pct'], df['IRR_attenuation_pct'], s=72,
           c=df['late_dx_pct'], cmap='YlOrRd', edgecolor='black', lw=0.6,
           alpha=0.9, zorder=3)

for city_name in ['Milwaukee', 'Atlanta', 'SanJuan', 'NewHaven',
                  'Hartford', 'Charleston', 'Columbia']:
    r = df[df['city'] == city_name]
    if len(r):
        r = r.iloc[0]
        nm = city_name.replace('CO', ' Co').replace('San', 'San ').replace('New', 'New ')
        off = (5, 5) if city_name != 'Hartford' else (-55, -6)
        ax.annotate(nm, (r['late_dx_pct'], r['IRR_attenuation_pct']),
                    xytext=off, textcoords='offset points',
                    fontsize=8.5, fontweight='bold')

z2 = np.polyfit(df['late_dx_pct'], df['IRR_attenuation_pct'], 1)
ax.plot(xs, np.polyval(z2, xs), '--', color='gray', alpha=0.6, lw=1.2, zorder=2)

ax.axhline(0, color='black', lw=1, linestyle=':', alpha=0.6)

ax.set_xlabel('Late-diagnosis percentage (AIDSVu 2023)', fontsize=11)
ax.set_ylabel(r'Reported IRR attenuation  $100\times(1 - B_{\mathrm{IRR}})$ [%]',
              fontsize=11)
ax.set_title(r'B. IRR attenuation (drug appears artificially superior)',
             fontsize=11, loc='left', fontweight='bold')
ax.grid(True, alpha=0.3)

plt.suptitle('Kassanjee bias across 34 US metropolitan areas under AIDSVu-derived structural hazard',
             fontsize=12, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('/home/claude/letter/figure1.pdf', bbox_inches='tight', dpi=300)
plt.savefig('/home/claude/letter/figure1.png', bbox_inches='tight', dpi=300)
print("Saved figure1.pdf and figure1.png")
