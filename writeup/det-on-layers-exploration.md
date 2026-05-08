# Exploration: where does the regime signal live?

**Status: EXPLORATORY. Hypothesis-generating. NOT pre-registered.**

These results do not satisfy any pre-registered hypothesis. The pre-registered analysis (`analyze_det_on_layers.py`, locked at Zenodo DOI 10.5281/zenodo.20077301) returned a clean null and that result stands. The exploration below answers a different question: given the same data, is there ANY simple feature/aggregation choice that distinguishes compliance from derivation regime, and if so, what's the upper bound? Anything compelling found here would need to be re-tested on independent data under a fresh pre-registration before it could be claimed as a real finding.

**Cell pool:** 45 cells, 30 compliance, 15 derivation.
**Bootstrap iters:** 5,000 per cell.

## DET pipeline — sweep over activity scalars × N bands

Same DET pipeline as the pre-reg (w_J=1, w_P=0, theta=2.0, K/V binning per `numpy.array_split`). Only the activity scalar and N vary. AUCs are folded to >= 0.5 (direction-agnostic) since this is exploration, not hypothesis testing.

| Activity scalar | N bands | AUC | 95% CI | Wrong dir |
|-----------------|--------:|----:|-------:|----------:|
| K_only | 3 | 0.5244 | [0.5029, 0.7222] | False |
| K_only | 4 | 0.5178 | [0.5024, 0.7243] | False |
| K_only | 5 | 0.5089 | [0.5029, 0.7101] | False |
| K_only | 6 | 0.5289 | [0.5040, 0.7135] | False |
| K_only | 7 | 0.5200 | [0.5023, 0.7095] | False |
| K_only | 8 | 0.5267 | [0.5022, 0.7212] | False |
| V_only | 3 | 0.5378 | [0.5024, 0.7188] | True |
| V_only | 4 | 0.5156 | [0.5025, 0.7099] | True |
| V_only | 5 | 0.5244 | [0.5025, 0.7140] | True |
| V_only | 6 | 0.5156 | [0.5023, 0.7134] | True |
| V_only | 7 | 0.5111 | [0.5024, 0.7096] | True |
| V_only | 8 | 0.5200 | [0.5024, 0.7197] | True |
| K_plus_V_mean | 3 | 0.5178 | [0.5025, 0.7188] | False |
| K_plus_V_mean | 4 | 0.5089 | [0.5023, 0.7122] | False |
| K_plus_V_mean | 5 | 0.5178 | [0.5025, 0.7128] | False |
| K_plus_V_mean | 6 | 0.5133 | [0.5022, 0.7046] | False |
| K_plus_V_mean | 7 | 0.5111 | [0.5025, 0.7059] | False |
| K_plus_V_mean | 8 | 0.5133 | [0.5031, 0.7078] | False |
| K_minus_V | 3 | 0.5022 | [0.5025, 0.7111] | False |
| K_minus_V | 4 | 0.5044 | [0.5025, 0.7143] | True |
| K_minus_V | 5 | 0.5289 | [0.5025, 0.7129] | True |
| K_minus_V | 6 | 0.5044 | [0.5023, 0.7085] | True |
| K_minus_V | 7 | 0.5378 | [0.5025, 0.7200] | True |
| K_minus_V | 8 | 0.5356 | [0.5027, 0.7197] | True |
| attention_entropy | 3 | 0.5422 | [0.5039, 0.7181] | False |
| attention_entropy | 4 | 0.5467 | [0.5040, 0.7419] | False |
| attention_entropy | 5 | 0.5089 | [0.5040, 0.7406] | True |
| attention_entropy | 6 | 0.5267 | [0.5027, 0.7332] | False |
| attention_entropy | 7 | 0.5022 | [0.5025, 0.7016] | True |
| attention_entropy | 8 | 0.5244 | [0.5025, 0.7105] | True |
| attn_to_anchor | 3 | 0.5556 | [0.5040, 0.7368] | True |
| attn_to_anchor | 4 | 0.5778 | [0.5044, 0.7611] | True |
| attn_to_anchor | 5 | 0.6156 | [0.5061, 0.8022] | True |
| attn_to_anchor | 6 | 0.5467 | [0.5039, 0.7346] | True |
| attn_to_anchor | 7 | 0.5511 | [0.5027, 0.7356] | True |
| attn_to_anchor | 8 | 0.5644 | [0.5043, 0.7500] | True |

**Best DET cell from sweep:** attn_to_anchor, N=5, AUC=0.6156, 95% CI [0.5061, 0.8022].

## Upper bound — logistic regression on the 5-band features

If the data simply does not contain cell-level regime signal at coarse-band resolution, no DET parameterization will find it. This run uses logistic regression on the 5-band means of K rank, V rank, attention entropy, and attention-to-anchor (20 features total) as an upper-bound check.

| CV scheme | AUC |
|-----------|----:|
| LOOCV-by-model | 0.5289
| LOOCV-by-checkpoint | 0.5800
| StratifiedKFold-5 | 0.5711

## Reading

If best DET AUC and LR upper-bound are both around 0.5, the cell-level regime classification problem at this resolution is genuinely hard with this data — no feature engineering will rescue it within the current 45-cell, single-snapshot, coarse-band scope. The honest next moves would be: (a) more cells (more models, more checkpoints), (b) finer time-axis aggregation (per-token rather than per-checkpoint), or (c) reformulating regime as a probe-level rather than cell-level label.

If the LR upper bound clearly exceeds the best DET cell, signal exists but is not in the shape DET expects. That would point at which features actually carry the regime information and motivate a different (non-DET) framework.

Either reading is informative. Neither is confirmatory of anything until replicated on new data.
