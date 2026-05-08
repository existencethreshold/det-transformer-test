# det-transformer-test

Transformer-language-model probe testing prompt-frame-gated compliance versus derivation regimes via paired-frame override sweeps, K/V effective-rank measurement, and tier-stratified planted-falsehood lie sets across context lengths from 500 to 32,000 tokens.

## Pre-registration

A planned analysis re-applying the Dynamic Existence Threshold (DET) integration-differentiation balance metric, as disclosed in US Provisional Patent 64/029,658, to the per-layer K/V effective-rank data already collected in this repository, is pre-registered at:

**Zenodo DOI:** [10.5281/zenodo.20077301](https://doi.org/10.5281/zenodo.20077301)

All parameters, layer-band mappings, baseline comparisons, decision rules, and researcher degrees of freedom for the planned DET-on-layers analysis are locked in `writeup/PRE-REGISTRATION-det-on-layers.md` and timestamped at the Zenodo DOI above. The analysis script `analyze_det_on_layers.py` is written and executed only after the deposit is live.

## Cited prior work

- Thornhill, N. M. (2026a). *The Existence Threshold: A Framework for Pattern Persistence in Binary Discrete Systems.* DOI: [10.5281/zenodo.18166974](https://doi.org/10.5281/zenodo.18166974)
- Thornhill, N. M. (2026b). *Pattern Loss at Dimensional Boundaries: The 86% Scaling Law.* DOI: [10.5281/zenodo.18262424](https://doi.org/10.5281/zenodo.18262424)
- Thornhill, N. M. (2026c). *The Dimensional Loss Theorem: Proof and Neural Network Validation.* DOI: [10.5281/zenodo.18319430](https://doi.org/10.5281/zenodo.18319430)
- US Provisional Patent 64/029,658 — *Dynamic Existence Threshold: Methods and Systems for Domain-General Monitoring, Prediction, and Classification of Complex System States Using Integration-Differentiation Balance Metrics.*

## Layout

| Path | Purpose |
|------|---------|
| `experiment.py` | Main probe runner — collects per-layer K/V rank, attention entropy, attention-to-anchor, and behavioral-probe outcomes per (model × checkpoint × frame) condition |
| `chunked_attention.py` | Memory-efficient chunked-eager attention implementation for long-context forward passes |
| `det_patterns.py` | Tiered-lie probe construction (T1 trivial → T2 arithmetic → T3 internal contradiction → T4 chained inference) |
| `analyze.py`, `analyze_tiered.py` | Per-run regime and override analysis |
| `validate_chunked.py` | Chunked-attention numerical-equivalence validation |
| `results/` | Per-run jsonl dumps — one record for the run config, one per checkpoint |
| `writeup/` | Pre-registration, methods writeup, panel audits |
| `run*.sh` | Reproducible run invocations |
| `shell.nix` | Reproducible Nix dev shell |

## Models tested

- Qwen/Qwen2.5-{1.5B, 3B, 7B, 14B}-Instruct
- meta-llama/Llama-3.1-8B-Instruct
- mistralai/Mistral-7B-Instruct-v0.3
- google/gemma-2-9b-it
- allenai/OLMo-2-1124-7B-Instruct

## Hardware

NVIDIA H100 PCIe 80GB (rented via RunPod for the production sweeps).

## Affiliation

Institute for Complexity Science and Advanced Computing (ICSAC).

## License

Code: MIT. Documentation and pre-registration: CC-BY-4.0.
