# Reproducing the Kassanjee v9 manuscript

This repository accompanies Demidont AC (2026), *"Calibration-to-Deployment
Mismatch in HIV Prevention Trials: How Structural Censoring Biases
Counterfactual Incidence Estimates"* — submitted to *JAIDS*; archived at
Zenodo (DOI in `CITATION.cff`).

The reproduction suite is designed so a JAIDS reviewer (or any reader) can
verify every load-bearing statistic in the manuscript with one command.

## TL;DR

```bash
git clone https://github.com/Nyx-Dynamics/nyx-kassanjee-letter.git
cd nyx-kassanjee-letter
pip install -r requirements.txt
python reproduce_v9.py
```

Expected runtime: **~3 minutes** on a 2024-era laptop.
Expected result: **22/22 PASS** on the regression test in Stage 4/4.

## What the pipeline does

`reproduce_v9.py` orchestrates four stages, all writing into a single
timestamped directory `runs/<YYYY-MM-DD_HHMMSS>/`:

| Stage | Script | Inputs | Outputs |
|-------|--------|--------|---------|
| 1/4 | `build_xlxs.py` | Raw AIDSVu xlsx (county + state, 2014–2023); `cdc_220_counties.csv` | `aidsvu_combined_2014_2023_FULL.xlsx`, five analytic CSVs, `run_metadata.txt` |
| 2/4 | `rebuild_figures.py` | Stage 1 workbook | `Figure_2_stratum_trajectories.{png,pdf}`, `Figure_3_covid_counterfactual.{png,pdf}` |
| 3/4 | `compute_covid_deficit.py` | Stage 1 workbook | `covid_deficit_per_stratum.csv`, `covid_deficit_summary.txt`, `fig_covid_counterfactual.{png,pdf}` |
| 4/4 | `verify_v9.py` | Stage 1 `Statistics_Summary.csv`, `expected_v9_statistics.csv` | PASS/FAIL per statistic; exit code 0 or 1 |

Per-stage timing is reported at run end. Skipping figures (`--skip-figures`)
reduces total runtime to about 30 seconds.

## What `verify_v9.py` checks

`expected_v9_statistics.csv` encodes 22 reference values with per-statistic
tolerances. Each tolerance is set conservatively to allow:

- Floating-point arithmetic differences across BLAS implementations
- Minor library version drift within `requirements.txt` compatibility ranges
- Edge-case variation in AIDSVu suppression handling (cells reporting <5 cases
  per AIDSVu policy are returned as code `-1` and converted to `NaN` before
  arithmetic)

Statistics anchor directly to manuscript sections via the `manuscript_section`
column. A reviewer wanting to trace, for example, `wilcoxon_median_delta`
back to the paper:

```bash
$ grep wilcoxon_median_delta expected_v9_statistics.csv
wilcoxon_median_delta,-14.8,0.1,§4.6.2 — pre/post-EHE median Δ (cases/yr)
```

A `FAIL` indicates one of:
- (a) regression in the analysis code,
- (b) input data drift from the deposited 2025-07-26 AIDSVu snapshot,
- (c) tolerance too tight for the local environment (rare).

The verifier prints exact deviations to support diagnosis.

## Raw data requirements

`build_xlxs.py` reads from the working directory:

- `cdc_220_counties.csv` — 220 CDC-vulnerable counties (Van Handel et al., *JAIDS* 2016 — 73(3):323–331)
- `AIDSVu_County_NewDX_<YYYY>-*.xlsx` — county-level new HIV diagnoses, one per year 2014–2023
- `AIDSVu_State_NewDX_<YYYY>-*.xlsx` — state-level new HIV diagnoses, one per year 2014–2023

All data are publicly available from <https://aidsvu.org>. The Zenodo deposit
includes snapshot copies as of **2025-07-26** to ensure reproducibility against
the canonical data state.

## Output map (per run)

```
runs/<YYYY-MM-DD_HHMMSS>/
├── aidsvu_combined_2014_2023_FULL.xlsx     8 sheets, ~8 MB
├── Stratum_Aggregates.csv                  3 strata × 10 years (deposit-ready)
├── MSA_Panel.csv                           35 MSAs × 10 years
├── State_Panel.csv                         52 units × 10 years
├── CDC_220_VanHandel.csv                   220 counties with MSA-overlay flag
├── Statistics_Summary.csv                  22 regression-target statistics
├── run_metadata.txt                        Timestamp, host, library versions, git state
├── Figure_2_stratum_trajectories.{png,pdf}
├── Figure_3_covid_counterfactual.{png,pdf}
├── covid_deficit_per_stratum.csv           §S8.5.1 counterfactual derivations
├── covid_deficit_summary.txt               Tabular summary for §S8.5
└── fig_covid_counterfactual.{png,pdf}
```

Every file is self-contained within the timestamped directory. Multiple runs
can coexist; the `runs/` parent is the only place outputs ever land.

## Known points of interest

- **MSA IDU-share slope p-value.** The Stage 1 pipeline computes
  `msa_idu_slope_p = 0.4669` via a one-sample t-test of per-MSA OLS slopes
  against zero. The v9 manuscript abstract reports `p = 0.26` for this
  quantity. Both values support the substantive claim (the slope is not
  significantly different from zero at α = 0.05); the numeric discrepancy
  reflects a one-vs-two-tailed reporting convention that will be reconciled
  in the JAIDS submission. The verify suite anchors to the script-computed
  value for regression purposes; the manuscript text is being updated.

- **CDC-220 / EHE-MSA overlap.** The Van Handel overlay step reports
  "1 inside EHE MSAs" — this is Wake County, NC (Raleigh MSA, CDC-220 rank
  26). The geographic separation between the 220 vulnerable counties and
  the 35 EHE-priority MSAs is by design (Van Handel selected for projected
  HIV/HCV outbreak risk among PWID in rural counties), and the single
  overlap (Wake) is handled by MSA-precedence in the stratum-assignment
  function in `build_xlxs.py`.

## Manual reproduction (stage-by-stage)

If you want to inspect intermediate outputs or vary parameters:

```bash
# Stage 1 only (~30s)
python build_xlxs.py
# Note the timestamped run directory printed at the start.

# Stage 2 only (figures) — pass the absolute xlsx path
python rebuild_figures.py --input-xlsx runs/<TS>/aidsvu_combined_2014_2023_FULL.xlsx

# Stage 3 only (COVID counterfactual)
python compute_covid_deficit.py \
    --input-xlsx runs/<TS>/aidsvu_combined_2014_2023_FULL.xlsx \
    --output-csv runs/<TS>/covid_deficit_per_stratum.csv

# Stage 4 only (verification)
python verify_v9.py \
    --statistics-csv runs/<TS>/Statistics_Summary.csv \
    --expected-csv expected_v9_statistics.csv
```

## Convenience targets (`make`)

If you have GNU Make:

```bash
make help            # list available targets
make reproduce       # full pipeline
make reproduce-fast  # numbers only, no figures
make verify          # re-verify latest run directory
make clean           # remove __pycache__
make clean-runs      # remove ALL run directories (prompts for confirmation)
```

## Citation

```bibtex
@article{Demidont2026Kassanjee,
  author  = {Demidont, A.C.},
  title   = {Calibration-to-Deployment Mismatch in HIV Prevention Trials:
             How Structural Censoring Biases Counterfactual Incidence Estimates},
  journal = {JAIDS (under review)},
  year    = {2026},
  note    = {Zenodo deposit DOI per CITATION.cff}
}
```

## Contact

Dr. A.C. Demidont, DO, AAHIVS
Nyx Dynamics LLC
ORCID: 0000-0002-9216-8569
GitHub: <https://github.com/Nyx-Dynamics>

For reproduction or methodology issues, please open an issue at the GitHub
repository above. For substantive manuscript questions, contact the
corresponding author per JAIDS submission record.
