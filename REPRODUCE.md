# Reproduction Guide

This document describes how to reproduce every table and figure in the Kassanjee
bias letter (manuscript/) from the source code in `src/`.

## 1. Environment setup

Python 3.11+ is recommended. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Pinned versions (see `requirements.txt`):

- numpy>=1.26,<2.0
- pandas>=2.3,<3.0
- matplotlib>=3.9,<4.0
- scipy>=1.12,<2.0

## 2. Input data

Processed input files are committed under `data/`. The AIDSVu 2023 raw `.xlsx`
files used to derive `city_pep_efficacy_results.csv` and the LEN PURPOSE
trial-extraction JSONs are **not redistributed** in this repository — obtain
the surveillance source data from https://aidsvu.org under their own terms.

## 3. Pipeline

Run scripts from the repository root with `.venv` activated. Each script writes
its outputs into `data/` or `figures/` via `os.path` resolution from
`__file__`, so the working directory does not matter — but staying at the repo
root keeps relative references in any logs consistent.

### 3.1 `src/build_figure.py`

- **Input:** `data/city_pep_efficacy_results.csv`
- **Output:** `data/table_34_cities.csv`, `figures/figure1.png`, `figures/figure1.pdf`
- **Purpose:** Generates Table 1 / Figure 1 of the main letter — the 34-MSA
  Kassanjee bias panel.

```bash
python src/build_figure.py
```

### 3.2 `src/gamma_site_function.py`

- **Input:** `data/city_pep_efficacy_results.csv`, `data/PrEP4U_sameday_start.json`,
  `data/LEN_implementation.json`, `data/purpose_2_full.json`, `data/purpose_4.json`
- **Output:** `data/city_gamma_table.csv`
- **Purpose:** Site-level γ extraction supporting the supplement Phase 1c v2 figure.

```bash
python src/gamma_site_function.py
```

### 3.3 `src/phase1c_v2_figure.py`

- **Input:** `data/city_gamma_table.csv`
- **Output:** `figures/fig_phase1c_v2.png`
- **Purpose:** Phase 1c v2 site-level gamma figure for the supplement.

```bash
python src/phase1c_v2_figure.py
```

### 3.4 `src/kassanjee_correction.py`

- **Input:** none (parameters defined inline from published mortality / retention literature)
- **Output:** `data/kassanjee_bias_by_pop.csv`, plus printed application table
- **Purpose:** Per-population B_IRR computation and reported→true IRR comparison.

```bash
python src/kassanjee_correction.py
```

### 3.5 `src/supplement_sensitivity.py`

- **Input:** `data/city_pep_efficacy_results.csv`
- **Output:** `data/sensitivity_summary.csv`, `figures/sensitivity_attenuation.png`
- **Purpose:** Sensitivity analysis across γ and τ for the supplement.

```bash
python src/supplement_sensitivity.py
```

### 3.6 `src/master_visualizer.py`

- **Input:** outputs of the five scripts above
- **Output:** consolidated visualization summary (writes into `figures/`)
- **Purpose:** Run last; depends on outputs from the prior steps.

```bash
python src/master_visualizer.py
```

## 4. Verification against the manuscript

After running the pipeline:

1. Compare regenerated `data/*.csv` files to the committed versions. Numerical
   columns should agree to within float-precision noise (last decimal place).
2. Compare regenerated `figures/*.png` and `figures/*.pdf` against the
   committed versions. Visual differences should be limited to font rendering;
   reported numbers, axes, and legend content should match.
3. Cross-check Table 1 row counts, Figure 1 panel counts, and supplement
   figures against the corresponding sections of `manuscript/`.

If any regenerated file differs structurally from the committed version,
investigate before assuming the pipeline is correct — file an issue.
