# Zenodo Deposit Draft — Pre-Registration Metadata

**Status:** Ready for Nathan to submit manually via Zenodo web UI
**Account:** Nathan's personal Zenodo (NOT ICSAC community — pre-regs aren't community-curated)
**Save as:** Draft (do NOT publish until pre-reg is git-locked and ready)

---

## Files to upload

1. **Primary:** `/home/dietpi/det-transformer-test/writeup/PRE-REGISTRATION-det-on-layers.pdf`
2. (Optional, for source-fidelity) `/home/dietpi/det-transformer-test/writeup/PRE-REGISTRATION-det-on-layers.md` — the markdown source

Drop both into the upload area on Zenodo. The PDF is the canonical, the .md is for anyone who wants to diff against the source.

---

## Web form fields — copy-paste ready

Go to: **https://zenodo.org/uploads/new**

### Communities
**Leave blank.** Do not add to ICSAC community — pre-regs aren't curated there.

### Resource type
- **Type:** Publication
- **Subtype:** Working paper

### Title
```
Pre-Registration: DET I-D Balance Applied to Transformer Layer Activations
```

### Publication date
```
2026-05-07
```

### Creators
- **Name:** `Thornhill, Nathan M.`
- **Affiliation:** `Institute for Complexity Science and Advanced Computing (ICSAC)`
- **ORCID:** _fill in your ORCID — it's gated on the ICSAC submission intake so you have it handy_

### Description (abstract field — supports HTML)
```
It is predicted that the Dynamic Existence Threshold (DET) integration-differentiation balance metric, computed under the parameters disclosed in US Provisional Patent 64/029,658, will classify behavioral regime in transformer language models when applied to per-layer K/V effective rank.

Existing paired-frame override-sweep data — collected on Qwen2.5-7B-Instruct, Llama-3.1-8B-Instruct, and Mistral-7B-Instruct-v0.3 across five context lengths (500 to 32,000 tokens) and three preamble framings (instruct, instruct_no_repeat, verify) — are re-analyzed without further model inference. Per-layer K/V effective rank is binned into N=5 contiguous bands and passed through the patent-default DET pipeline to produce one cell-level balance metric B per (model × checkpoint × frame) condition. The primary endpoint is the AUC of B for binary classification of cells into compliance regime (instruct + instruct_no_repeat) versus derivation regime (verify), pooled across models and checkpoints, with a pre-registered success threshold of AUC ≥ 0.70 and 95% CI lower bound > 0.5.

All parameters, layer-band mappings, baseline comparisons, decision rules, and researcher degrees of freedom are specified prior to analysis. A positive outcome supports the addition of a transformer-architecture embodiment to the non-provisional conversion of US Provisional Patent 64/029,658 (deadline 2027-04-04). A null or negative outcome is reported with equal prominence and yields no additional patent claim.

The deposit is timestamped prior to the writing or execution of any analysis script. The minted Zenodo DOI serves as canonical evidence of pre-commitment.
```

### Keywords (comma-separated, add one at a time on Zenodo)
```
dynamic existence threshold
DET
transformer interpretability
pre-registration
integration-differentiation balance
K/V effective rank
prompt-frame compliance
patent embodiment
mechanistic interpretability
complex systems
```

### Additional notes
```
This pre-registration corresponds to a planned analysis re-using existing experimental data from the det-transformer-test repository (https://github.com/... — fill in if/when public). No new model inference is performed; the test re-analyzes already-collected per-layer geometric features under the DET pipeline.

The deposit timestamp serves as evidence that all locked parameters, endpoints, baselines, and decision rules were specified before any analysis was executed.
```

### License
```
Creative Commons Attribution 4.0 International (CC-BY-4.0)
```

### Related/alternate identifiers
Add each as a separate entry. Relation given in parentheses.

| Identifier | Relation | Resource type |
|------------|----------|---------------|
| `10.5281/zenodo.18166974` | is supplement to | Publication / Preprint |
| `10.5281/zenodo.18262424` | is supplement to | Publication / Preprint |
| `10.5281/zenodo.18319430` | is supplement to | Publication / Preprint |
| US Provisional 64/029,658 | is documentation of | Publication / Patent |

(The three Zenodo DOIs are the prior DET-line preprints cross-referenced in the patent. The patent number can be entered in the Notes field if Zenodo's identifier dropdown doesn't accept the format directly.)

### Funding / grants
**Leave blank.** No external funding.

### Subjects
Optional. If adding, use:
- `Mechanistic interpretability of language models`
- `Complex systems theory`

---

## Submission flow (recommended order)

1. Read through `PRE-REGISTRATION-det-on-layers.md` one more time. Make any final edits in markdown source.
2. If edits made, recompile PDF: `pandoc PRE-REGISTRATION-det-on-layers.md -o PRE-REGISTRATION-det-on-layers.pdf --pdf-engine=weasyprint -V geometry:margin=1in`
3. **git commit the .md file** — local timestamp + content hash. Push to remote if you want offsite redundancy.
4. Open https://zenodo.org/uploads/new
5. Fill fields per this document. Upload PDF (and .md if you want).
6. **Click "Save" — NOT "Publish".** This stages a draft you can revisit.
7. Review on the Zenodo draft page. Make sure community = none, license = CC-BY-4.0, all fields populated.
8. When satisfied, click **Publish**. DOI is minted at that moment.
9. Copy the DOI back into `PRE-REGISTRATION-det-on-layers.md` header (replace the placeholder line).
10. Final git commit recording the DOI.
11. Only now write `analyze_det_on_layers.py` and run it.

---

## What gets locked vs what remains editable

**Locked at Zenodo publish (step 8):**
- All hypotheses, parameters, endpoints, baselines, decision rules, researcher degrees of freedom

**Still editable after publish (via Zenodo "New version"):**
- The DOI in the header (added step 9 — published as v2)
- Typo fixes / clarifications

Each "New version" mints a new DOI but the original deposit DOI is what you cite as the pre-commitment evidence — always reference the v1 DOI in the results report, not the latest.

---

## After-deposit checklist

- [ ] Zenodo DOI added to `PRE-REGISTRATION-det-on-layers.md` header
- [ ] Final git commit on the .md file
- [ ] Pre-registration DOI noted in any future paper drafting from this work
- [ ] Pre-registration DOI noted in `64/029,658` non-provisional conversion paperwork (if test passes)

---

**Drafted:** 2026-05-07 by orchestrator on Nathan's behalf
**For your eyes before submission. Edit anywhere before pasting into Zenodo.**
