#!/usr/bin/env python3
"""EXPLORATORY (NOT pre-registered): where does the regime signal live?

The pre-registered analysis (analyze_det_on_layers.py) asked one locked
question and got a null. This script asks the broader question that
remains scientifically open: does ANY simple feature-and-aggregation
combination of the available per-layer transformer state distinguish
compliance from derivation regime in this 45-cell dataset?

Findings here are HYPOTHESIS-GENERATING. They do not satisfy any
pre-registered hypothesis. Any claim derived from them must be
re-tested on independent data with a fresh pre-registration before it
can be cited as confirmatory.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial.distance import jensenshannon
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut, cross_val_predict

REPO_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = REPO_ROOT / "results"
WRITEUP_DIR = REPO_ROOT / "writeup"
REPORT_MD = WRITEUP_DIR / "det-on-layers-exploration.md"

TARGET_MODELS = {
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
}
COMPLIANCE_FRAMES = {"instruct", "instruct_no_repeat"}
TARGET_CHECKPOINTS = (500, 2000, 8000, 16000, 32000)
RNG_SEED = 20260507
THETA = 2.0


def load_cells() -> list[dict]:
    cells = []
    for fp in sorted(RESULTS_DIR.glob("*.jsonl")):
        recs = [json.loads(l) for l in open(fp) if l.strip()]
        if not recs:
            continue
        cfg = recs[0]
        if cfg.get("model") not in TARGET_MODELS:
            continue
        if cfg.get("anchor_mode") != "mixed_tiered":
            continue
        if cfg.get("frame") not in {"instruct", "instruct_no_repeat", "verify"}:
            continue
        if tuple(cfg.get("checkpoints", [])) != TARGET_CHECKPOINTS:
            continue
        cp_records = [r for r in recs[1:] if "target_tokens" in r]
        if len(cp_records) != 5:
            continue
        for cp in cp_records:
            wa = cp["with_anchor"]
            cells.append({
                "model": cfg["model"],
                "frame": cfg["frame"],
                "checkpoint": int(cp["target_tokens"]),
                "regime": "compliance" if cfg["frame"] in COMPLIANCE_FRAMES else "derivation",
                "k": np.array(wa["k_effective_rank_per_layer"], dtype=np.float64),
                "v": np.array(wa["v_effective_rank_per_layer"], dtype=np.float64),
                "ent": np.array(wa["attention_entropy_per_layer"], dtype=np.float64),
                "attn_anchor": np.array(wa.get("attn_to_anchor_per_layer") or [], dtype=np.float64),
                "override_count": sum(
                    1 for d in cp.get("behavioral_deltas", []) if d.get("delta_violation", 0) > 0
                ),
            })
    return cells


def det_pipeline(activity: np.ndarray, n_bands: int) -> tuple[float, float]:
    """w_J=1, w_P=0. Returns (I, D)."""
    if activity.sum() <= 0:
        return 0.0, 0.0
    bands = np.array_split(activity, n_bands)
    a = np.array([float(np.mean(b)) for b in bands])
    if a.sum() <= 0:
        return 0.0, 0.0
    p = a / a.sum()
    p_safe = np.where(p > 0, p, 1.0)
    H = -np.sum(p * np.log(p_safe))
    N_eff = math.exp(H)
    if N_eff >= THETA:
        R = (N_eff - 1) / (n_bands - 1)
        C = N_eff / n_bands
        J = H / math.log(n_bands)
        S = C * J
    else:
        R = 0.0
        S = 0.0
    I = R * S
    uniform = np.full(n_bands, 1.0 / n_bands)
    D = float(jensenshannon(p, uniform, base=math.e))
    if not math.isfinite(D):
        D = 0.0
    return float(I), D


def compute_B(I_vec: np.ndarray, D_vec: np.ndarray) -> np.ndarray:
    def z(x):
        s = x.std(ddof=0)
        return (x - x.mean()) / s if s > 0 else np.zeros_like(x)
    return np.abs(z(I_vec) - z(D_vec))


def directed_auc_with_ci(scores: np.ndarray, labels: np.ndarray,
                         rng: np.random.Generator, iters: int = 5000) -> tuple[float, float, float, bool]:
    auc = roc_auc_score(labels, scores)
    wrong_dir = auc < 0.5
    auc_dir = max(auc, 1 - auc)
    n = len(labels)
    boot = []
    for _ in range(iters):
        idx = rng.integers(0, n, n)
        if len(np.unique(labels[idx])) < 2:
            continue
        try:
            a = roc_auc_score(labels[idx], scores[idx])
            boot.append(max(a, 1 - a))
        except ValueError:
            continue
    boot = np.array(boot)
    return float(auc_dir), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)), wrong_dir


def sweep_det(cells, scalars: dict, n_bands_list: list[int], labels, rng):
    rows = []
    for scalar_name, scalar_fn in scalars.items():
        for nb in n_bands_list:
            I_vec, D_vec = [], []
            valid = True
            for c in cells:
                v = scalar_fn(c)
                if v is None or len(v) < nb:
                    valid = False
                    break
                I, D = det_pipeline(v, nb)
                I_vec.append(I)
                D_vec.append(D)
            if not valid:
                rows.append((scalar_name, nb, float("nan"), float("nan"), float("nan"), False))
                continue
            B = compute_B(np.array(I_vec), np.array(D_vec))
            auc, lo, hi, wd = directed_auc_with_ci(B, labels, rng)
            rows.append((scalar_name, nb, auc, lo, hi, wd))
    return rows


def upper_bound_logistic(cells, labels, rng) -> dict:
    """How well can ANY classifier do on this data, using 5-band-mean of all 4 features?

    Uses leave-one-group-out by model to avoid leak; then leave-one-checkpoint-out.
    Reports cross-validated predictions' AUC.
    """
    feat_cols = []
    for c in cells:
        row = []
        for arr in (c["k"], c["v"], c["ent"], c["attn_anchor"]):
            if len(arr) == 0:
                row.extend([0.0] * 5)
            else:
                bands = np.array_split(arr, 5)
                row.extend(float(np.mean(b)) for b in bands)
        feat_cols.append(row)
    X = np.asarray(feat_cols)
    y = np.asarray(labels)
    out = {}
    for group_name, groups in [
        ("LOOCV-by-model", [c["model"] for c in cells]),
        ("LOOCV-by-checkpoint", [c["checkpoint"] for c in cells]),
    ]:
        cv = LeaveOneGroupOut()
        groups_arr = np.array(groups)
        try:
            preds = cross_val_predict(
                LogisticRegression(max_iter=2000, C=1.0),
                X, y, cv=cv.split(X, y, groups_arr),
                method="predict_proba",
            )[:, 1]
            auc = roc_auc_score(y, preds)
            out[group_name] = max(auc, 1 - auc)
        except Exception as e:
            out[group_name] = float("nan")
            out[f"{group_name}_error"] = str(e)
    # Also unrestricted 5-fold
    from sklearn.model_selection import StratifiedKFold
    cv5 = StratifiedKFold(n_splits=5, shuffle=True, random_state=RNG_SEED)
    try:
        preds = cross_val_predict(
            LogisticRegression(max_iter=2000, C=1.0),
            X, y, cv=cv5,
            method="predict_proba",
        )[:, 1]
        auc = roc_auc_score(y, preds)
        out["StratifiedKFold-5"] = max(auc, 1 - auc)
    except Exception as e:
        out["StratifiedKFold-5"] = float("nan")
    return out


def main() -> int:
    cells = load_cells()
    print(f"Cells: {len(cells)}")
    if len(cells) == 0:
        return 1

    labels = np.array([1 if c["regime"] == "derivation" else 0 for c in cells])
    rng = np.random.default_rng(RNG_SEED)

    scalars = {
        "K_only": lambda c: c["k"],
        "V_only": lambda c: c["v"],
        "K_plus_V_mean": lambda c: 0.5 * (c["k"] + c["v"]),
        "K_minus_V": lambda c: np.abs(c["k"] - c["v"]),
        "attention_entropy": lambda c: c["ent"],
        "attn_to_anchor": lambda c: c["attn_anchor"] if len(c["attn_anchor"]) > 0 else None,
    }
    n_bands_list = [3, 4, 5, 6, 7, 8]

    print("\n=== DET pipeline sweep over activity scalars × N bands ===\n")
    rows = sweep_det(cells, scalars, n_bands_list, labels, rng)

    lines = [
        "# Exploration: where does the regime signal live?",
        "",
        "**Status: EXPLORATORY. Hypothesis-generating. NOT pre-registered.**",
        "",
        "These results do not satisfy any pre-registered hypothesis. The pre-registered analysis "
        "(`analyze_det_on_layers.py`, locked at Zenodo DOI 10.5281/zenodo.20077301) returned a "
        "clean null and that result stands. The exploration below answers a different question: "
        "given the same data, is there ANY simple feature/aggregation choice that distinguishes "
        "compliance from derivation regime, and if so, what's the upper bound? Anything compelling "
        "found here would need to be re-tested on independent data under a fresh pre-registration "
        "before it could be claimed as a real finding.",
        "",
        f"**Cell pool:** {len(cells)} cells, {sum(labels==0)} compliance, {sum(labels==1)} derivation.",
        "**Bootstrap iters:** 5,000 per cell.",
        "",
        "## DET pipeline — sweep over activity scalars × N bands",
        "",
        "Same DET pipeline as the pre-reg (w_J=1, w_P=0, theta=2.0, K/V binning per `numpy.array_split`). "
        "Only the activity scalar and N vary. AUCs are folded to >= 0.5 (direction-agnostic) since "
        "this is exploration, not hypothesis testing.",
        "",
        "| Activity scalar | N bands | AUC | 95% CI | Wrong dir |",
        "|-----------------|--------:|----:|-------:|----------:|",
    ]
    best = None
    for scalar, nb, auc, lo, hi, wd in rows:
        lines.append(f"| {scalar} | {nb} | {auc:.4f} | [{lo:.4f}, {hi:.4f}] | {wd} |")
        if not math.isnan(auc) and (best is None or auc > best[2]):
            best = (scalar, nb, auc, lo, hi, wd)
    if best:
        lines += [
            "",
            f"**Best DET cell from sweep:** {best[0]}, N={best[1]}, AUC={best[2]:.4f}, "
            f"95% CI [{best[3]:.4f}, {best[4]:.4f}].",
        ]

    print("\n=== Upper-bound: logistic regression on all 5-band features ===\n")
    ub = upper_bound_logistic(cells, labels, rng)
    lines += [
        "",
        "## Upper bound — logistic regression on the 5-band features",
        "",
        "If the data simply does not contain cell-level regime signal at coarse-band resolution, "
        "no DET parameterization will find it. This run uses logistic regression on the 5-band "
        "means of K rank, V rank, attention entropy, and attention-to-anchor (20 features total) "
        "as an upper-bound check.",
        "",
        "| CV scheme | AUC |",
        "|-----------|----:|",
    ]
    for k, v in ub.items():
        if "error" not in k:
            lines.append(f"| {k} | {v:.4f}" if isinstance(v, float) and not math.isnan(v) else f"| {k} | NaN |")
    lines += [
        "",
        "## Reading",
        "",
        "If best DET AUC and LR upper-bound are both around 0.5, the cell-level regime classification "
        "problem at this resolution is genuinely hard with this data — no feature engineering will "
        "rescue it within the current 45-cell, single-snapshot, coarse-band scope. The honest next "
        "moves would be: (a) more cells (more models, more checkpoints), (b) finer time-axis aggregation "
        "(per-token rather than per-checkpoint), or (c) reformulating regime as a probe-level rather "
        "than cell-level label.",
        "",
        "If the LR upper bound clearly exceeds the best DET cell, signal exists but is not in the "
        "shape DET expects. That would point at which features actually carry the regime information "
        "and motivate a different (non-DET) framework.",
        "",
        "Either reading is informative. Neither is confirmatory of anything until replicated on new data.",
    ]

    REPORT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT_MD.relative_to(REPO_ROOT)}")
    print()
    print(f"Best DET AUC: {best[2]:.4f} ({best[0]}, N={best[1]})")
    print(f"LR LOOCV-by-model AUC: {ub.get('LOOCV-by-model', float('nan')):.4f}")
    print(f"LR LOOCV-by-checkpoint AUC: {ub.get('LOOCV-by-checkpoint', float('nan')):.4f}")
    print(f"LR StratifiedKFold-5 AUC: {ub.get('StratifiedKFold-5', float('nan')):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
