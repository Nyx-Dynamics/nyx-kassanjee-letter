# Decisions AC Must Adjudicate Before Manuscript Re-Patch

The audit produced four findings serious enough that they cannot be resolved by Claude Code alone. They are interpretive (about what to claim in the manuscript) or scope (about whether to fix code now or document limitations), and only AC can decide.

Read `audit_report.md` first if you have not already — the headline finding is that **the pipeline is NOT stable per the audit definition.** Determinism passes, but transparency, honest counts, and anchored constants all have failures.

---

## Decision 1 — Which pipeline is authoritative?

The handoff JSON asked me to "confirm the canonical CSV supersedes the handoff JSON." I cannot give a clean yes.

The two outputs come from materially different pipelines:

| Source | Method | Stratum B 2019 IDU peak | Suppression handling |
|---|---|---|---|
| `build_longitudinal_panel.py` → freshly-uploaded CSVs | `Cases × Percent / 100`, naïve name match | 94.5 | -1/-2/-9 kept as integers (BROKEN) |
| `build_xlxs.py` → `aidsvu_combined_2014_2023_FULL.xlsx` | Integer IDU Cases sum, FIPS match | 99 | -1/-2/-9 → NaN (CORRECT) |
| AC's manual integer rebuild | Integer IDU Cases sum | 99 | n/a |

`build_xlxs.py` and AC's manual rebuild **agree exactly** on Stratum B 2014–2023 (46, 38, 33, 79, 93, 99, 43, 66, 84, 46). The canonical CSV from `build_longitudinal_panel.py` is systematically 2.5–5 IDU lower per year because suppression −1 codes flow through the arithmetic.

**Three options:**

- **(a) Adopt `build_xlxs.py` xlsx as authoritative.** Cite endpoints 636/631/46/46/561/646 with the year-varying B trajectory above. Reasoning: that pipeline does suppression correctly and matches AC's independent rebuild. Cost: re-do whatever manuscript text was based on the canonical CSV.
- **(b) Adopt the canonical CSV as authoritative and disclose limitations.** Cite 628/624/44/42/614/689 with the slightly-lower trajectory. Add a Supplement subsection naming the suppression bug and the 8 missing MSA constituents. Defensible because the bias is small and the qualitative findings (peak 2019, post-launch dip) survive. Cost: a paragraph of confession in the supplement.
- **(c) Fix `build_longitudinal_panel.py` and re-run.** Treat both current outputs as superseded by the patched output. Cost: code work outside this audit's scope; needs to verify the fix matches `build_xlxs.py` (likely will).

**My recommendation: (a) or (c).** (b) leaves a known-broken pipeline citing as canonical, and at JAIDS-grade peer review someone will ask why the suppression codes survived to the sums.

---

## Decision 2 — How should the manuscript report `n` counties per stratum?

The handoff said: 84 / 219 / 2,918. None of those match any actual pipeline output.

Three real options exist:

- **`n=84` framing (handoff JSON):** Constituency claim — "84 counties that constitute the 35 EHE-priority MSAs." Source uncertain; doesn't match either pipeline. **Recommend abandoning.**
- **`n=51` framing (canonical CSV):** "51 counties name-matched in AIDSVu." Literally true of the CSV but the value is constant across years because of name-match BUGS, not because of stable reporting. Citing this without acknowledging the missing 8 MSA constituents is misleading.
- **`n=55` framing (`build_xlxs.py` xlsx):** "55 counties identified via FIPS." Matches the correct MSA constituency. Constant across years because the FIPS set is frozen from 2023.
- **Year-varying framing for B and C:** report as a range (e.g., Stratum B n=114–130 across 2014–2023) rather than a single constant. Most defensible if the manuscript is going to JAIDS where this kind of pedantic reporting helps with reviewer trust.

**My recommendation: combine.** Stratum A constituency claim ("55 counties across 35 MSAs, FIPS list in Supplement"); Stratum B/C year-varying ("median n=125 / median n=1900, full year-by-year table in Supplement"). This is transparent and survives scrutiny.

---

## Decision 3 — Wake County NC narrative

Both pipelines put Wake into Stratum A correctly (it's in the Raleigh MSA constituency). It is flagged `in_msa=True, msa_name=Raleigh` in `cdc_220_counties_with_msa_flag.csv`. Wake is the SOLE overlap between the CDC-220 vulnerable list and the 35 EHE-priority MSAs.

This is a useful narrative beat for the supplement — it operationalizes the "Stratum A counties can also be high-vulnerability" claim with a single named example. It is not a contamination issue.

**Three options:**

- **(a) Drop Wake from narrative entirely.** Simplest. Lose a concrete example.
- **(b) Retain in supplement only.** "Of the 220 CDC-vulnerable counties, exactly 1 (Wake County NC, in the Raleigh MSA) overlaps the 35 EHE-priority MSA constituencies and is assigned to Stratum A." One sentence. Clean.
- **(c) Footnote in main text.** Same content as (b), but in main letter Figure 2 caption.

**My recommendation: (b).** It demonstrates the partition logic explicitly, takes one sentence, and the alternative (silently absorbing Wake into Stratum A) is less defensible if a reviewer cross-references the cdc_220 list.

---

## Decision 4 — How to frame the Stratum B trajectory

The "flat 46→46 across decade" claim in the prior handoff is **not just wrong, it is a cherry-pick.** The endpoints (46 in 2014, 46 in 2023) happen to coincide; the trajectory in between varies from 33 (2016) to 99 (2019). Stating "flat" reads either careless or deceptive.

Three options (handoff Task 6 listed these; I am ordering by manuscript impact):

- **(a) Strict endpoint-only: "44→42, essentially unchanged"** [canonical CSV] or "46→46, essentially unchanged" [xlsx]. Defensible only if you genuinely don't care about the in-between. Reviewers will pull the trajectory data and ask why the peak was hidden.
- **(b) Honest characterization: endpoints + peak + range.** "2014 = 46; 2019 peak = 99 (≈2.2× endpoint); 2023 = 46; post-launch trough 2020 = 43." Defensible and accurate.
- **(c) Use the 2019 peak as supporting evidence for structural-functions / latent-U framing.** "Stratum B's IDU diagnoses peaked at 99 in 2019 — the EHE launch year — and collapsed 57% by 2020. This temporal coincidence with both the EHE launch and the COVID-19 onset is precisely the kind of structurally-driven oscillation that γ-as-constant models miss." This converts the inconvenient peak into a load-bearing finding.

**My recommendation: (c), but only if `build_xlxs.py` is adopted as canonical.** The (c) framing requires the 99 peak to land cleanly in the supplement, with year-by-year values in a table. The canonical CSV's 94.5 peak undermines the narrative force slightly. If sticking with the canonical CSV, (b) is the floor.

---

## Followup engineering items (DO NOT act on without AC approval)

These are out of scope for this audit but are obvious from the findings. Listed here for AC's reference, not as a TODO:

1. Fix `build_longitudinal_panel.py` suppression handling: convert -1/-2/-9 to NaN before any arithmetic.
2. Fix `build_longitudinal_panel.py` MSA_COUNTY_MAP keys: import `build_xlxs.py`'s keys (with literal suffixes) and handle embedded newlines in AIDSVu column entries.
3. Decide whether `build_longitudinal_panel.py` and `build_xlxs.py` should be merged into one canonical script. Currently they implement two different methods and one is broken.
4. `Fig_4_stratum_trajectories.py` — replace hard-coded legend `n=` literals with values pulled from the input CSV's `n_counties_reporting` column (or from a metadata header).
5. `build_figure.py` — replace `/mnt/project/` and `/home/claude/` paths with relative paths; document which local CSV is the canonical input.
6. Add inline citation keys for `ALPHA = 1.2` (convexity parameter) and `SELECTION_AMP = 1.5` (NHBS 2023 anchor) in `build_figure.py`.
