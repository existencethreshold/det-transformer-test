# Pre-Registration: DET I-D Balance Applied to Transformer Layer Activations

**Author:** Nathan M. Thornhill
**Affiliation:** Institute for Complexity Science and Advanced Computing (ICSAC)
**Drafted:** 2026-05-07
**Status:** LOCKED via Zenodo deposit
**Zenodo DOI:** [10.5281/zenodo.20077301](https://doi.org/10.5281/zenodo.20077301)
**Initial commit:** `b11fe85ac04a0bfb870668c6633c25700cc63457` (2026-05-07)
**Repo:** `existencethreshold/det-transformer-test`

---

## Purpose

It is tested whether the Dynamic Existence Threshold (DET) integration-differentiation balance metric, computed under the parameters disclosed in US Provisional Patent 64/029,658, classifies behavioral regime in transformer language models when applied to per-layer K/V effective rank.

A positive result supports the addition of a transformer-architecture embodiment to the non-provisional conversion of 64/029,658 (deadline 2027-04-04). A null result is reported as a bounded-scope finding; no claim is added.

## Hypothesis (locked before run)

**H1 (primary):** Cell-level DET balance metric `B`, computed on per-layer K/V effective rank binned into N=5 bands using patent-default parameters, classifies cells into compliance regime (instruct + instruct_no_repeat) vs derivation regime (verify) with AUC ≥ 0.70 (95% CI lower bound > 0.5).

**H0 (null):** AUC < 0.70 or 95% CI includes 0.5. No claim added at conversion.

## Data source

Existing jsonl results in `det-transformer-test/results/`. **No new model runs.**

Eligible files (must satisfy all):
- model ∈ {Qwen2.5-7B-Instruct, Llama-3.1-8B-Instruct, Mistral-7B-Instruct-v0.3}
- anchor_mode = `mixed_tiered`
- frame ∈ {instruct, instruct_no_repeat, verify}
- contains all 5 checkpoints {500, 2000, 8000, 16000, 32000}

Expected cell count: 3 models × 5 checkpoints × 3 frames = **45 cells**
- Compliance class (instruct + instruct_no_repeat): 30
- Derivation class (verify): 15

If actual eligible files yield fewer cells, the pre-registered minimum is N≥36 (3 models × 5 checkpoints × either 2 or 3 frames complete). Below that, run is aborted, reported as insufficient data, no analysis performed.

## Activity scalar (locked)

**Primary:** `a_i` = mean K/V effective rank in band i, where K/V rank = 0.5·(k_effective_rank_per_layer + v_effective_rank_per_layer).

Source field: `with_anchor.k_effective_rank_per_layer` and `with_anchor.v_effective_rank_per_layer` from per-checkpoint records.

`without_anchor` data NOT used in primary endpoint (this is a regime test on the loaded condition, not a delta test).

**Secondary (robustness only, reported but not used for decision):** `a_i` = mean attention entropy per band, from `with_anchor.attention_entropy_per_layer`.

## Layer-to-band mapping (locked)

For a model with L transformer layers, layers [0..L-1] are partitioned into N=5 contiguous bands using `numpy.array_split(range(L), 5)`. Band i activity is the arithmetic mean of per-layer K/V rank over layers in band i.

Verified layer counts from data:
- Qwen-7B: 28 layers → bands of sizes [6, 6, 6, 5, 5]
- Llama-3.1-8B: 32 layers → bands of sizes [7, 7, 6, 6, 6]
- Mistral-7B-v0.3: 32 layers → bands of sizes [7, 7, 6, 6, 6]

This binning rule is locked. No alternative mappings (per-band layer count, fixed-size bins, etc.) will be tried post-hoc.

## DET pipeline parameters (locked, patent defaults)

| parameter | value | source |
|-----------|-------|--------|
| N | 5 | patent claim 3 |
| theta (activation threshold) | 2.0 | patent claim 4 |
| w_J (evenness weight) | 1.0 | patent claim 2 (allowed setting) |
| w_P (pattern diversity weight) | 0.0 | patent claim 2 (allowed setting) |

**Note on w_J=1.0, w_P=0.0:** Patent claim 2 specifies w_J and w_P as "non-negative weights summing to 1," which permits this setting. The pattern-diversity term P is computed over W sub-windows of a time series; with one activity vector per cell (single forward-pass snapshot, no time axis), P is undefined. Setting w_P=0 elides the term while remaining within the patent's parameter space. This is a deliberate, pre-registered choice and not a post-hoc adaptation — it constrains the test to evaluate the evenness-driven half of the synergy metric only.

**Pipeline (executed exactly as in patent claim 1, with elided P term):**
1. `p_i = a_i / sum(a_j)`
2. `H = -sum(p_i · ln(p_i))`
3. `N_eff = exp(H)`
4. `R = (N_eff - 1) / (N - 1)` if `N_eff ≥ theta` else `R = 0`
5. `C = N_eff / N`; `J = H / ln(N)` (Pielou evenness)
6. `S = C · J` if `N_eff ≥ theta` else `S = 0` (equivalent to `S = C · (w_J · J + w_P · P)` with w_J=1, w_P=0)
7. `I = R · S`
8. `D = sqrt(JSD(p, uniform_N))` where uniform_N = [1/N]·N
9. **B per cell**: For the cross-cell test, `z(I)` and `z(D)` are computed using mean and std over the 45-cell pool (within-pool z-score). `B = |z(I) - z(D)|`.

**No parameter tuning.** If any parameter is changed for any reason after run start, the pre-registration is voided and the result is reported as exploratory only.

## Endpoints

### Primary endpoint
**AUC of `B` for binary classification of cells into {compliance: instruct, instruct_no_repeat} vs {derivation: verify}**, pooled across all 3 models and 5 checkpoints.

- Computed via `sklearn.metrics.roc_auc_score`
- 95% CI via 10,000-iteration bootstrap on cell labels (pairs resampled with replacement)
- Direction: B *higher* in derivation class is the pre-registered direction. If B is higher in compliance class instead, AUC is reported as min(AUC, 1−AUC) and the result is treated as "wrong-direction signal" — reported but does not satisfy H1.

### Secondary endpoints (reported, not decision-relevant)
1. AUC of `B` per-model (3 separate AUCs with CIs)
2. AUC of `B` per-checkpoint (5 separate AUCs with CIs)
3. Spearman correlation of cell `B` with cell-level override count (sum of `behavioral_deltas[i].delta_violation > 0` over the 8 probes)
4. Robustness: AUC of `B` recomputed with attention entropy as activity scalar instead of K/V rank

### Baseline comparisons (decision-relevant context)
Pre-registered baselines, computed identically:
1. **AUC of mean K/V rank alone** (averaged across all 28-32 layers, no DET pipeline)
2. **AUC of mean attention-to-anchor alone**
3. **Permutation null:** AUC distribution under 10,000 random shuffles of the regime label

`B` must beat both feature baselines (point estimate) AND the permutation 95th percentile to claim DET adds information beyond raw geometric features.

## Decision rule (locked)

| AUC of `B` (point) | 95% CI lower | Beats both feature baselines? | Decision |
|-------------------|--------------|------------------------------|----------|
| ≥ 0.70 | > 0.50 | yes | **POSITIVE.** Add transformer embodiment to 64/029,658 conversion. |
| ≥ 0.70 | > 0.50 | no | **WEAK POSITIVE.** B tracks regime but doesn't add info beyond raw features. Report; do not add patent claim. |
| 0.50–0.70 | any | any | **NULL.** DET-on-transformer-layers does not generalize at patent-default parameters. Report cleanly. |
| < 0.50 (wrong direction) | any | any | **NEGATIVE.** Report; do not add claim. |

## Reporting commitment

Regardless of outcome:
- Final report written to `det-transformer-test/writeup/det-on-layers-results.md`
- Includes: all 4 secondary endpoints, all 3 baselines, full bootstrap distributions, the cell × B table, and the decision per the rule above
- Committed to git within 7 days of run completion
- A null or negative result is reported with the same prominence as a positive one. No file deletion, no parameter retry.

## Researcher degrees of freedom — acknowledged and locked

The following choices could have been made differently and are locked here to prevent post-hoc selection:
1. **Activity scalar = K/V rank (mean of K and V)** rather than K-only, V-only, residual norm, or any other layer feature.
2. **N=5 bands** rather than N=3, 4, 6, 7, 8, or per-layer (N=L).
3. **Equal-split binning** rather than fixed-size bins, log-scale bins, or learned binning.
4. **w_J=1.0, w_P=0.0** (P term elided due to absence of time axis) rather than w_J=0.5/w_P=0.5 with an improvised non-time-series P.
5. **with_anchor data only** rather than delta vs without_anchor or absolute without_anchor.
6. **Compliance class = {instruct, instruct_no_repeat}** rather than instruct only.
7. **Within-pool z-scoring** rather than per-model or per-checkpoint baselines.
8. **AUC threshold = 0.70** rather than 0.65, 0.75, or 0.80.

If the run yields a null at primary endpoint, retrying with any alternative on this list is exploratory and must be reported as such.

## Implementation footprint

- One script: `analyze_det_on_layers.py` in repo root
- Reads `results/*.jsonl`, writes `writeup/det-on-layers-results.md` and `results/det-on-layers-cells.csv`
- ~250 lines, numpy + sklearn + scipy only
- Runtime: <1 minute, single CPU
- No model inference, no GPU

## Sign-off

Locking ceremony, executed in this exact order:

1. Append commit timestamp above
2. `git add` + `git commit` this file (records local timestamp + content hash)
3. **Deposit to Zenodo (general, not ICSAC community) before any analysis is run.** The Zenodo DOI is the canonical lock; git commit is the redundant evidence layer.
4. Append the minted Zenodo DOI to the header above; final git commit
5. The analysis script `analyze_det_on_layers.py` is written only after the Zenodo deposit is live. Its first line echoes BOTH the git commit hash AND the Zenodo DOI of this pre-registration as runtime sanity checks
6. The final results report cites the Zenodo DOI as evidence that pre-registration preceded analysis

---

**Reviewer notes / objections (fill in before locking):**

- [ ]
- [ ]
- [ ]
