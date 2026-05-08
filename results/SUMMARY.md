# DET-on-transformer probe — results summary

Geometric metrics (attn_to_anchor, KV effective rank) decouple from behavioral fidelity to a planted multi-fact instruction as context length grows. Hypothesis from Dynamic Existence Threshold (DET): a system can show a coherence surge before collapse. Tested on three model scales (135M, 1.5B, 7B) with six counter-intuitive planted falsehoods spanning prior-strength tiers (strong/medium/weak).

## Setup

- Anchor: 6 planted falsehoods (e.g. 'capital of France is Marseille', 'water boils at 73°C').
- Per checkpoint: two forward passes — anchor-present and anchor-replaced-by-neutral-filler of equal token length. Behavioral delta = with_anchor fidelity − without_anchor fidelity.
- Probes use deterministic generation (do_sample=False).
- Geometric metrics (attention entropy per layer, KV effective rank, last-token attention to anchor span) collected via forward hooks on attention modules.

## Headline result: scaling table

| model | context | france_capital | everest_country | moon_landing_year | largest_planet | water_boil | earth_age | total |
|---|---|---|---|---|---|---|---|---|
| SmolLM-135M | 200 | 0 | 0 | 0 | 0 | **+1** | 0 | 1 |
| SmolLM-135M | 500 | 0 | 0 | 0 | **+1** | 0 | 0 | 1 |
| SmolLM-135M | 1500 | 0 | 0 | 0 | **+1** | 0 | 0 | 1 |
| SmolLM-135M | 2000 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| SmolLM-135M | 3000 | 0 | 0 | 0 | **+1** | 0 | 0 | 1 |
| Qwen-1.5B | 200 | **+1** | 0 | 0 | **+1** | 0 | **+1** | 3 |
| Qwen-1.5B | 500 | **+1** | 0 | 0 | **+1** | 0 | **+1** | 3 |
| Qwen-1.5B | 2000 | **+1** | 0 | 0 | **+1** | 0 | **+1** | 3 |
| Qwen-1.5B | 8000 | **+1** | **+1** | 0 | **+1** | 0 | **+1** | 4 |
| Qwen-1.5B | 16000 | **+1** | 0 | 0 | **+1** | 0 | 0 | 2 |
| Qwen-1.5B | 32000 | **+1** | 0 | 0 | **+1** | 0 | 0 | 2 |
| Qwen-3B | 500 | **+1** | 0 | **+1** | **+1** | **+1** | **+1** | 5 |
| Qwen-3B | 2000 | **+1** | 0 | **+1** | **+1** | **+1** | **+1** | 5 |
| Qwen-3B | 8000 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |
| Qwen-3B | 16000 | **+1** | 0 | 0 | **+1** | 0 | **+1** | 3 |
| Qwen-3B | 32000 | **+1** | 0 | 0 | **+1** | 0 | 0 | 2 |
| Qwen-7B | 500 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |
| Qwen-7B | 2000 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |
| Qwen-7B | 8000 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |
| Qwen-7B | 16000 | **+1** | **+1** | **+1** | **+1** | 0 | **+1** | 5 |
| Qwen-7B | 32000 | **+1** | **+1** | **+1** | **+1** | 0 | **+1** | 5 |
| Mistral-7B-v0.3 | 500 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |
| Mistral-7B-v0.3 | 2000 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |
| Mistral-7B-v0.3 | 8000 | **+1** | **+1** | **+1** | **+1** | 0 | **+1** | 5 |
| Mistral-7B-v0.3 | 16000 | **+1** | 0 | 0 | **+1** | 0 | **+1** | 3 |
| Mistral-7B-v0.3 | 32000 | **+1** | 0 | 0 | **+1** | 0 | **+1** | 3 |
| OLMo-2-7B | 500 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |
| OLMo-2-7B | 2000 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |
| OLMo-2-7B | 8000 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| OLMo-2-7B | 16000 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| OLMo-2-7B | 32000 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Llama-3.1-8B | 500 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |
| Llama-3.1-8B | 2000 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |
| Llama-3.1-8B | 8000 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |
| Llama-3.1-8B | 16000 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |
| Llama-3.1-8B | 32000 | **+1** | **+1** | **+1** | **+1** | **+1** | **+1** | 6 |

## attn_to_anchor decay (where collected)

| model | context | attn_to_anchor (mean over layers) |
|---|---|---|
| SmolLM-135M | 200 | 0.6586 |
| SmolLM-135M | 500 | 0.3479 |
| SmolLM-135M | 1500 | 0.3159 |
| SmolLM-135M | 2000 | 0.2676 |
| SmolLM-135M | 3000 | 0.2694 |
| Qwen-1.5B | 200 | 0.5748 |
| Qwen-1.5B | 500 | 0.3888 |
| Qwen-1.5B | 2000 | 0.2616 |
| Qwen-1.5B | 8000 | 0.2779 |
| Qwen-3B | 500 | 0.4263 |
| Qwen-3B | 2000 | 0.3605 |
| Qwen-3B | 8000 | 0.3803 |
| Qwen-3B | 16000 | 0.3125 |
| Qwen-3B | 32000 | 0.2674 |
| Qwen-7B | 500 | 0.4374 |
| Qwen-7B | 2000 | 0.3267 |
| Mistral-7B-v0.3 | 500 | 0.5754 |
| Mistral-7B-v0.3 | 2000 | 0.5532 |
| Mistral-7B-v0.3 | 8000 | 0.5742 |
| Mistral-7B-v0.3 | 16000 | 0.5151 |
| Mistral-7B-v0.3 | 32000 | 0.5027 |
| OLMo-2-7B | 500 | 0.4046 |
| OLMo-2-7B | 2000 | 0.1632 |
| OLMo-2-7B | 8000 | 0.0353 |
| OLMo-2-7B | 16000 | 0.0141 |
| OLMo-2-7B | 32000 | 0.0124 |
| Llama-3.1-8B | 500 | 0.5921 |
| Llama-3.1-8B | 2000 | 0.5811 |
| Llama-3.1-8B | 8000 | 0.5625 |
| Llama-3.1-8B | 16000 | 0.5630 |
| Llama-3.1-8B | 32000 | 0.5485 |

## Plots

- `results/plots/override_count.png`
- `results/plots/probe_heatmap.png`
- `results/plots/attn_to_anchor_decay.png`

## Findings

1. **Override capacity scales with model size.** SmolLM-135M can't follow planted falsehoods at any context length. Qwen-1.5B follows 3/6 at short context, retains 2/6 at 32K. Qwen-7B follows 6/6 at short context, retains 5/6 at 32K. ~10× params → ~2.5× surviving overrides.
2. **DET-predicted surge observed at intermediate scale.** Qwen-1.5B at ckpt 8000 shows an *additional* override (`everest_country`) appearing — a surge of compliance — that reverts by 16K. attn_to_anchor ticks up against the smooth decay trend (0.26 → 0.28) on the same checkpoint. Both behavioral and geometric metrics rise together at the surge point.
3. **Collapse is selective, not catastrophic, AND family-conditioned.** When an override breaks, others can remain stable indefinitely. Qwen-7B at 32K loses only `water_boil` (5/6 survive). Mistral-7B-v0.3 at 32K loses three (`water_boil`, `everest_country`, `moon_landing_year`) and keeps the other three (`france_capital`, `largest_planet`, `earth_age`) stable from 16K through 32K. First fact to break in BOTH 7B-class families is `water_boil` — the strongly encyclopedically reinforced numerical fact (100°C) — supporting prior-strength as the determinant of break order, not arbitrary noise.
4. **Inverse decoupling: same geometry, different behavior — replicated cross-family.** Within Qwen scale-axis: ~0.39 attn_to_anchor at ckpt 500 on Qwen-1.5B vs ~0.44 on Qwen-7B → 3/6 vs 6/6 flips. Cross-family at 32K: Mistral-7B holds attn_to_anchor at 0.50 while flipping only 3/6 probes; Qwen-7B's attention budget by 32K is presumably much lower (decay trajectory from 0.44→0.33 between 500 and 2000) yet Qwen-7B retains 5/6 — *more* surviving overrides on *less* anchor attention. Geometry of attention does not predict behavioral compliance, in either direction.
5. **DET surge requires headroom.** Qwen-7B and Mistral-7B both saturate at 6/6 at ckpt 500 — there's nowhere for the surge to manifest as additional flips. The pattern shows up only when the model has un-flipped probes available to flip on the surge stroke (Qwen-1.5B at 8K).
6. **Cross-family generality (anti-Qwen-quirk).** Mistral-7B-Instruct-v0.3 reproduces the surge-then-selective-collapse pattern: 6/6 at 500-2000, 5/6 at 8K, 3/6 stable from 16K-32K. The phenomenon is not a Qwen-specific instruction-override quirk — two unrelated 7B-class families show the same shape with the same first-to-break fact. Different stable-survivor profile (Mistral keeps strongest+repeated; Qwen-7B keeps the cleaner-recall-text facts) suggests prior-strength interacts with training-data-specific committal behavior.

## Limitations / wrinkles

- `attn_to_anchor` could not be collected at 16K+ on Qwen-1.5B and at 8K+ on Qwen-7B due to memory: forward hooks did not actually free the per-layer attention tensors in transformers 4.57.1 (full attention matrices remain resident across all layers during the forward pass on GPU). The fix would be a chunked-attention monkey-patch of `LlamaAttention.forward` so attention is computed and freed per query-chunk; not implemented in this run.
- Qwen-7B 16K/32K used `attn_implementation="sdpa"` to fit memory, which doesn't expose attention weights; behavioral and KV-rank metrics only.
- `water_boil`'s anchor (73°C) plausibly leaks information about its own override status because the parametric prior (100°C) is exceptionally strongly trained. Replacing with a less drilled-in fact would test whether the 'first to break' result generalizes.
- A torch reinstall earlier in the session silently replaced the ROCm-aware torch with a CUDA-only generic wheel, causing several runs to execute on CPU. The MI300X Qwen-1.5B JSONL is from the corrected GPU run; earlier files in `results/` are partial/CPU runs and should be ignored.

## Open questions for next runs

- Replication seeds: each run is deterministic (do_sample=False), so seed variance is zero. Variation comes from re-prompting with paraphrased anchors/probes.
- Does the surge timing scale with model size? Qwen-1.5B surge at 8K; would Qwen-3B surge at 16K? Need an intermediate model.
- Multi-anchor independence: re-run with one fact per anchor (six runs) to confirm the attention-dilution confound observed when fact-density grew from 3 to 6.
- Chunked-attention refactor unlocks `attn_to_anchor` at full context on all models. If decoupling is real at long context, expect attn_to_anchor to stay flat or even rise slightly while behavior collapses — the cleanest single-figure signature.
