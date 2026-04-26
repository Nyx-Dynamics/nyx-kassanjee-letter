# Selection on Testing Engagement: A Structural Bias in Cross-Sectional Incidence Estimation Using Recency Assays

Companion code, processed data, figures, and manuscript LaTeX sources for the
Demidont (2026) letter formalizing a structural bias in the Kassanjee/Gao
cross-sectional HIV incidence estimator under structural censoring, and
applying the correction to 34 high-burden US metropolitan areas.

## Brief

Cross-sectional HIV incidence estimation using recent-infection testing
algorithms (RITAs) underpins counterfactual-controlled PrEP efficacy trials.
The Kassanjee estimator assumes closed-system observability — that every
recently-infected individual within the recency window is equally present at
screening. Populations experiencing structural censoring (overdose,
incarceration, displacement, IPV, related mechanisms) violate that assumption
in a systematic and directional way.

This repository derives the effective MDRI under structural censoring,
Ω*(γ) = ∫₀ᵀ P_R(t) S_c(t) dt, the joint IRR bias factor B_IRR incorporating
both screening-cohort and intervention-arm observation probabilities, and
applies the framework to AIDSVu 2023 surveillance data across 34 US MSAs.
Within the empirical AIDSVu range, reported IRRs systematically understate
true IRRs, making interventions appear artificially superior in populations
with elevated structural hazard and correspondingly reduced trial retention.

## Repository structure

```
├── src/                  Analysis and visualization scripts (MIT)
├── data/                 Processed CSV/JSON tables (CC-BY-4.0)
├── figures/              Generated PNG/PDF figures (CC-BY-4.0)
├── manuscript/           Letter + supplement LaTeX sources, PDFs, .bib (CC-BY-4.0)
├── docs/                 Reviewer notes and analysis documents
├── requirements.txt      Pinned Python dependencies
├── REPRODUCE.md          Step-by-step reproduction guide
├── CITATION.cff          Citation metadata
├── .zenodo.json          Zenodo deposition metadata
├── LICENSE               Dual-license dispatcher
├── LICENSE-MIT           MIT license (code)
└── LICENSE-CC-BY-4.0     CC-BY-4.0 license (manuscript, figures, data)
```

## Quick start

```bash
git clone https://github.com/Nyx-Dynamics/nyx-kassanjee-letter.git
cd nyx-kassanjee-letter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/build_figure.py
python src/gamma_site_function.py
python src/phase1c_v2_figure.py
python src/kassanjee_correction.py
python src/supplement_sensitivity.py
python src/master_visualizer.py
```

See [REPRODUCE.md](REPRODUCE.md) for inputs, outputs, and verification steps.

## Companion preprints

This letter is part of a sequence on HIV prevention methods:

- Demidont AC. *The Prevention Theorem: Time-Dependent Constraints on
  Post-Exposure Prophylaxis for HIV.* Preprints. January 2026.
  doi:10.20944/preprints202601.1090.v1. Under review at Science Advances.
- Demidont AC. *Structural Barriers, Stochastic Avoidance, and Outbreak
  Risk in HIV Prevention for People Who Inject Drugs.* Preprints.
  January 2026. doi:10.20944/preprints202601.0948.v1. Under review at
  BMC Public Health.

## License

Dual-licensed:

- **Code** (`src/`) under [MIT](LICENSE-MIT).
- **Manuscript** (`manuscript/`), **figures** (`figures/`), and **processed
  data** (`data/`) under [CC-BY-4.0](LICENSE-CC-BY-4.0).
- **AIDSVu raw datasets** are not redistributed; obtain from
  https://aidsvu.org under their own terms.

See [LICENSE](LICENSE) for the dispatch summary.

## Citation

If you use this software or analysis, please cite both the software (per
[CITATION.cff](CITATION.cff)) and the medRxiv submission (DOI to be assigned
on posting).

## Competing interests

A.C. Demidont is the sole member of Nyx Dynamics LLC. No external
funding, sponsorship, or in-kind support was received for this work.

The author reports prior employment with Gilead Sciences, Inc., from
January 2020 through November 2024; all Gilead stock was fully divested
by December 2024. Employment ended prior to initiation of this research.
Gilead Sciences had no role in conception, analysis, interpretation,
writing, or the decision to submit.

## AI use disclosure

Large language model assistants (Anthropic Claude family) were used as
analysis and drafting tools during preparation of the code, the manuscript
LaTeX, and supplementary materials. All quantitative results were generated
by the deterministic Python pipeline in `src/`; all citations were verified
manually against primary sources. The author is solely responsible for the
content.
