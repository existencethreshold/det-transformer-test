import json
import numpy as np
import os
from collections import defaultdict

files = {
    "SmolLM-135M": "/home/dietpi/det-transformer-test/results/20260504T054917Z_HuggingFaceTB_SmolLM2-135M-Instruct.jsonl",
    "Qwen-1.5B": "/home/dietpi/det-transformer-test/results/20260505T061521Z_Qwen_Qwen2.5-1.5B-Instruct.jsonl",
    "Qwen-3B": "/home/dietpi/det-transformer-test/results/20260507T002154Z_Qwen_Qwen2.5-3B-Instruct.jsonl",
    "Qwen-7B-attn": "/home/dietpi/det-transformer-test/results/20260505T135700Z_Qwen_Qwen2.5-7B-Instruct.jsonl",
    "Mistral-7B": "/home/dietpi/det-transformer-test/results/20260506T222407Z_mistralai_Mistral-7B-Instruct-v0.3.jsonl",
    "OLMo-2-7B": "/home/dietpi/det-transformer-test/results/20260507T000322Z_allenai_OLMo-2-1124-7B-Instruct.jsonl",
    "Llama-3.1-8B": "/home/dietpi/det-transformer-test/results/20260507T011103Z_meta-llama_Llama-3.1-8B-Instruct.jsonl"
}

def load_data(filepath):
    data = []
    with open(filepath, 'r') as f:
        header = json.loads(f.readline())
        for line in f:
            data.append(json.loads(line))
    return header, data

def analyze_surge():
    print("--- Qwen Surge Localization (8K) ---")
    for name in ["Qwen-1.5B", "Qwen-3B"]:
        _, records = load_data(files[name])
        rec_2k = next((r for r in records if r['target_tokens'] == 2000), None)
        rec_8k = next((r for r in records if r['target_tokens'] == 8000), None)
        rec_16k = next((r for r in records if r['target_tokens'] == 16000), None)
        
        if rec_2k and rec_8k and rec_16k:
            attn_2k = rec_2k['with_anchor'].get('attn_to_anchor_per_layer')
            attn_8k = rec_8k['with_anchor'].get('attn_to_anchor_per_layer')
            attn_16k = rec_16k['with_anchor'].get('attn_to_anchor_per_layer')
            
            if attn_2k and attn_8k and attn_16k:
                attn_2k = np.array(attn_2k)
                attn_8k = np.array(attn_8k)
                attn_16k = np.array(attn_16k)
                
                diff_8k_2k = attn_8k - attn_2k
                diff_16k_8k = attn_16k - attn_8k
                
                top_rising_layers = np.argsort(diff_8k_2k)[-5:][::-1]
                print(f"{name} Rising Layers (8K vs 2K): {top_rising_layers}, diffs: {diff_8k_2k[top_rising_layers]}")
                
                top_falling_layers = np.argsort(diff_16k_8k)[:5]
                print(f"{name} Falling Layers (16K vs 8K): {top_falling_layers}, diffs: {diff_16k_8k[top_falling_layers]}")
            else:
                print(f"{name}: Missing attn data for some ckpts.")

def analyze_kv_rank():
    print("\n--- KV Rank Trajectories ---")
    for name, path in files.items():
        _, records = load_data(path)
        print(f"{name}:")
        for r in records:
            if 'with_anchor' not in r:
                continue
            ctx = r['target_tokens']
            k_rank = r['with_anchor'].get('k_effective_rank_per_layer')
            v_rank = r['with_anchor'].get('v_effective_rank_per_layer')
            if k_rank and v_rank:
                mean_k = np.mean(k_rank)
                mean_v = np.mean(v_rank)
                print(f"  {ctx:5}: K-rank {mean_k:6.2f}, V-rank {mean_v:6.2f}, Ratio K/V {mean_k/mean_v:.3f}")

def analyze_sentinels():
    print("\n--- Anchor Sentinels (Layers keeping >0.5 attn at max ctx) ---")
    for name, path in files.items():
        _, records = load_data(path)
        valid_recs = [r for r in records if 'with_anchor' in r and r['with_anchor'].get('attn_to_anchor_per_layer')]
        if valid_recs:
            last_rec = valid_recs[-1]
            attn = last_rec['with_anchor']['attn_to_anchor_per_layer']
            sentinels = [i for i, val in enumerate(attn) if val > 0.5]
            print(f"{name} (ctx {last_rec['target_tokens']}): {sentinels}")

def analyze_answers():
    print("\n--- Answer Patterns (Failed Overrides) ---")
    for name, path in files.items():
        _, records = load_data(path)
        rejections = 0
        total_fails = 0
        for r in records:
            if 'with_anchor' not in r: continue
            for probe in r['with_anchor']['behavioral_probes']:
                if probe['fidelity_hits'] == 0:
                    total_fails += 1
                    ans = probe['answer'].lower()
                    if any(x in ans for x in ["instead", "actually", "override", "correct", "however", "contrary", "but"]):
                        rejections += 1
        if total_fails > 0:
            print(f"{name}: {rejections}/{total_fails} explicit rejections found.")

def analyze_probe_order():
    print("\n--- Probe Break Order ---")
    for name, path in files.items():
        _, records = load_data(path)
        probe_breaks = {}
        for r in records:
            if 'with_anchor' not in r: continue
            ctx = r['target_tokens']
            for probe in r['with_anchor']['behavioral_probes']:
                if probe['fidelity_hits'] == 0 and probe['id'] not in probe_breaks:
                    probe_breaks[probe['id']] = ctx
        sorted_breaks = sorted(probe_breaks.items(), key=lambda x: x[1])
        print(f"{name}: {sorted_breaks}")

def analyze_entropy_causal():
    print("\n--- Entropy Causal Effect (With - Without) ---")
    for name, path in files.items():
        _, records = load_data(path)
        print(f"{name}:")
        for r in records:
            if 'with_anchor' not in r or 'without_anchor' not in r: continue
            ctx = r['target_tokens']
            e_with = r['with_anchor'].get('attention_entropy_per_layer')
            e_without = r['without_anchor'].get('attention_entropy_per_layer')
            if e_with and e_without:
                diff = np.mean(e_with) - np.mean(e_without)
                print(f"  {ctx:5}: Mean Entropy Diff {diff:.4f}")

def analyze_everest_surge():
    print("\n--- Everest Country Probe (Qwen-1.5B) ---")
    _, records = load_data(files["Qwen-1.5B"])
    for r in records:
        if 'with_anchor' not in r: continue
        probe = next(p for p in r['with_anchor']['behavioral_probes'] if p['id'] == 'everest_country')
        print(f"  ctx {r['target_tokens']:5}: fidelity_hits={probe['fidelity_hits']}, answer={probe['answer'][:30]}...")

def analyze_kv_correlation():
    print("\n--- Mean V-Rank vs Overrides Correlation ---")
    for name, path in files.items():
        _, records = load_data(path)
        v_ranks = []
        overrides = []
        for r in records:
            if 'with_anchor' not in r: continue
            v_rank = r['with_anchor'].get('v_effective_rank_per_layer')
            if v_rank:
                v_ranks.append(np.mean(v_rank))
                # Count successful overrides (delta_fidelity > 0 or fidelity_hits > 0 if without_anchor fidelity is 0)
                # Actually, just use fidelity_hits from with_anchor
                hits = sum(p['fidelity_hits'] for p in r['with_anchor']['behavioral_probes'])
                overrides.append(hits)
        
        if len(v_ranks) > 1:
            corr = np.corrcoef(v_ranks, overrides)[0, 1]
            print(f"{name}: Correlation Mean V-Rank / Total Hits = {corr:.4f}")
            # print(f"  V-ranks: {v_ranks}")
            # print(f"  Hits:    {overrides}")

def analyze_v_rank_collapse_layers():
    print("\n--- Layers with fastest V-Rank Collapse ---")
    for name, path in files.items():
        _, records = load_data(path)
        valid_recs = [r for r in records if 'with_anchor' in r and r['with_anchor'].get('v_effective_rank_per_layer')]
        if len(valid_recs) < 2: continue
        v0 = np.array(valid_recs[0]['with_anchor']['v_effective_rank_per_layer'])
        vn = np.array(valid_recs[-1]['with_anchor']['v_effective_rank_per_layer'])
        diff = vn - v0
        top_collapsing = np.argsort(diff)[:5]
        print(f"{name}: Top collapsing V-rank layers: {top_collapsing}, diffs: {diff[top_collapsing]}")

def analyze_kv_causal():
    print("\n--- KV Rank Causal Effect (With - Without) ---")
    for name, path in files.items():
        _, records = load_data(path)
        print(f"{name}:")
        for r in records:
            if 'with_anchor' not in r or 'without_anchor' not in r: continue
            ctx = r['target_tokens']
            k_with = r['with_anchor'].get('k_effective_rank_per_layer')
            k_without = r['without_anchor'].get('k_effective_rank_per_layer')
            v_with = r['with_anchor'].get('v_effective_rank_per_layer')
            v_without = r['without_anchor'].get('v_effective_rank_per_layer')
            if k_with and k_without and v_with and v_without:
                k_diff = np.mean(k_with) - np.mean(k_without)
                v_diff = np.mean(v_with) - np.mean(v_without)
                print(f"  {ctx:5}: K-diff {k_diff:6.2f}, V-diff {v_diff:6.2f}")

if __name__ == "__main__":
    analyze_surge()
    analyze_kv_rank()
    analyze_sentinels()
    analyze_answers()
    analyze_probe_order()
    analyze_entropy_causal()
    analyze_everest_surge()
    analyze_kv_correlation()
    analyze_v_rank_collapse_layers()
    analyze_kv_causal()
