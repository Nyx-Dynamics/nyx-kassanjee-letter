# Zenodo Re-Versioning Handoff: v6 → v7

**Date prepared:** May 2026
**Source version:** v6 (April 25, 2026) — internal; not yet on Zenodo
**Target version:** v7 (May 2026)
**Existing Zenodo deposit:** DOI 10.5281/zenodo.19796212 (currently v4)
**GitHub repo:** https://github.com/Nyx-Dynamics/nyx-kassanjee-letter

---

## Why "New version" rather than "New deposit"

Use the Zenodo "New version" feature on existing record 19796212. This:

1. Preserves the Concept DOI (the parent DOI that points to all versions).
2. Creates a new version-specific DOI for v7 automatically.
3. Sets the `isNewVersionOf` relation correctly without manual metadata
   editing.
4. Avoids the Crossref-dedup problem encountered previously with the
   Preprints.org submission (a new orphan deposit would re-trigger that
   conflict).

**Do NOT create a new orphan deposit.** Use the "New version" button on
the existing record's landing page (depositor view).

---

## Pre-flight checklist (before opening Zenodo)

- [ ] v7 main letter compiled to PDF (`kassanjee_bias_letter_v7.pdf`)
- [ ] v7 supplement compiled to PDF (`kassanjee_bias_supplement_v7.pdf`)
- [ ] `Fig_2_stratum_trajectories.png` and `.pdf` generated; visually
      verified
- [ ] `Fig_3_kassanjee_invariance.png` and `.pdf` generated; visually
      verified
- [ ] All longitudinal CSV inputs present in repo and verified against
      raw AIDSVu data
- [ ] Spearman ρ = 0.9979 verified by running
      `Fig_5_kassanjee_invariance.py` (diagnostic output prints to
      stdout; check console)
- [ ] `README.md` updated with v7 section
- [ ] `CHANGELOG.md` updated with v7 entry
- [ ] `CITATION.cff` version bumped to 7.0 (DOI placeholder until
      Zenodo mints)
- [ ] Old manuscript files (`Demidont_KassanjeeBias_*_FINAL.tex/pdf`)
      removed from working tree
- [ ] Repository tagged `v7.0` and pushed to GitHub **after** all
      above items complete
- [ ] No `ρ = 0.9988` stragglers in manuscript or supplement
      (`grep -rn "0.9988" kassanjee_bias_letter_v7.tex
      kassanjee_bias_supplement_v7.tex` should return nothing; the
      v6 archived handoff file is allowed to retain it as historical
      record)

---

## File manifest for the v7 Zenodo upload

Upload all of the following to the new version. Recommended naming for
the upload form's "File name" field is exactly as listed below.

### Main deliverables (replace v4 versions on Zenodo)
- `kassanjee_bias_letter_v7.pdf`
- `kassanjee_bias_letter_v7.tex`
- `kassanjee_bias_supplement_v7.pdf`
- `kassanjee_bias_supplement_v7.tex`

### Figures
- `Fig_1_structural_hazard.png` (retained from v4; renamed from
  `Figure_1.png`)
- `Fig_2_stratum_trajectories.png` (NEW)
- `Fig_2_stratum_trajectories.pdf` (vector)
- `Fig_3_kassanjee_invariance.png` (NEW)
- `Fig_3_kassanjee_invariance.pdf` (vector)
- `Fig_S1.png` (retained from v4: site-level γ with LEN overlay)
- `Fig_S2.png` (retained from v4: archetype decomposition)

### Data files (existing + new)
- `Table_34_cities_full.csv` (existing)
- `city_gamma_table.csv` (existing)
- `kassanjee_bias_by_pop.csv` (existing)
- `sensitivity_summary.csv` (existing)
- `aidsvu_msa_newdx_panel_2014_2023.csv` (NEW: 350-observation MSA panel)
- `aidsvu_state_newdx_panel_2014_2023.csv` (NEW: 520-observation state
  panel)
- `cdc_220_counties.csv` (NEW: Van Handel 2016 FIPS list)
- `cdc_220_counties_with_msa_flag.csv` (NEW: with MSA-overlay flag)
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
- `Fig_4_stratum_trajectories.py` (NEW: produces Fig_2_*.png/pdf)
- `Fig_5_kassanjee_invariance.py` (NEW: produces Fig_3_*.png/pdf)

### Repository metadata
- `README.md` (updated for v7)
- `CHANGELOG.md` (v7 entry plus historical entries)
- `CITATION.cff` (version 7.0; DOI placeholder until minted)
- `LICENSE` (no change; CC-BY-4.0 unless v4 deposit used different)

---

## Zenodo metadata for v7

### Resource type
**Publication > Preprint** (match what v4 used; verify on the v4 record
page if uncertain).

### Title
```
Calibration-to-Deployment Mismatch in HIV Prevention Trials: How
Structural Censoring Biases Counterfactual Incidence Estimates (v7)
```

### Version
`v7.0`

### Publication date
The date of the new-version Zenodo publish (e.g., `2026-05-22`). Set
to today's date when you publish.

### Authors
- `Demidont, A.C.`
  - ORCID: `0000-0002-9216-8569`
  - Affiliation: `Nyx Dynamics LLC`

### Description (Markdown, paste into Description field verbatim)

```markdown
Version 7 of the Calibration-to-Deployment Mismatch manuscript adds
empirical anchoring for the structural-functions reframing introduced
in version 6, using the 2014–2023 AIDSVu county-level panel.

**New in v7:**

- §4.6 *Longitudinal empirical validation:* four independent analyses
  test the structural-functions reframing of §3.3.
  - Temporal stability (AR(1) φ = +0.278, test-retest r = 0.988 for
    total dx; r = 0.841 for IDU share).
  - Pre-EHE vs post-EHE Wilcoxon break-point (median Δ = −12.4
    cases/year, p < 0.0001).
  - State-vs-MSA divergence in IDU-share trends (+0.81 vs +0.14
    pp/yr, p = 0.002 vs 0.35) — consistent with PWID HIV migrating
    from EHE-priority MSAs to non-MSA jurisdictions.
  - CDC Van Handel 220-county overlay: 0/220 inside EHE MSAs (clean
    partition); IDU dx growth occurring in Stratum C (~2,900
    "other" counties, +9% 2014–2023) — direct evidence that
    point-in-time vulnerability indices are unstable surface proxies.
  - Kassanjee correction invariance test across 34 MSAs (Spearman
    ρ = 0.9979, 34/34 cities identical optimal policies; step-by-step
    policy-match rate 100% across all five cascade steps).

- §5.1 augmented paragraph: longitudinal evidence reinforces the
  LEN-deployment concerns developed in v6.

- New Figures 2 and 3: stratum trajectories and Kassanjee invariance
  scatter.

- Supplement §S8: panel construction methods, Van Handel overlay
  construction, invariance test methodology, longitudinal data and
  code availability.

- Abstract and Conclusion updated to reflect empirical anchoring.

**Unchanged from v6:**

- §3.3 SCM structural-functions reframing
- §4.1–4.5 cross-sectional bias structure and 34-MSA application
- §5.1 three-convergence operational argument
- §5.2 22.5-day biological window argument

**Reproducibility:** All code and data, including the v7 longitudinal
additions, are deposited at
https://github.com/Nyx-Dynamics/nyx-kassanjee-letter and reproducible
from publicly available AIDSVu surveillance data plus the Van Handel
et al. 2016 MMWR vulnerable-county list. The Kassanjee invariance
test additionally depends on the policy-iteration MDP framework from
the companion HIV_Prevention_PWID repository (BMC Public Health
manuscript). No individual-level or proprietary data are used.
```

### Keywords
- HIV incidence
- Kassanjee estimator
- recent-infection testing algorithm
- pre-exposure prophylaxis
- lenacapavir
- structural barriers
- PWID
- trial design
- reproducibility
- longitudinal surveillance
- AIDSVu
- EHE
- causal inference
- structural functions
- proxy variables

### Related identifiers
- `isNewVersionOf`: `10.5281/zenodo.19796212` (v4 — set automatically
  by Zenodo when using "New version" feature)
- `isSupplementTo`: the eventual JAIDS article DOI (add this after
  acceptance; leave blank for now)
- `references`:
  - `10.20944/preprints202601.1090.v1` (Finite Windows companion)
  - `10.20944/preprints202601.0948.v1` (Structural Barriers companion)

### License
`CC-BY-4.0` (confirm matches v4; if v4 used a different license,
match that to preserve consistency).

### Communities
Add to relevant Zenodo communities if applicable (e.g., open-science,
biostatistics, HIV-research). Optional; can be added post-publish.

### Funding
Same as v4: no external funding. Self-funded under Nyx Dynamics LLC.

### Reserve DOI before publishing (optional)
If you want the v7 DOI in `CITATION.cff` and `README.md` before
publishing on Zenodo, use the "Reserve DOI" button on the draft.
Update `CITATION.cff` and `README.md` with the reserved DOI, commit,
push, then publish on Zenodo with the DOI already in the
repository. Otherwise, publish first, then update.

---

## Step-by-step Zenodo workflow

1. Navigate to your v4 deposit page on Zenodo
   (https://zenodo.org/records/19796212).
2. Click **"New version"** button (visible on the depositor view at
   the top of the page).
3. Zenodo creates a draft with all v4 metadata pre-filled. Verify
   nothing leaked from v4 that shouldn't carry forward (especially
   "Version" field, "Publication date", and "Description").
4. **Delete** the v4 file attachments from the draft. Upload the v7
   file manifest listed above. Verify file count matches.
5. Update **Version** field: `v7.0`.
6. Update **Publication date** to today.
7. **Replace Description** with the v7 description block above.
8. Verify keywords list expanded as listed above.
9. Verify **Related identifiers** — `isNewVersionOf` should auto-link
   to v4. Add references as listed.
10. (Optional) Reserve DOI; update `CITATION.cff` and `README.md`
    with the reserved DOI; commit and push.
11. Click **"Save draft"**. Click **"Preview"** to inspect the landing
    page rendering.
12. Verify the new DOI (auto-assigned or reserved) appears in the
    preview metadata block.
13. Click **"Publish"**.
14. If you didn't reserve DOI in step 10: copy the published DOI,
    update `CITATION.cff` and `README.md` with the new DOI in your
    repository, commit (`git commit -am "Update CITATION and README
    with v7 Zenodo DOI"`), push.
15. Tag the repository: `git tag -a v7.0 -m "v7.0: longitudinal AIDSVu
    panel + Kassanjee invariance test"`.
16. Push the tag: `git push --tags`.

---

## Post-publish verification

- [ ] v7 Zenodo landing page resolves
- [ ] v7 DOI resolves to the new landing page
- [ ] v4 Concept DOI still resolves and shows v7 as latest version on
      the version chain widget
- [ ] All file attachments downloadable from the v7 landing page
- [ ] PDF main letter and supplement on Zenodo match what's in the
      GitHub release at tag v7.0
- [ ] `CITATION.cff` and `README.md` updated with new DOI on GitHub
- [ ] GitHub release v7.0 tag pushed and visible

---

## Cover letter language for JAIDS submission

When submitting v7 to JAIDS, include in the cover letter:

```
The manuscript and all supporting code and data are deposited at
Zenodo (DOI: 10.5281/zenodo.XXXXXXXX, v7) and GitHub
(https://github.com/Nyx-Dynamics/nyx-kassanjee-letter, tagged v7.0).
The framework is fully reproducible from publicly available AIDSVu
surveillance data plus the CDC Van Handel et al. 2016 vulnerable-
county list; no individual-level or proprietary data are used. The
policy-iteration MDP underpinning the §4.6 invariance test is
documented in the companion BMC Public Health manuscript and its
associated HIV_Prevention_PWID repository.
```

This positions the manuscript squarely for the JAIDS reproducibility
section.
