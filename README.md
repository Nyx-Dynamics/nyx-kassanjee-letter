[README.md](https://github.com/user-attachments/files/27052468/README.md)
# Kassanjee Structural Bias

**Selection on Testing Engagement: A Structural Bias in Cross-Sectional Incidence Estimation Using Recency Assays**

Code and data for the methodological framework correcting the Kassanjee/Gao cross-sectional HIV incidence estimator for competing-risk structural censoring, applied to 34 US high-burden metropolitan areas using AIDSVu 2023 surveillance data.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19733583.svg)](https://doi.org/10.5281/zenodo.19733583)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## Overview

The Kassanjee cross-sectional incidence estimator, used in counterfactual-controlled pre-exposure prophylaxis (PrEP) efficacy trials, assumes closed-system observability of the at-risk population: every recently-infected individual is equally likely to be present at screening. Populations experiencing structural censoring — competing-risk hazards from overdose mortality, incarceration, displacement, carceral disruption of healthcare, and related mechanisms disproportionately affecting marginalized groups — violate this assumption in a systematic and directional way.

This repository implements a correction framework that:

1. **Derives the effective mean duration of recent infection under structural censoring**, $\Omega^*(\gamma) = \int_0^T P_R(t) S_c(t) dt$, where $S_c(t) = \exp(-\int_0^t \gamma(u) du)$ is the competing-risk survival function.

2. **Computes the joint bias factor on the reported incidence rate ratio**, $B_{\mathrm{IRR}}(\gamma, r) = \rho_{\mathrm{int}}/\rho_{\mathrm{screen}}$, incorporating both screening-cohort observation probability and intervention-arm retention-weighted detection.

3. **Identifies the 90-day no-prior-testing eligibility criterion** (standard in Phase 3 PrEP trials including PURPOSE 1 and PURPOSE 2) as a selection mechanism operating on the same axis (testing engagement) that drives the competing-risk hazard, compounding the bias.

4. **Applies the framework to 34 AIDSVu metropolitan areas** using late-diagnosis percentage as the empirical proxy for structural hazard, producing reproducible per-MSA correction factors.

**Full manuscript and supplementary material:** see `manuscript/` directory.

**Citation:** Demidont AC. *Selection on Testing Engagement: A Structural Bias in Cross-Sectional Incidence Estimation Using Recency Assays.* Manuscript in preparation, 2026. Archive DOI: [10.5281/zenodo.19733583](https://doi.org/10.5281/zenodo.19733583)

---

## Key results

Under primary parameterization ($\gamma_{\mathrm{base}} = 5\times 10^{-4}$/day, $\alpha = 1.2$, 1.5× selection amplification, severity-coupled retention), applied to 34 AIDSVu MSAs:

| Metric | Range across 34 MSAs |
|---|---|
| Effective MDRI $\Omega^*$ | 135.9 – 159.2 days |
| Kassanjee denominator inflation $\Omega/\Omega^*$ | 1.087 – 1.273 (+8.7% to +27.3%) |
| Joint IRR bias factor $B_{\mathrm{IRR}}$ | 0.969 – 0.999 |
| Maximum IRR attenuation | 3.1% (Hartford, CT) |
| Pearson correlation (late-dx % vs $\Omega/\Omega^*$) | $r = 0.9995$, $p < 10^{-48}$ |

The bias is **monotone in late-diagnosis percentage**, demonstrating structural rather than stochastic variation. The correction matters most in cities with the highest structural severity — the populations who can least afford to have their prevention needs misestimated.

---

## Repository structure

```
kassanjee-structural-bias/
├── README.md                            # This file
├── LICENSE                              # CC BY 4.0
├── CITATION.cff                         # Citation metadata (GitHub auto-renders)
├── requirements.txt                     # Python dependencies
├── .zenodo.json                         # Zenodo archival metadata
│
├── src/                                 # Source code
│   ├── build_figure.py                  # Main Figure 1 generator (letter)
│   ├── kassanjee_correction.py          # Core Ω* and B_IRR functions
│   ├── supplement_sensitivity.py        # Table S1 sensitivity analyses
│   ├── gamma_site_function.py           # Meyer–Kamitani multivariate γ (Table S3)
│   ├── phase1c_v2_figure.py             # Figure S2 (site-level γ + LEN overlay)
│   └── kassanjee_figure.py              # Figure S1 (subpopulation archetype)
│
├── data/                                # Input data and derived tables
│   ├── city_pep_efficacy_results.csv    # AIDSVu-derived 34-MSA base profile
│   ├── table_34_cities.csv              # Primary-parameterization correction (Table S2)
│   ├── city_gamma_table.csv             # Multivariate γ parameterization (Table S3)
│   ├── kassanjee_bias_by_pop.csv        # Subpopulation archetype factors (Table S4)
│   └── sensitivity_summary.csv          # 10-scenario sensitivity results (Table S1)
│
├── figures/                             # Generated figures (PNG + PDF)
│   ├── figure1.png / figure1.pdf        # Main letter Figure 1
│   ├── figS1.png                        # Supplement Figure S1 (archetype bias)
│   └── figS2.png                        # Supplement Figure S2 (site-level γ)
│
├── manuscript/                          # Compiled manuscript materials
│   ├── Demidont_KassanjeeBias_letter.tex
│   ├── Demidont_KassanjeeBias_letter.pdf
│   ├── Demidont_KassanjeeBias_supplement.tex
│   └── Demidont_KassanjeeBias_supplement.pdf
│
└── docs/                                # Extended documentation
    ├── METHODS.md                       # Mathematical derivations summary
    ├── PARAMETERS.md                    # Parameter values and sources
    └── REPRODUCE.md                     # Step-by-step reproduction guide
```

---

## Quick start

```bash
# Clone and install
git clone https://github.com/Nyx-Dynamics/kassanjee-structural-bias.git
cd kassanjee-structural-bias
pip install -r requirements.txt

# Generate the main letter figure from AIDSVu inputs
python src/build_figure.py

# Reproduce the full 34-MSA correction table
python src/kassanjee_correction.py

# Run all sensitivity analyses
python src/supplement_sensitivity.py

# Generate site-level γ with LEN trial-site overlay (Figure S2)
python src/gamma_site_function.py
python src/phase1c_v2_figure.py
```

All scripts are self-contained and read AIDSVu-derived inputs from `data/`. No proprietary data, no API keys, no external authentication.

---

## Mathematical framework

### Effective MDRI under structural censoring

$$\Omega^*(\gamma) = \int_0^T P_R(t)\, S_c(t)\, dt$$

Under exponential approximation $P_R(t) \approx P_0 e^{-t/\tau}$ with $\tau = 173$ d (Sedia LAg-EIA) and constant hazard $\gamma$:

$$\Omega^*(\gamma) \approx \frac{\Omega}{1 + \gamma\tau}$$

### Joint IRR bias factor

$$\widehat{\mathrm{IRR}} = \mathrm{IRR}_{\mathrm{true}} \cdot \frac{\rho_{\mathrm{int}}(\gamma, r)}{\rho_{\mathrm{screen}}(\gamma)} \equiv \mathrm{IRR}_{\mathrm{true}} \cdot B_{\mathrm{IRR}}$$

where

$$\rho_{\mathrm{screen}}(\gamma) \approx \exp(-\gamma\tau/2)$$

$$\rho_{\mathrm{int}}(\gamma, r) \approx \frac{1+r}{2}\exp(-\gamma\, d_{\mathrm{visit}}/2)$$

with $d_{\mathrm{visit}}/2 \approx 22.5$ d (13-week visit interval).

### AIDSVu-derived city-specific hazard

$$\gamma_{\mathrm{city}} = \gamma_{\mathrm{base}} \cdot \left(\frac{\text{late-dx}_{\mathrm{city}}}{\text{late-dx}_{\mathrm{national}}}\right)^\alpha$$

with $\gamma_{\mathrm{base}} = 5\times 10^{-4}$/day and $\alpha = 1.2$ in the primary parameterization. A 1.5× selection amplification is applied to reflect the 90-day testing-exclusion effect on enrolled-cohort γ relative to general-population γ.

---

## Data sources

All data are publicly available, require no registration, and no individual-level information is used.

- **AIDSVu 2023 downloadable datasets:** [https://aidsvu.org](https://aidsvu.org). Rollins School of Public Health, Emory University. Late-diagnosis percentage, viral suppression, linkage-to-care, IDU prevalence, Gini coefficients, poverty rates per MSA.
- **CDC HIV Surveillance Supplemental Report 2023:** National late-diagnosis reference value.
- **CDC National HIV Behavioral Surveillance 2023:** Testing-frequency distributions for selection amplification calibration.
- **Bureau of Justice Statistics, Prisoners in 2022:** Incarceration hazard component of γ_base.
- **ClinicalTrials.gov registry:** PURPOSE 1 (NCT04994509), PURPOSE 2 (NCT04925752), PURPOSE 4 (NCT06101342) eligibility criteria.

---

## Reproducibility

All results in the manuscript and supplement are reproducible from the code and data in this repository. The complete reproduction pipeline is:

1. `build_figure.py` produces the primary parameterization table (`table_34_cities.csv`) and main-letter Figure 1.
2. `supplement_sensitivity.py` produces the 10-scenario sensitivity analysis (`sensitivity_summary.csv`) used in Supplementary Table S1.
3. `gamma_site_function.py` produces the Meyer–Kamitani multivariate γ parameterization (`city_gamma_table.csv`) used in Supplementary Table S3.
4. `kassanjee_correction.py` produces the subpopulation archetype analysis (`kassanjee_bias_by_pop.csv`) used in Supplementary Table S4.
5. `phase1c_v2_figure.py` produces Supplementary Figure S2 (site-level γ with LEN trial-site overlay).
6. `kassanjee_figure.py` produces Supplementary Figure S1 (subpopulation bias decomposition).

Version-controlled commits corresponding to the manuscript submission are tagged as `v1.0`.

---

## Dependencies

- Python ≥ 3.9
- numpy ≥ 1.23
- scipy ≥ 1.9
- pandas ≥ 1.5
- matplotlib ≥ 3.6

Full environment specification in `requirements.txt`. Tested on Python 3.9, 3.10, 3.11, and 3.12 on macOS and Ubuntu.

---

## Author

**A.C. Demidont, DO, AAHIVS**
Nyx Dynamics LLC, Philadelphia, PA 19107
ORCID: [0000-0002-9216-8569](https://orcid.org/0000-0002-9216-8569)
Correspondence: ac.demidont@nyxdynamics.com

---

## License

This repository is licensed under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). You are free to share and adapt the material for any purpose, including commercial use, provided appropriate credit is given and changes are indicated.

See [LICENSE](LICENSE) for full terms.

---

## Citing this work

If you use this code, data, or framework in your own research, please cite:

> Demidont AC. Selection on Testing Engagement: A Structural Bias in Cross-Sectional Incidence Estimation Using Recency Assays. Manuscript in preparation, 2026.
>
> Archive: [10.5281/zenodo.19733583](https://doi.org/10.5281/zenodo.19733583)

BibTeX:
```bibtex
@software{demidont_kassanjee_2026,
  author       = {Demidont, A.C.},
  title        = {Kassanjee Structural Bias: Selection on Testing
                  Engagement in Cross-Sectional Incidence Estimation},
  year         = 2026,
  publisher    = {Zenodo},
  version      = {v1.0},
  doi          = {10.5281/zenodo.19733583},
  url          = {https://doi.org/10.5281/zenodo.19733583}
}
```

---

## Competing interests

The author reports prior employment with Gilead Sciences, Inc., from January 2020 through November 2024. All Gilead stock was fully divested by December 2024. Employment ended prior to initiation of this research. Gilead Sciences had no role in the conception, analysis, interpretation, writing, or decision to archive this work.

No external funding. Work conducted under the affiliation of Nyx Dynamics LLC, of which the author is sole owner.

---

## AI tool disclosure

Computational analyses were conducted in Python (NumPy, SciPy, Matplotlib, pandas). Large language models (Anthropic Claude) were used to support manuscript drafting and code readability review. All AI tools were used as assistive technologies only. The author retains full responsibility for design, analysis, interpretation, and conclusions.

---

## Companion work

This methodological letter is part of a broader research program on HIV prevention trial methodology:

- **Finite Prevention Windows for HIV PEP** (Demidont, under review, *Science Advances*). Derives the absorbing Markov framework for route-specific intervention limits; provides the biological ceiling framework complementary to the measurement-bias framework presented here.
- **City-level PrEP barrier extrapolation** (with J. Meyer, E. Kamitani, in review, *BMC Public Health*). Applies structural severity parameterization to US metropolitan areas; provides the empirical substrate for the multivariate γ used in Supplementary Section S4 of this work.
- **PURPOSE 4 prospective analysis** (anticipated 2028). Prospective falsification test of the combined framework at PURPOSE 4 primary completion (NCT06101342).

---

*Repository initialized April 2026. Archived on Zenodo with minted DOI for permanent citation.*

---

## Version 7 (May 2026)

This release adds longitudinal empirical validation of the
structural-functions reframing introduced in v6, using the 2014–2023
AIDSVu county-level panel.

### What's new in v7

- **Main letter §4.6:** Four independent longitudinal analyses
  (temporal stability, pre/post-EHE break-point, state-vs-MSA
  divergence, CDC-220 overlay, Kassanjee invariance test).
- **Main letter §5.1:** Augmented paragraph connecting the
  longitudinal evidence to LEN-deployment concerns.
- **New Figures 2 and 3.**
- **Supplement §S8:** Methods for the longitudinal additions.
- **Abstract and Conclusion** updated with empirical-anchoring summary.

### Key empirical result

Spearman ρ = 0.9979 across 34 high-burden US MSAs in the Kassanjee
correction invariance test, with 34/34 cities yielding identical
optimal cascade policies with and without the correction applied.
This is the empirical signature of joint structural co-determination
predicted by the SCM reframing in §3.3 — not a measurement-error
proxy relationship.

### Repository structure

Flat layout. Manuscript and supplement (`.tex` + compiled `.pdf`) at
root. Main figures (`Fig_1_*`, `Fig_2_*`, `Fig_3_*`) and supplement
figures (`Fig_S1`, `Fig_S2`) at root. Data CSVs and Python scripts at
root. No subdirectories.

### Reproduction workflow

```bash
# 1. Reproduce the longitudinal panel CSVs from AIDSVu raw .xlsx files
python build_longitudinal_panel.py --data-dir /path/to/aidsvu/xlsx \
                                   --cdc-220 cdc_220_counties.csv

# 2. Run the Kassanjee invariance test (requires companion repo)
python kassanjee_invariance_test.py

# 3. Regenerate the figures
python Fig_4_stratum_trajectories.py    # produces Fig_2_*.png/.pdf
python Fig_5_kassanjee_invariance.py    # produces Fig_3_*.png/.pdf

# 4. Compile the manuscript
pdflatex kassanjee_bias_letter_v7.tex
pdflatex kassanjee_bias_letter_v7.tex
pdflatex kassanjee_bias_supplement_v7.tex
pdflatex kassanjee_bias_supplement_v7.tex
```

### Citation

If using v7, please cite as:

```
Demidont AC. Calibration-to-Deployment Mismatch in HIV Prevention
Trials: How Structural Censoring Biases Counterfactual Incidence
Estimates (v7). Zenodo. May 2026. doi:10.5281/zenodo.XXXXXXXX
```

DOI assigned by Zenodo upon publication of the new version. See
CITATION.cff for the canonical citation metadata.

---

## Version history

- **v7 (May 2026):** Longitudinal additions; this release. See
  CHANGELOG.md.
- **v6 (April 2026):** Intermediate. SCM reframing, operational
  consequences, 22.5-day window argument.
- **v4 (March 2026):** Initial Zenodo deposit. DOI
  10.5281/zenodo.19796212.
