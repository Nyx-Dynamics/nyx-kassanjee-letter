# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [7.0.0] – 2026-05-XX

### Added
- Main letter §4.6 (NEW): Longitudinal empirical validation of the
  structural-functions reframing. Four analyses: AR(1) temporal
  stability (φ = +0.278, half-life ≈ 0.54 yr), pre-EHE vs post-EHE
  within-MSA Wilcoxon break-point (median Δ = −12.4 cases/year,
  p < 0.0001), state-vs-MSA divergence in IDU-share trends
  (+0.81 vs +0.14 pp/yr, p = 0.002 vs 0.35), CDC Van Handel 220-county
  overlay (0/220 inside EHE MSAs; Stratum C growth +9%), and Kassanjee
  correction invariance test across 34 MSAs (Spearman ρ = 0.9979,
  34/34 cities, step-by-step policy-match rate 100%).
- Main letter §5.1: Appended paragraph reinforcing operational concerns
  with longitudinal evidence on geographic migration of PWID HIV burden
  and CDC-220 staleness.
- Main letter Figure 2: Stratum-aggregate longitudinal trajectories
  2014–2023.
- Main letter Figure 3: Kassanjee correction invariance scatter and
  step-level policy-match panel.
- Main letter abstract: Extended Results section with longitudinal
  findings.
- Main letter Conclusion: Empirical-anchoring summary sentence.
- Supplement §S8 (NEW): Longitudinal AIDSVu panel construction methods,
  temporal trend tests, Van Handel overlay construction, Kassanjee
  invariance test methodology.
- Data files (NEW):
  `aidsvu_msa_newdx_panel_2014_2023.csv`,
  `aidsvu_state_newdx_panel_2014_2023.csv`,
  `cdc_220_counties.csv`,
  `cdc_220_counties_with_msa_flag.csv`,
  `aidsvu_220_overlay_annual_agg.csv`,
  `kassanjee_sensitivity_test.csv`.
- Code files (NEW):
  `build_longitudinal_panel.py`,
  `kassanjee_invariance_test.py`,
  `Fig_4_stratum_trajectories.py`,
  `Fig_5_kassanjee_invariance.py`.

### Changed
- Supplement §S8 (Code and data availability) renumbered to §S9.
- Code listing in (new) §S9 expanded to include longitudinal scripts
  and CSV outputs.
- Bibliography (main letter): Added Demidont structural barriers
  companion (`demidont_barriers_synergy`).
- Bibliography (supplement): Added Van Handel et al. 2016 MMWR.
- Repository file structure normalized to flat layout (matches actual,
  not the prior hierarchical README description).
- Old manuscript files (`Demidont_KassanjeeBias_*_FINAL.tex`) removed
  from working tree; v4 retained in git history at v4.0 tag and on
  Zenodo at DOI 10.5281/zenodo.19796212.

### Note on reproducibility
All four longitudinal analyses are fully reproducible from publicly
available AIDSVu surveillance data (2014–2023 county-level files) plus
the Van Handel et al. 2016 MMWR 220-county FIPS list. The Kassanjee
invariance test additionally requires the policy-iteration MDP
framework from the companion HIV_Prevention_PWID repository (BMC
Public Health manuscript). No individual-level or proprietary data are
used at any point.

## [6.0.0] – 2026-04-25 (intermediate)

### Added
- Main letter §3.3: SCM structural-functions reframing with full
  citation chain (Pearl, Kuroki-Pearl, Wang-Blei, Miao, Tchetgen
  Tchetgen).
- Main letter §4.4: Boundary behavior and operational-envelope
  characterization.
- Main letter §5.1: Operational consequences in network-clustered
  populations (three-convergence argument: testing failure, network
  density, empirical outbreak occurrence).
- Main letter §5.2: 22.5-day biological window argument anchored to
  Fiebig II.

### Changed
- Bibliography expanded with LEN resistance pharmacology (Wirden 2024,
  Pennetzdorfer 2026, Briganti 2025), 2025 WHO LEN guidance, PrEP4U
  pragmatic trial, and 2025 CDC nPEP guidelines (Tanner et al. MMWR).

## [5.0.0] – 2026-04 (skipped; rolled into 6.0)

## [4.0.0] – 2026-03

Initial Zenodo deposit (10.5281/zenodo.19796212). Cross-sectional
34-MSA Kassanjee bias analysis with single-variable late-dx
parameterization, sensitivity analyses, multivariate composite,
subpopulation archetype analysis, 1.5× selection amplification
derivation. Companion to BMC Public Health structural barriers
manuscript and Science Advances Prevention Theorem manuscript.

## [3.0.0] – 2026-02

Internal version (10.5281/zenodo.19733583). Superseded by v4.
