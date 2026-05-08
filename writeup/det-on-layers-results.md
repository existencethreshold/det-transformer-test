# DET-on-Transformer-Layers — Results

**Pre-registration:** [10.5281/zenodo.20077301](https://doi.org/10.5281/zenodo.20077301)
**Analysis script:** `analyze_det_on_layers.py` (this repo)
**Pipeline parameters (locked):** N=5, theta=2.0, w_J=1.0, w_P=0.0

## Cell pool

- Total cells: **45**
- Compliance (instruct + instruct_no_repeat): 30
- Derivation (verify): 15

## Primary endpoint

**AUC of B (K/V rank activity scalar) for compliance vs derivation:** 0.5178
**95% CI (bootstrap, 10,000 iters):** [0.3333, 0.6978]
**Wrong-direction flag:** False

## Baselines

- Mean K/V rank alone: AUC = 0.5111
- Mean attention-to-anchor alone: AUC = 0.5311
- Permutation null 95th percentile: AUC = 0.6778
- **B beats all baselines:** False

## Secondary endpoints

### Per-model AUC

| Model | AUC | 95% CI | n |
|-------|-----|--------|---|
| Qwen/Qwen2.5-7B-Instruct | 0.5000 | [0.1606, 0.8394] | 15 |
| meta-llama/Llama-3.1-8B-Instruct | 0.5600 | [0.2037, 0.8889] | 15 |
| mistralai/Mistral-7B-Instruct-v0.3 | 0.5600 | [0.2000, 0.9000] | 15 |

### Per-checkpoint AUC

| Checkpoint | AUC | 95% CI | n |
|-----------:|-----|--------|---|
|        500 | 0.5000 | [0.0500, 1.0000] | 9 |
|       2000 | 0.5000 | [0.0000, 0.9500] | 9 |
|       8000 | 0.5556 | [0.1250, 1.0000] | 9 |
|      16000 | 0.6111 | [0.1667, 1.0000] | 9 |
|      32000 | 0.6111 | [0.1429, 1.0000] | 9 |

### Spearman: B vs override count

- rho = -0.2293, p = 0.1297

### Robustness: attention entropy as activity scalar

- AUC = 0.4911, 95% CI [0.2943, 0.6996]

## Decision

**NULL: AUC below 0.70 or 95% CI includes 0.5. DET-on-transformer-layers does not generalize at patent-default parameters. Report cleanly; no patent claim added.**

## Patent context

The pre-registered analysis was designed to answer a single, narrow question: does the existing DET integration-differentiation balance metric — as disclosed in **US Provisional Patent 64/029,658** (filed 2026-04-04, non-provisional conversion deadline 2027-04-04) — generalize to transformer language-model layer activations at patent-default parameters (N=5, theta=2.0, w_J=1.0, w_P=0.0)?

A positive outcome would have supported adding a transformer-architecture embodiment to the non-provisional conversion of 64/029,658, claiming the same I-D balance machinery that classifies financial-market, space-weather, and EEG states (existing claimed AUCs 0.868, 0.932, 0.909 respectively) also classifies prompt-frame compliance vs derivation regime in transformer LMs.

The null result means **no transformer-architecture embodiment is added** to the existing patent at conversion. The patent's already-claimed application domains (financial, geophysical, neurological, telecommunications, power grid, biological, social network, transportation, industrial process control, distributed computing — per claim 8) remain undisturbed; the AUCs reported in the existing patent application stand on their original validation domains. No claim is added; no claim is weakened.

The negative scope finding here is itself useful prior art for the conversion: it documents that the inventor tested generalization to a high-value adjacent domain (transformer interpretability), found patent-default parameters did not extend to that substrate at the cell-level snapshot granularity, and chose not to broaden the claim language. This evidences good-faith bounded scoping rather than overreach during conversion.

## Scope of this conclusion

The null applies specifically to: cell-level, single-snapshot K/V effective rank as activity scalar, N=5 contiguous bands, w_J=1.0/w_P=0.0, on the 3 target models × 5 checkpoints × 3 frames = 45 cells. Whether DET-shaped signals exist in transformer activations under different feature choices, finer or coarser binning, time-axis-aware aggregation, or larger model panels is **not addressed** by the pre-registered analysis — those are open questions for exploratory follow-up, the results of which are scientifically valid as hypothesis-generating but cannot be claimed as confirmatory of any patent extension without a new pre-registration on independent data.

## Cell-level data

See `results/det-on-layers-cells.csv` (45 rows).
