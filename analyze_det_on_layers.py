#!/usr/bin/env python3
"""DET I-D Balance applied to transformer layer activations.

Pre-registration: https://doi.org/10.5281/zenodo.20077301
Pre-registration commit (in this repo): writeup/PRE-REGISTRATION-det-on-layers.md
Patent: US Provisional 64/029,658

This script implements exactly the analysis specified in the pre-registration.
Any deviation from pre-registered parameters voids the lock.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

PRE_REG_DOI = "10.5281/zenodo.20077301"
PRE_REG_URL = "https://doi.org/10.5281/zenodo.20077301"

# === Pre-registered parameters (LOCKED) =====================================
TARGET_MODELS = {
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
}
TARGET_FRAMES = {"instruct", "instruct_no_repeat", "verify"}
COMPLIANCE_FRAMES = {"instruct", "instruct_no_repeat"}
DERIVATION_FRAMES = {"verify"}
TARGET_CHECKPOINTS = (500, 2000, 8000, 16000, 32000)
TARGET_ANCHOR_MODE = "mixed_tiered"

N_BANDS = 5
THETA = 2.0
W_J = 1.0
W_P = 0.0  # P term elided; setting permitted under patent claim 2

AUC_THRESHOLD = 0.70
BOOTSTRAP_ITERS = 10_000
PERMUTATION_ITERS = 10_000
RNG_SEED = 20260507  # locked seed for bootstrap and permutation reproducibility
MIN_CELLS = 36       # below this, run is aborted per pre-reg

REPO_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = REPO_ROOT / "results"
WRITEUP_DIR = REPO_ROOT / "writeup"
CELLS_CSV = RESULTS_DIR / "det-on-layers-cells.csv"
REPORT_MD = WRITEUP_DIR / "det-on-layers-results.md"


# === Header sanity check (executed before any computation) ==================
def _print_header() -> None:
    print(f"=== DET-on-Transformer-Layers Analysis ===")
    print(f"Pre-registration DOI: {PRE_REG_DOI}")
    print(f"Pre-registration URL: {PRE_REG_URL}")
    pre_reg_md = WRITEUP_DIR / "PRE-REGISTRATION-det-on-layers.md"
    if not pre_reg_md.exists():
        sys.exit(f"FATAL: pre-registration document not found at {pre_reg_md}")
    print(f"Pre-registration document: {pre_reg_md.relative_to(REPO_ROOT)}")
    print()


# === Eligibility filter =====================================================
def load_eligible_runs(results_dir: Path) -> list[dict]:
    runs = []
    for fp in sorted(results_dir.glob("*.jsonl")):
        try:
            with open(fp) as f:
                records = [json.loads(line) for line in f if line.strip()]
        except (json.JSONDecodeError, OSError):
            continue
        if not records:
            continue
        config = records[0]
        if config.get("model") not in TARGET_MODELS:
            continue
        if config.get("anchor_mode") != TARGET_ANCHOR_MODE:
            continue
        if config.get("frame") not in TARGET_FRAMES:
            continue
        if tuple(config.get("checkpoints", [])) != TARGET_CHECKPOINTS:
            continue
        # Confirm checkpoint records present
        cp_records = [r for r in records[1:] if "target_tokens" in r]
        if len(cp_records) != len(TARGET_CHECKPOINTS):
            continue
        runs.append({
            "path": fp,
            "model": config["model"],
            "frame": config["frame"],
            "checkpoints": cp_records,
        })
    return runs


# === DET pipeline (patent claim 1, w_J=1, w_P=0) ============================
def det_pipeline(activity: np.ndarray) -> tuple[float, float]:
    """Return (I, D) for a single cell's activity vector of length N_BANDS."""
    activity = np.asarray(activity, dtype=np.float64)
    if activity.sum() <= 0 or len(activity) != N_BANDS:
        return 0.0, 0.0
    p = activity / activity.sum()
    p_safe = np.where(p > 0, p, 1.0)  # avoid log(0)
    H = -np.sum(p * np.log(p_safe))
    N_eff = math.exp(H)
    if N_eff >= THETA:
        R = (N_eff - 1.0) / (N_BANDS - 1.0)
        C = N_eff / N_BANDS
        J = H / math.log(N_BANDS)
        S = C * (W_J * J + W_P * 0.0)  # P elided
    else:
        R = 0.0
        S = 0.0
    I = R * S
    uniform = np.full(N_BANDS, 1.0 / N_BANDS)
    D = float(jensenshannon(p, uniform, base=math.e))
    if not math.isfinite(D):
        D = 0.0
    return float(I), D


def bin_per_layer(per_layer: list[float], n_bands: int) -> np.ndarray:
    """numpy.array_split → mean per band."""
    arr = np.asarray(per_layer, dtype=np.float64)
    bands = np.array_split(arr, n_bands)
    return np.array([float(np.mean(b)) for b in bands])


# === Cell construction ======================================================
def build_cells(runs: list[dict]) -> list[dict]:
    cells = []
    for run in runs:
        for cp in run["checkpoints"]:
            wa = cp["with_anchor"]
            k_per_layer = wa["k_effective_rank_per_layer"]
            v_per_layer = wa["v_effective_rank_per_layer"]
            entropy_per_layer = wa["attention_entropy_per_layer"]
            attn_to_anchor = wa.get("attn_to_anchor_per_layer") or []
            kv_per_layer = [(k + v) / 2.0 for k, v in zip(k_per_layer, v_per_layer)]
            kv_bands = bin_per_layer(kv_per_layer, N_BANDS)
            entropy_bands = bin_per_layer(entropy_per_layer, N_BANDS)
            I_kv, D_kv = det_pipeline(kv_bands)
            I_ent, D_ent = det_pipeline(entropy_bands)
            override_count = sum(
                1 for d in cp.get("behavioral_deltas", [])
                if d.get("delta_violation", 0) > 0
            )
            cells.append({
                "model": run["model"],
                "frame": run["frame"],
                "checkpoint": int(cp["target_tokens"]),
                "regime": "compliance" if run["frame"] in COMPLIANCE_FRAMES else "derivation",
                "n_layers": len(kv_per_layer),
                "kv_mean": float(np.mean(kv_per_layer)),
                "attn_to_anchor_mean": float(np.mean(attn_to_anchor)) if attn_to_anchor else float("nan"),
                "I_kv": I_kv,
                "D_kv": D_kv,
                "I_ent": I_ent,
                "D_ent": D_ent,
                "override_count": override_count,
            })
    return cells


# === B from pooled z-scores =================================================
def compute_B(I_vec: np.ndarray, D_vec: np.ndarray) -> np.ndarray:
    def z(x: np.ndarray) -> np.ndarray:
        s = x.std(ddof=0)
        return (x - x.mean()) / s if s > 0 else np.zeros_like(x)
    return np.abs(z(I_vec) - z(D_vec))


# === AUC with pre-registered direction handling =============================
def directed_auc(scores: np.ndarray, labels: np.ndarray) -> tuple[float, bool]:
    """Pre-registered direction: B HIGHER in derivation (label=1).
    Returns (auc, wrong_direction_flag).
    If wrong direction, AUC is reported as min(auc, 1-auc) per pre-reg.
    """
    auc = roc_auc_score(labels, scores)
    if auc < 0.5:
        return float(min(auc, 1 - auc)), True
    return float(auc), False


def bootstrap_auc(scores: np.ndarray, labels: np.ndarray,
                  iters: int, rng: np.random.Generator) -> tuple[float, float]:
    n = len(labels)
    aucs = []
    for _ in range(iters):
        idx = rng.integers(0, n, size=n)
        sl = labels[idx]
        if len(np.unique(sl)) < 2:
            continue
        try:
            aucs.append(roc_auc_score(sl, scores[idx]))
        except ValueError:
            continue
    aucs = np.array(aucs)
    return float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))


def permutation_auc(scores: np.ndarray, labels: np.ndarray,
                    iters: int, rng: np.random.Generator) -> np.ndarray:
    aucs = []
    for _ in range(iters):
        permuted = rng.permutation(labels)
        try:
            aucs.append(roc_auc_score(permuted, scores))
        except ValueError:
            continue
    return np.array(aucs)


# === Decision rule ==========================================================
def apply_decision_rule(auc_pt: float, ci_lower: float,
                        beats_baselines: bool, wrong_direction: bool) -> str:
    if wrong_direction:
        return "NEGATIVE: wrong-direction signal; no patent claim added."
    if auc_pt >= AUC_THRESHOLD and ci_lower > 0.5:
        if beats_baselines:
            return ("POSITIVE: B classifies regime above pre-registered threshold "
                    "AND beats raw-feature baselines. "
                    "Add transformer embodiment to 64/029,658 conversion.")
        else:
            return ("WEAK POSITIVE: B classifies regime above threshold but does NOT "
                    "beat raw-feature baselines. Report; no patent claim added.")
    return ("NULL: AUC below 0.70 or 95% CI includes 0.5. "
            "DET-on-transformer-layers does not generalize at patent-default parameters. "
            "Report cleanly; no patent claim added.")


# === Reporting ==============================================================
def write_cells_csv(cells: list[dict], B_kv: np.ndarray, B_ent: np.ndarray) -> None:
    fieldnames = [
        "model", "frame", "checkpoint", "regime",
        "n_layers", "kv_mean", "attn_to_anchor_mean",
        "I_kv", "D_kv", "B_kv",
        "I_ent", "D_ent", "B_ent",
        "override_count",
    ]
    with open(CELLS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for cell, b_kv, b_ent in zip(cells, B_kv, B_ent):
            row = {**{k: cell[k] for k in fieldnames if k in cell},
                   "B_kv": b_kv, "B_ent": b_ent}
            writer.writerow(row)


def write_report(report_lines: list[str]) -> None:
    REPORT_MD.write_text("\n".join(report_lines))


# === Main ===================================================================
def main() -> int:
    _print_header()

    runs = load_eligible_runs(RESULTS_DIR)
    print(f"Eligible runs: {len(runs)}")
    cells = build_cells(runs)
    print(f"Cells assembled: {len(cells)}")
    n_compliance = sum(1 for c in cells if c["regime"] == "compliance")
    n_derivation = sum(1 for c in cells if c["regime"] == "derivation")
    print(f"  compliance: {n_compliance}, derivation: {n_derivation}")

    if len(cells) < MIN_CELLS:
        print(f"FATAL: cell count {len(cells)} below pre-registered minimum {MIN_CELLS}.")
        print("Run aborted per pre-registration.")
        return 1

    rng = np.random.default_rng(RNG_SEED)

    I_kv = np.array([c["I_kv"] for c in cells])
    D_kv = np.array([c["D_kv"] for c in cells])
    I_ent = np.array([c["I_ent"] for c in cells])
    D_ent = np.array([c["D_ent"] for c in cells])
    B_kv = compute_B(I_kv, D_kv)
    B_ent = compute_B(I_ent, D_ent)

    labels = np.array([1 if c["regime"] == "derivation" else 0 for c in cells])

    write_cells_csv(cells, B_kv, B_ent)
    print(f"Wrote {CELLS_CSV.relative_to(REPO_ROOT)}")

    # === Primary endpoint ===
    auc_kv, wrong_dir = directed_auc(B_kv, labels)
    ci_lower, ci_upper = bootstrap_auc(B_kv, labels, BOOTSTRAP_ITERS, rng)

    # === Baselines ===
    kv_mean = np.array([c["kv_mean"] for c in cells])
    auc_kv_mean_raw = roc_auc_score(labels, kv_mean)
    auc_kv_mean = max(auc_kv_mean_raw, 1 - auc_kv_mean_raw)

    attn_anchor = np.array([c["attn_to_anchor_mean"] for c in cells])
    valid_attn = ~np.isnan(attn_anchor)
    if valid_attn.sum() == len(labels):
        auc_attn_raw = roc_auc_score(labels, attn_anchor)
        auc_attn = max(auc_attn_raw, 1 - auc_attn_raw)
    else:
        auc_attn = float("nan")

    perm_aucs = permutation_auc(B_kv, labels, PERMUTATION_ITERS, rng)
    perm_aucs_directed = np.maximum(perm_aucs, 1 - perm_aucs)
    perm_p95 = float(np.percentile(perm_aucs_directed, 95))

    beats_baselines = (
        auc_kv > auc_kv_mean
        and (math.isnan(auc_attn) or auc_kv > auc_attn)
        and auc_kv > perm_p95
    )

    # === Secondary endpoints ===
    per_model: dict[str, dict] = {}
    for model in TARGET_MODELS:
        idx = np.array([i for i, c in enumerate(cells) if c["model"] == model])
        if len(idx) > 0 and len(np.unique(labels[idx])) >= 2:
            sub_auc, _ = directed_auc(B_kv[idx], labels[idx])
            sub_lo, sub_hi = bootstrap_auc(B_kv[idx], labels[idx], 2000, rng)
            per_model[model] = {"auc": sub_auc, "ci": (sub_lo, sub_hi), "n": int(len(idx))}

    per_checkpoint: dict[int, dict] = {}
    for cp in TARGET_CHECKPOINTS:
        idx = np.array([i for i, c in enumerate(cells) if c["checkpoint"] == cp])
        if len(idx) > 0 and len(np.unique(labels[idx])) >= 2:
            sub_auc, _ = directed_auc(B_kv[idx], labels[idx])
            sub_lo, sub_hi = bootstrap_auc(B_kv[idx], labels[idx], 2000, rng)
            per_checkpoint[cp] = {"auc": sub_auc, "ci": (sub_lo, sub_hi), "n": int(len(idx))}

    overrides = np.array([c["override_count"] for c in cells])
    spearman_rho, spearman_p = spearmanr(B_kv, overrides)

    auc_ent, _ = directed_auc(B_ent, labels)
    ci_ent_lower, ci_ent_upper = bootstrap_auc(B_ent, labels, BOOTSTRAP_ITERS, rng)

    # === Decision ===
    decision = apply_decision_rule(auc_kv, ci_lower, beats_baselines, wrong_dir)

    # === Report ===
    lines = [
        "# DET-on-Transformer-Layers — Results",
        "",
        f"**Pre-registration:** [{PRE_REG_DOI}]({PRE_REG_URL})",
        f"**Analysis script:** `analyze_det_on_layers.py` (this repo)",
        "**Pipeline parameters (locked):** N=5, theta=2.0, w_J=1.0, w_P=0.0",
        "",
        "## Cell pool",
        "",
        f"- Total cells: **{len(cells)}**",
        f"- Compliance (instruct + instruct_no_repeat): {n_compliance}",
        f"- Derivation (verify): {n_derivation}",
        "",
        "## Primary endpoint",
        "",
        f"**AUC of B (K/V rank activity scalar) for compliance vs derivation:** {auc_kv:.4f}",
        f"**95% CI (bootstrap, {BOOTSTRAP_ITERS:,} iters):** [{ci_lower:.4f}, {ci_upper:.4f}]",
        f"**Wrong-direction flag:** {wrong_dir}",
        "",
        "## Baselines",
        "",
        f"- Mean K/V rank alone: AUC = {auc_kv_mean:.4f}",
        f"- Mean attention-to-anchor alone: AUC = {auc_attn:.4f}"
            if not math.isnan(auc_attn) else f"- Mean attention-to-anchor: NaN (incomplete data)",
        f"- Permutation null 95th percentile: AUC = {perm_p95:.4f}",
        f"- **B beats all baselines:** {beats_baselines}",
        "",
        "## Secondary endpoints",
        "",
        "### Per-model AUC",
        "",
        "| Model | AUC | 95% CI | n |",
        "|-------|-----|--------|---|",
    ]
    for model, info in sorted(per_model.items()):
        lines.append(
            f"| {model} | {info['auc']:.4f} | "
            f"[{info['ci'][0]:.4f}, {info['ci'][1]:.4f}] | {info['n']} |"
        )
    lines += [
        "",
        "### Per-checkpoint AUC",
        "",
        "| Checkpoint | AUC | 95% CI | n |",
        "|-----------:|-----|--------|---|",
    ]
    for cp, info in sorted(per_checkpoint.items()):
        lines.append(
            f"| {cp:>10} | {info['auc']:.4f} | "
            f"[{info['ci'][0]:.4f}, {info['ci'][1]:.4f}] | {info['n']} |"
        )
    lines += [
        "",
        "### Spearman: B vs override count",
        "",
        f"- rho = {spearman_rho:.4f}, p = {spearman_p:.4g}",
        "",
        "### Robustness: attention entropy as activity scalar",
        "",
        f"- AUC = {auc_ent:.4f}, 95% CI [{ci_ent_lower:.4f}, {ci_ent_upper:.4f}]",
        "",
        "## Decision",
        "",
        f"**{decision}**",
        "",
        "## Cell-level data",
        "",
        f"See `results/det-on-layers-cells.csv` ({len(cells)} rows).",
        "",
    ]
    write_report(lines)
    print(f"Wrote {REPORT_MD.relative_to(REPO_ROOT)}")
    print()
    print(f"PRIMARY: AUC(B,K/V) = {auc_kv:.4f}, 95% CI [{ci_lower:.4f}, {ci_upper:.4f}]")
    print(f"DECISION: {decision}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
