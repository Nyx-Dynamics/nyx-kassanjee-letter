# Calibration-to-Deployment Mismatch in HIV Prevention Trials

**How Structural Censoring Biases Counterfactual Incidence Estimates**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20344293.svg)](https://doi.org/10.5281/zenodo.20344293)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![License: MIT](https://img.shields.io/badge/Code%20License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

This repository accompanies Demidont AC (2026), *"Calibration-to-Deployment Mismatch in HIV Prevention Trials: How Structural Censoring Biases Counterfactual Incidence Estimates"* — submitted to *JAIDS*; archived at Zenodo (DOI: `10.5281/zenodo.20344293`).

---

## One-command reproduction

```bash
git clone https://github.com/Nyx-Dynamics/nyx-kassanjee-letter.git
cd nyx-kassanjee-letter
pip install -r requirements.txt
python reproduce_v9.py
```

Expected runtime: **~3 minutes** on a 2024-era laptop.
Expected result: **22/22 PASS** on the regression test against canonical v9 manuscript values.

See [`REPRODUCE.md`](REPRODUCE.md) for full reviewer documentation.

---

## What's in this repo

| Path | Purpose |
|---|---|
| `kassanjee_bias_letter_v9.tex/.pdf` | Main manuscript (submitted to *JAIDS*) |
| `kassanjee_bias_supplement_v9.tex/.pdf` | Supplementary materials |
| `build_xlxs.py` | Canonical aggregator: raw AIDSVu → workbook + analytic CSVs |
| `rebuild_figures.py` | Figure 2 (stratum trajectories) + Figure 3 (COVID counterfactual) |
| `compute_covid_deficit.py` | §S8.5 COVID counterfactual deficit derivation |
| `reproduce_v9.py` | One-command pipeline orchestrator |
| `verify_v9.py` | Regression test against `expected_v9_statistics.csv` |
| `kassanjee_correction.py` | Core Ω* correction implementation |
| `kassanjee_invariance_test.py` | 34-MSA MDP-based invariance test |
| `gamma_site_function.py` | Per-MSA γ derivation |
| `supplement_sensitivity.py` | Table S1 sensitivity sweep |
| `phase1c_v2_figure.py` | Figure S1 (site-level γ) |
| `recompute_section_4_6_stats-2.py` | §4.6 statistics regression tool |
| `expected_v9_statistics.csv` | Canonical reference values (22 statistics) |
| `cdc_220_counties.csv` | Van Handel 2016 input file |
| `requirements.txt` | Pinned dependencies |
| `REPRODUCE.md` | Reviewer-facing reproduction guide |
| `CHANGELOG.md` | Per-version change history |
| `CITATION.cff` | Machine-readable citation metadata |
| `Makefile` | Convenience targets (`make reproduce`, `make verify`) |
| `runs/<YYYY-MM-DD_HHMMSS>/` | Self-contained timestamped pipeline outputs |

---

## Canonical numerical results (v9, post-CT-fix)

Reproduced exactly by `python reproduce_v9.py`:

| Statistic | Value | §Section |
|---|---|---|
| AR(1) φ (MSA-detrended) | +0.04 | §4.6.1 |
| Test-retest r (total dx) | 0.999 | §4.6.1 |
| Test-retest r (IDU share) | 0.89 | §4.6.1 |
| Wilcoxon median Δ (pre/post-EHE) | −14.8 cases/yr, p<0.0001 | §4.6.2 |
| State IDU-share slope | +0.12 pp/yr, p=0.45 | §4.6.3 |
| MSA IDU-share slope | −0.05 pp/yr, p=0.47 | §4.6.3 |
| Stratum A trajectory (n=59) | 656 → 636 (−3.0%) | §4.6.4 |
| Stratum B trajectory (n varies, median 125) | 46 → 46 (peak 99 in 2019) | §4.6.4 |
| Stratum C trajectory (n varies, median 1,897) | 541 → 641 (+18.5%) | §4.6.4 |
| Kassanjee invariance (34-MSA) | ρ=0.9979, 34/34 identical | §4.7 |

COVID counterfactual (Figure 3 + §S8.5):

| Stratum | Pre-COVID slope | 2020–2022 deficit [95% CI] | 2023 single-year |
|---|---|---|---|
| A | −5.89/yr (NS, p=0.18) | +89 [−101, +197] | −39 (overshoot) |
| B | +13.60/yr (p=0.023) | +185 [+74, +294] | +107 |
| C | +33.37/yr (p=0.036) | +361 [+18, +528] | +225 |

---

## Cited works in this manuscript

The four-corners HIV prevention research program:

| # | Manuscript | Status |
|---|---|---|
| 1 | Synergistic Healthcare | medRxiv [10.64898/2026.02.22.26346836](https://doi.org/10.64898/2026.02.22.26346836) |
| 2 | Finite Windows | Preprints [10.20944/preprints202601.1090.v2](https://doi.org/10.20944/preprints202601.1090.v2) — under peer review at *Science Advances* |
| 3 | Structural Barriers / PWID | Preprints [10.20944/preprints202601.0948.v1](https://doi.org/10.20944/preprints202601.0948.v1) — under peer review at *BMC Public Health* |
| 4 | **Kassanjee / Calibration-to-Deployment** (this repo) | Zenodo [10.5281/zenodo.20344293](https://doi.org/10.5281/zenodo.20344293) — submitted to *JAIDS* |

---

## How to cite

```
Demidont AC. Calibration-to-Deployment Mismatch in HIV Prevention Trials: How
Structural Censoring Biases Counterfactual Incidence Estimates. Version 9.0.
Zenodo; May 22, 2026. doi:10.5281/zenodo.20344293
```

See [`CITATION.cff`](CITATION.cff) for machine-readable metadata in CFF, BibTeX, and RIS formats.

---

## License

- **Manuscript and prose content:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Code:** [MIT License](https://opensource.org/licenses/MIT)

---

## Contact

**Dr. A.C. Demidont, DO, AAHIVS**
Nyx Dynamics LLC
ORCID: [0000-0002-9216-8569](https://orcid.org/0000-0002-9216-8569)
GitHub: [@Nyx-Dynamics](https://github.com/Nyx-Dynamics)

For reproduction or methodology issues, please open an issue in this repository. For substantive manuscript questions, contact corresponding author per the *JAIDS* submission record.
