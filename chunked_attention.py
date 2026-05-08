"""Chunked-eager attention for the DET-on-transformer probe.

Drop-in replacement for `eager_attention_forward` (same signature) that
computes attention in query-row chunks so the full [B, H, Q, K] attention
matrix is never materialized. Per-chunk it accumulates the entropy stat we
care about, plus the last-token attention back to a designated anchor span,
then frees the chunk's attn tensor before computing the next.

Memory: O(B * H * chunk * K) per chunk, vs O(B * H * Q * K) for stock eager.
At 32K context with 28 heads (Qwen-7B / Mistral-7B) and chunk=512, that's
roughly 60x lower peak per layer.

Usage:

    from chunked_attention import (
        register_chunked_eager,
        set_probe_state,
        clear_probe_state,
        collect_layer_metrics,
    )
    register_chunked_eager()  # idempotent

    model = AutoModelForCausalLM.from_pretrained(
        ..., attn_implementation="chunked_eager"
    )

    set_probe_state(anchor_span=(0, anchor_len), last_q=seq_len - 1,
                    chunk_size=1024)
    out = model(inputs)
    metrics = collect_layer_metrics(model)
    # metrics = {"attention_entropy_per_layer": [...],
    #            "attn_to_anchor_per_layer": [...]}  # latter only if anchor_span set
    clear_probe_state()

The probe state is process-global (thread-local would also work but the
experiment harness is single-threaded). Always clear it before doing
unrelated forwards (e.g. .generate()) so behavioral probes don't leak
metrics into the wrong layer slot.
"""
from __future__ import annotations

import math
import threading
from typing import Optional

import torch
from torch import nn


_PROBE_STATE = threading.local()


def set_probe_state(*, anchor_span=None, last_q=None, chunk_size=1024,
                    collect=True):
    """Configure metric collection for the next forward pass.

    anchor_span: (start, end) token indices of the anchor in the input.
                 If None, attn_to_anchor is not collected.
    last_q:      query index whose attention pattern we record. Usually
                 seq_len - 1 (the would-be next-token query). If None,
                 attn_to_anchor is not collected.
    chunk_size:  number of query rows per chunk. 1024 is a reasonable default.
    collect:     master switch. If False, attention runs chunked but no
                 metrics are recorded (use during .generate() so we don't
                 pollute layer state with token-by-token attention).
    """
    _PROBE_STATE.anchor_span = anchor_span
    _PROBE_STATE.last_q = last_q
    _PROBE_STATE.chunk_size = chunk_size
    _PROBE_STATE.collect = collect


def clear_probe_state():
    for attr in ("anchor_span", "last_q", "chunk_size", "collect"):
        if hasattr(_PROBE_STATE, attr):
            delattr(_PROBE_STATE, attr)


def _state(attr, default):
    return getattr(_PROBE_STATE, attr, default)


def _repeat_kv(hidden: torch.Tensor, n_rep: int) -> torch.Tensor:
    """GQA expand: [B, H_kv, S, D] -> [B, H_kv * n_rep, S, D]."""
    if n_rep == 1:
        return hidden
    b, h, s, d = hidden.shape
    return hidden[:, :, None, :, :].expand(b, h, n_rep, s, d).reshape(b, h * n_rep, s, d)


def chunked_eager_attention_forward(
    module: nn.Module,
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attention_mask: Optional[torch.Tensor],
    scaling: Optional[float] = None,
    dropout: float = 0.0,
    softcap: Optional[float] = None,
    **kwargs,
):
    """Same return contract as eager_attention_forward: (attn_output, attn_weights).

    Handles the union of Llama/Qwen2/Mistral/OLMo2/Gemma2 eager-attention
    semantics:
      - GQA via num_key_value_groups
      - logit soft-capping (Gemma2): scores = softcap * tanh(scores / softcap)
      - alternating sliding-window attention (Gemma2): module.sliding_window
        is None for global layers, an int (e.g. 4096) for sliding layers
      - per-chunk causal mask construction when transformers' _update_causal_mask
        returns None (it does for non-recognized impls)

    attn_output is shape [B, Q, H, D] (transposed, as the caller expects).
    attn_weights is always None (we never materialize the full matrix).
    Per-layer metrics, when collect=True, are stashed on `module._det_metrics`.
    """
    n_rep = getattr(module, "num_key_value_groups", 1)
    key = _repeat_kv(key, n_rep)
    value = _repeat_kv(value, n_rep)

    bsz, heads, q_len, head_dim = query.shape
    k_len = key.shape[-2]
    chunk_size = int(_state("chunk_size", 1024))
    collect = bool(_state("collect", False))
    anchor_span = _state("anchor_span", None)
    last_q = _state("last_q", None)

    if scaling is None:
        scaling = head_dim ** -0.5

    # Gemma2: each layer is either sliding-window (e.g. window=4096) or global.
    # `module.sliding_window` is set in Gemma2Attention.__init__; other families
    # don't define it, so getattr returns None and the global path is used.
    sliding_window = getattr(module, "sliding_window", None)
    # Soft-cap may also be sourced from the module if the dispatcher didn't
    # forward it as a kwarg. Gemma2 sets `module.attn_logit_softcapping`.
    if softcap is None:
        softcap = getattr(module, "attn_logit_softcapping", None)

    out_dtype = query.dtype
    attn_output = torch.empty(
        (bsz, heads, q_len, head_dim), dtype=out_dtype, device=query.device
    )

    # transformers 4.57's _update_causal_mask may return None for custom
    # attention implementations — it has explicit branches for "eager",
    # "sdpa", "flash_attention_2", etc. When that happens we build the
    # causal mask ourselves per-chunk (saves O(Q*K) memory at long ctx).
    # Standard prefill: q_len == k_len, q_i looks at k_0..k_i. Decode with
    # cache: q_len < k_len, queries align to the tail (offset = k_len - q_len).
    build_causal = attention_mask is None
    causal_offset = k_len - q_len if build_causal else 0
    k_arange = (
        torch.arange(k_len, device=query.device).unsqueeze(0)
        if build_causal else None
    )
    neg_inf = torch.finfo(query.dtype).min

    # Entropy is averaged over (batch, heads, query positions). To do this
    # incrementally we accumulate a sum and a count.
    entropy_sum = 0.0
    entropy_count = 0
    attn_to_anchor = None  # filled in when last_q is in a chunk

    for q_start in range(0, q_len, chunk_size):
        q_end = min(q_start + chunk_size, q_len)
        q_chunk = query[:, :, q_start:q_end, :]

        # scores: [B, H, q_chunk, K]
        scores = torch.matmul(q_chunk, key.transpose(-1, -2)) * scaling
        # Gemma2 logit soft-cap: applied AFTER scaling, BEFORE mask + softmax.
        # See transformers/models/gemma2/modeling_gemma2.py eager_attention_forward.
        if softcap is not None:
            scores = scores / softcap
            scores = torch.tanh(scores)
            scores = scores * softcap
        if build_causal:
            # per-chunk causal mask: [1, 1, q_chunk, K]
            q_idx = torch.arange(q_start, q_end, device=query.device).unsqueeze(1)
            # Causal: query at (q + offset) cannot see keys after itself.
            mask_chunk = (k_arange > (q_idx + causal_offset))  # bool [q_chunk, K]
            # Sliding window (Gemma2 alternating layers): query at (q + offset)
            # cannot see keys further back than (q + offset - window + 1).
            if sliding_window is not None:
                sw_mask = (k_arange < (q_idx + causal_offset - sliding_window + 1))
                mask_chunk = mask_chunk | sw_mask
                del sw_mask
            scores = scores.masked_fill(mask_chunk.unsqueeze(0).unsqueeze(0), neg_inf)
            del mask_chunk, q_idx
        elif attention_mask is not None:
            scores = scores + attention_mask[:, :, q_start:q_end, :k_len]

        # Softmax in fp32 for numerical stability (matches stock eager).
        attn = nn.functional.softmax(scores, dim=-1, dtype=torch.float32)
        del scores

        if collect:
            eps = 1e-12
            # entropy per (b, h, q): -sum_k p log p
            ent = -(attn * (attn + eps).log()).sum(dim=-1)  # [B, H, q_chunk]
            entropy_sum += float(ent.sum().item())
            entropy_count += ent.numel()
            del ent

            if anchor_span is not None and last_q is not None and q_start <= last_q < q_end:
                a_s, a_e = anchor_span
                # attn slice for the last query, summed over anchor span,
                # mean over heads. attn shape: [B, H, q_chunk, K]
                local_idx = last_q - q_start
                w = attn[0, :, local_idx, a_s:a_e]  # [H, anchor_len]
                attn_to_anchor = float(w.sum(dim=-1).mean().item())
                del w

        attn = attn.to(out_dtype)
        if dropout > 0 and module.training:
            attn = nn.functional.dropout(attn, p=dropout, training=True)

        out_chunk = torch.matmul(attn, value)  # [B, H, q_chunk, D]
        attn_output[:, :, q_start:q_end, :] = out_chunk
        del attn, out_chunk

    # Stash metrics on the module so the harness can pick them up after the
    # forward completes. We append (not overwrite) so multi-pass forwards
    # accumulate; the harness resets before each pass.
    if collect:
        slot = getattr(module, "_det_metrics", None)
        if slot is None:
            slot = {"entropy": [], "attn_to_anchor": []}
            module._det_metrics = slot
        slot["entropy"].append(
            entropy_sum / max(entropy_count, 1)
        )
        slot["attn_to_anchor"].append(attn_to_anchor)

    # Match eager's return shape: [B, Q, H, D]
    attn_output = attn_output.transpose(1, 2).contiguous()
    return attn_output, None


_REGISTERED = False


def register_chunked_eager(name: str = "chunked_eager"):
    """Register the chunked impl with transformers' attention registry.
    Idempotent. Returns the registered name."""
    global _REGISTERED
    from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS
    if name not in ALL_ATTENTION_FUNCTIONS.valid_keys():
        ALL_ATTENTION_FUNCTIONS.register(name, chunked_eager_attention_forward)
    _REGISTERED = True
    return name


def reset_layer_metrics(model):
    """Clear per-layer accumulators. Call before each forward you want
    to measure cleanly."""
    for layer in _iter_attn_modules(model):
        if hasattr(layer, "_det_metrics"):
            del layer._det_metrics


def collect_layer_metrics(model):
    """Walk attn modules in order and pull the most recent metric per layer.

    Returns:
      {"attention_entropy_per_layer": [float, ...],
       "attn_to_anchor_per_layer": [float|None, ...]}
    """
    ent, anchor = [], []
    for layer in _iter_attn_modules(model):
        m = getattr(layer, "_det_metrics", None)
        if m is None or not m["entropy"]:
            ent.append(None)
            anchor.append(None)
            continue
        ent.append(m["entropy"][-1])
        anchor.append(m["attn_to_anchor"][-1])
    return {
        "attention_entropy_per_layer": ent,
        "attn_to_anchor_per_layer": anchor,
    }


def _iter_attn_modules(model):
    """Yield self_attn modules in layer order. Works for Llama/Qwen2/Mistral
    -shaped models (model.model.layers[i].self_attn)."""
    inner = getattr(model, "model", model)
    layers = getattr(inner, "layers", None)
    if layers is None:
        return
    for layer in layers:
        attn = getattr(layer, "self_attn", None)
        if attn is not None:
            yield attn
