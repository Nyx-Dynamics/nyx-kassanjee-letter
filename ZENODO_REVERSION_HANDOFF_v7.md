# ZENODO_REVERSION_HANDOFF_v7.md

## Source → target

- **Source:** v6 of the Kassanjee letter (April 25, 2026), currently
  deposited at Zenodo as v4 (DOI: 10.5281/zenodo.19796212).
- **Target:** v7 of the Kassanjee letter (May 2026), with longitudinal
  AIDSVu panel + Kassanjee invariance test additions.

## Why "New version" rather than "New deposit"

Use the Zenodo "New version" feature on existing record 19796212. This:
1. Preserves the Concept DOI (the parent DOI that points to all versions).
2. Creates a new version-specific DOI for v7 automatically.
3. Sets the `isNewVersionOf` relation correctly without manual metadata
   editing.
4. Avoids the Crossref-dedup problem you hit with the Preprints.org
   submission (a new orphan deposit would re-trigger that conflict).

DO NOT create a new orphan deposit. Use the "New version" button on the
existing record's landing page.

## Pre-flight checklist (before opening Zenodo)

- [ ] v7 main letter compiled to PDF (`kassanjee_bias_letter_final_v7.pdf`)
- [ ] v7 supplement compiled to PDF (`kassanjee_bias_supplement_final_v7.pdf`)
- [ ] Figure_2.png + Figure_2.pdf generated and verified rendering
- [ ] Figure_3.png + Figure_3.pdf generated and verified rendering
- [ ] All longitudinal CSV inputs verified against raw AIDSVu data
- [ ] Spearman ρ = 0.9979 verified by running Fig_5_kassanjee_invariance.py
      (diagnostic output prints to stdout)
- [ ] README.md updated with v7 section
- [ ] CHANGELOG.md updated with v7 entry
- [ ] CITATION.cff version bumped to 7.0
- [ ] Repository tagged v7.0 and pushed to GitHub
- [ ] No ρ = 0.9988 stragglers anywhere
      (`grep -r "0.9988" .` should return nothing)

## File manifest for the v7 Zenodo upload

Upload all of the following to the new version:

### Main deliverables (replacing v4 versions)
- `kassanjee_bias_letter_final_v7.pdf`
- `kassanjee_bias_letter_final_v7.tex`
- `kassanjee_bias_supplement_final_v7.pdf`
- `kassanjee_bias_supplement_final_v7.tex`

### Figures (new + retained from v4)
- `Figure_1.png` (retained from v4: 34-MSA Kassanjee bias scatter)
- `Figure_2.png` (NEW: stratum trajectories 2014–2023)
- `Figure_2.pdf` (vector)
- `Figure_3.png` (NEW: Kassanjee invariance scatter)
- `Figure_3.pdf` (vector)
- `Fig_S1.png` (retained from v4: site-level γ with LEN overlay)
- `Fig_S2.png` (retained from v4: archetype decomposition)

### Data files (existing + new)
- `Table_34_cities_full.csv` (existing)
- `city_gamma_table.csv` (existing)
- `kassanjee_bias_by_pop.csv` (existing)
- `sensitivity_summary.csv` (existing)
- `aidsvu_msa_newdx_panel_2014_2023.csv` (NEW: 350-observation MSA panel)
- `aidsvu_state_newdx_panel_2014_2023.csv` (NEW: 520-observation state panel)
- `cdc_220_counties_with_msa_flag.csv` (NEW: Van Handel parser output)
- `aidsvu_220_overlay_annual_agg.csv` (NEW: stratum A/B/C aggregates)
- `kassanjee_sensitivity_test.csv` (NEW: invariance test outputs)

### Code files (existing + new)
- `build_figure.py` (existing)
- `supplement_sensitivity.py` (existing)
- `gamma_site_function.py` (existing)
- `kassanjee_correction.py` (existing)
- `phase1c_v2_figure.py` (existing)
- `build_longitudinal_panel.py` (NEW: panel construction pipeline)
- `kassanjee_invariance_test.py` (NEW: MDP invariance test)
- `Fig_4_stratum_trajectories.py` (NEW: emits Figure_2.png/pdf)
- `Fig_5_kassanjee_invariance.py` (NEW: emits Figure_3.png/pdf)

### Repository metadata
- `README.md` (updated for v7)
- `CHANGELOG.md` (v7 entry)
- `CITATION.cff` (version bump)
- `LICENSE` (no change)

## Zenodo metadata for v7

**Resource type:** Publication > Preprint (or "Other" if Zenodo defaults
differ from your v4 deposit; match whatever v4 used).

**Title:**

<!-- ============================================================ -->
<!-- HANDOFF TEXT CUT OFF HERE in the 2026-05-20 paste.            -->
<!-- Remaining sections (Title body, Description, Authors,         -->
<!-- Keywords, Related identifiers, License, Communities, etc.)    -->
<!-- still need to be filled in. See the v6 handoff               -->
<!-- (`ZENODO_REVERSION_HANDOFF.md`) for the prior version's       -->
<!-- metadata as a starting template.                              -->
<!-- ============================================================ -->
