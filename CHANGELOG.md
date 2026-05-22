# Changelog

All notable changes to this repository are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v9.0] — 2026-05-22

**Zenodo DOI:** [10.5281/zenodo.20344293](https://doi.org/10.5281/zenodo.20344293)
**Submitted to:** *JAIDS*

### Fixed
- County-name normalization bug in `build_xlxs.py` that silently zeroed Connecticut Planning Region (Hartford, Bridgeport, New Haven) contributions to the 2014–2023 longitudinal MSA panel. Cross-sectional values (Figure 1, Table 1) were never affected — the bug was localized to the longitudinal county→MSA crosswalk.
- Hardcoded `n=55` literal in `compute_covid_deficit.py` summary text corrected to `n=59 counties constant`; added 2023 single-year deficits to summary block; added n-range labels to Stratum B and C for symmetry.
- MSA IDU-share slope p-value in manuscript abstract and §4.6.3: pre-CT-fix stale `p=0.26` corrected to canonical `p=0.47`.

### Added
- **COVID-era stratum-divergent counterfactual analysis** — main letter Figure 3 + supplement §S8.5 (methodology + Viguerie et al. 2024 comparison). Pre-COVID OLS counterfactual extrapolations, cumulative 2020–2022 deficits with bootstrap 95% CIs, 2023 single-year post-caveat readings. Stratum A absorbed and overshot; Strata B and C show sustained deficits significantly different from zero.
- **§1 Introduction closing paragraph** generalizing the recency-alone Kassanjee correction to the broader calibration-to-deployment mismatch framework.
- **§5.7 Conclusion closing paragraph** landing on the structural-functions / stratified-longitudinal surveillance thesis.
- **§5.1 closing paragraph** extended with COVID partition findings as a third axis of operational concern.
- **One-command reproducibility suite**: `reproduce_v9.py` (pipeline orchestrator), `verify_v9.py` (regression test), `expected_v9_statistics.csv` (22 canonical reference values), `requirements.txt`, `REPRODUCE.md`, `Makefile`.
- **Timestamped run-directory output** in `build_xlxs.py` — every invocation writes to `runs/<YYYY-MM-DD_HHMMSS>/` with companion `run_metadata.txt` (timestamp, hostname, Python/library versions, git HEAD, input file mtimes). Enables forensic diff between runs.
- **8 new bibliography entries**: Viguerie 2024 (*Sex Transm Dis*), Randall 2022 (*BMC Public Health*), DiNenno 2022 (*MMWR*), Hassan 2022 (*J Subst Abuse Treat*), Carrico 2020 (*AIDS Behav*), Cranston 2019 (*MMWR*), Hershow 2022 (*MMWR*), Cohen 2022 (*Drug Alcohol Depend Rep*).
- Figure S3 (relocated from main letter v8 Figure 3): Kassanjee invariance scatter — numerically unchanged.

### Changed
- **Canonical numeric refresh** throughout main letter and supplement, propagated from the CT-fix:
  - Stratum A IDU trajectory: 636→631 (−0.8%) → **656→636 (−3.0%)**
  - Stratum C IDU trajectory: 561→646 (+15.2%) → **541→641 (+18.5%)**
  - Wilcoxon Δ: −9.6 cases/yr (p=0.0002) → **−14.8 cases/yr (p<0.0001)**
  - AR(1) φ: +0.05 → **+0.04**
  - Test-retest r (IDU share): 0.94 → **0.89**
  - MSA IDU-share post-EHE slope: −0.08 → **−0.05 pp/yr (p=0.47)**
  - Stratum counts: A=84 → **59**; B=220 → **var 114–130 median 125**; C≈2,918 → **var 1,868–1,964 median 1,897**
- Figure 3 in main letter replaced (invariance scatter → COVID counterfactual); invariance scatter relocated to supplement as Figure S3.
- Title page metadata updated: date 2026-05-22, word count ~7,400, supplement figures 3, references 47.

### Removed
- `build_longitudinal_panel.py` — broken parallel pipeline (suppression-code contamination, name-matching failures for 8 of 59 MSA constituents). Deprecated; `build_xlxs.py` is the sole canonical aggregator.
- `build_figure.py` — hardcoded Anthropic compute paths (`/mnt/project/`, `/home/claude/letter/`); replaced by `rebuild_figures.py`.
- `Fig_4_stratum_trajectories.py` — stale legend literals (`n=84/220/2,918`) not derived from any canonical pipeline output.

### Reproducibility
- Full chain: raw AIDSVu xlsx → `build_xlxs.py` → workbook + 5 analytic CSVs → `rebuild_figures.py` + `compute_covid_deficit.py` → `verify_v9.py` regression test.
- One-command entry point: `python reproduce_v9.py`.
- Canonical run captured in `runs/2026-05-22_073404/` with full provenance metadata.
- Verified 22/22 PASS on `verify_v9.py` against `expected_v9_statistics.csv`.

---

## [v4] — 2025-10-XX  (archived)

**Zenodo DOI:** [10.5281/zenodo.19796212](https://doi.org/10.5281/zenodo.19796212)

Prior release with pre-CT-fix numbers. Superseded by v9.

---

## [v3] — 2025-09-XX  (archived)

**Zenodo DOI:** [10.5281/zenodo.19733583](https://doi.org/10.5281/zenodo.19733583)

Earlier release. Superseded by v9.
