# validation_publication.py
import os
import json
import time
import statistics
from collections import defaultdict, Counter

# Azure (optional: only for mismatch reasoning, not re-eval)
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Metrics
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import cohen_kappa_score, confusion_matrix, classification_report
from sentence_transformers import SentenceTransformer
from bert_score import score as bertscore_score
from rouge_score import rouge_scorer

# Utils
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns

# =========================
# Config — EDIT THESE PATHS
# =========================
GROUND_TRUTH_PATH = r"C:\Users\b-fkabir\Desktop\New folder\gorilla\evaluatoroutput\groundtruthgeval\groundthurht.jsonl"
EVALUATION_PATH   = r"C:\Users\b-fkabir\Desktop\New folder\gorilla\evaluatoroutput\groundtruthgeval\ev4.1nano.jsonl"
OUTPUT_PATH       = r"C:\Users\b-fkabir\Desktop\New folder\gorilla\Finaloutput\final_output4.3.jsonl"

# Azure OpenAI (optional: used only to generate a short mismatch explanation)
ENDPOINT_URL    = os.getenv("ENDPOINT_URL", "https://aoai-l-swedencentral.openai.azure.com/")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME", "gpt-4o-2024-08-06-global")
API_VERSION     = "2024-08-01-preview"

# Controls
INCLUDE_REFUSED_IN_CM     = True   # also produce 3-class CM if REFUSED present
USE_GPT_REASONING         = True   # only to *explain* mismatches (no re-evaluation)
MAX_LLM_RETRIES           = 3
RETRY_BACKOFF_BASE_S      = 1.0    # exponential backoff base, effective wait = base * (2**i)
SAVE_FIG_DPI              = 200

# =========================
# Prompt (safe markers; no {} formatting collisions)
# =========================
REASON_PROMPT_TEMPLATE = (
    "You will be given two evaluation results for the SAME (QueryID, type).\n"
    "Briefly EXPLAIN why they disagree on key fields. Do NOT re-evaluate.\n\n"
    "Focus ONLY on:\n"
    "- overall_verdict (PASS/FAIL/REFUSED)\n"
    "- satisfaction_level (±1 tolerance context)\n"
    "- reference_usage (boolean)\n\n"
    "Ground Truth evaluation_result JSON:\n__GT__\n\n"
    "Evaluator output evaluation_result JSON:\n__EV__\n\n"
    "Return JSON ONLY:\n"
    "{\n"
    '  "reason": "one or two sentences explaining likely reasons for the mismatch"\n'
    "}\n"
)

# =========================
# IO helpers
# =========================
def load_jsonl_safe(path):
    rows = []
    bad = 0
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            s = line.strip()
            if not s:
                continue
            try:
                rows.append(json.loads(s))
            except Exception as e:
                bad += 1
                print(f"⚠️ Skipping bad JSON line {i} in {os.path.basename(path)}: {e}")
    if bad:
        print(f"⚠️ {bad} bad lines skipped in {os.path.basename(path)}")
    return rows

def write_jsonl_overwrite(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path

# =========================
# Normalization helpers (no type normalization)
# =========================
SAT_MAP = {
    "poor": 0, "0": 0, 0: 0,
    "fair": 1, "1": 1, 1: 1,
    "good": 2, "2": 2, 2: 2,
    "excellent": 3, "3": 3, 3: 3
}

def norm_sat(x):
    if x is None: return None
    return SAT_MAP.get(str(x).strip().lower(), None)

def verdict_only(x):
    return "" if x is None else str(x).strip().upper()

def yesno_bool(x):
    if isinstance(x, bool): return x
    if x is None: return None
    s = str(x).strip().lower()
    if s in ("yes", "true", "y", "1"): return True
    if s in ("no", "false", "n", "0"): return False
    return None

def get_eval_type(eval_obj):
    # keep exact type values: 'tool', 'text/tool', 'text'
    t = (eval_obj.get("type") or eval_obj.get("response_type") or eval_obj.get("eval_type") or "").strip().lower()
    return t or None

def normalize_eval_obj(e):
    # normalize only the fields we compare; do not re-evaluate
    return {
        "verdict": verdict_only(e.get("overall_verdict") or e.get("verdict")),
        "satisfaction_level": norm_sat(e.get("satisfaction_level") or e.get("satisfaction") or e.get("score_level")),
        "reference_usage": yesno_bool(e.get("reference_usage") or e.get("used_reference") or e.get("reference_used")),
        "type": get_eval_type(e)
    }

# =========================
# Azure client (optional)
# =========================
def init_azure_client():
    if not USE_GPT_REASONING:
        return None
    try:
        client = AzureOpenAI(
            azure_endpoint=ENDPOINT_URL,
            azure_ad_token_provider=get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            ),
            api_version=API_VERSION,
        )
        return client
    except Exception as e:
        print(f"⚠️ Azure client not available: {e}")
        return None

def call_llm_json(client, prompt, key_str):
    if client is None:
        return None
    err = None
    for i in range(MAX_LLM_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": "Return ONLY a valid JSON object. No commentary."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            content = resp.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            err = e
            wait = RETRY_BACKOFF_BASE_S * (2 ** i)
            print(f"⚠️ GPT reasoning retry {i+1}/{MAX_LLM_RETRIES} for {key_str}: {e} (waiting {wait:.1f}s)")
            time.sleep(wait)
    print(f"❌ GPT reasoning failed for {key_str}: {err}")
    return None

# =========================
# Build (QueryID, type) maps + duplicate diagnostics
# =========================
def get_key(row, fallback_prefix, idx):
    qid = row.get("QueryID") or row.get("id") or f"{fallback_prefix}_{idx}"
    eval_obj = row.get("evaluation_result", row)
    typ = get_eval_type(eval_obj) or "unknown"
    return (str(qid), typ)

def build_key_map(rows, prefix):
    out = {}
    dupes = []
    dup_buckets = defaultdict(list)

    for i, r in enumerate(rows):
        key = get_key(r, prefix, i)
        if key in out:
            dupes.append(key)
            dup_buckets[key].append(r)
            # keep first occurrence by default
            continue
        out[key] = r
        dup_buckets[key].append(r)

    if dupes:
        counts = Counter(dupes)
        print(f"⚠️ Duplicate (QueryID,type) in {prefix}: {dict(counts)} — keeping first occurrence")
        # extra diagnostics: identical vs conflicting duplicates
        identical = 0
        conflicting = 0
        for k, bucket in dup_buckets.items():
            if len(bucket) <= 1:
                continue
            try:
                # compare 'evaluation_result' blobs
                evals = [json.dumps(b.get('evaluation_result', b), sort_keys=True) for b in bucket]
                if len(set(evals)) == 1:
                    identical += 1
                else:
                    conflicting += 1
            except Exception:
                conflicting += 1
        print(f"   ↳ duplicate groups: identical={identical}, conflicting={conflicting}")
    return out

def type_mismatch_report(gt_rows, ev_rows):
    # Show QueryIDs that exist in both files, but with disjoint types.
    gt_qid_to_types = defaultdict(set)
    ev_qid_to_types = defaultdict(set)
    for r in gt_rows:
        q = r.get("QueryID") or r.get("id")
        if q is None: continue
        t = get_eval_type(r.get("evaluation_result", r)) or "unknown"
        gt_qid_to_types[str(q)].add(t)
    for r in ev_rows:
        q = r.get("QueryID") or r.get("id")
        if q is None: continue
        t = get_eval_type(r.get("evaluation_result", r)) or "unknown"
        ev_qid_to_types[str(q)].add(t)

    both_qids = sorted(set(gt_qid_to_types.keys()) & set(ev_qid_to_types.keys()))
    mismatches = []
    for q in both_qids:
        if gt_qid_to_types[q].isdisjoint(ev_qid_to_types[q]):
            mismatches.append((q, sorted(gt_qid_to_types[q]), sorted(ev_qid_to_types[q])))
    if mismatches:
        print(f"ℹ️ QueryIDs present in BOTH files but with NON-overlapping types (showing up to 10):")
        for q, gt_types, ev_types in mismatches[:10]:
            print(f"   - {q}: GT types={gt_types} vs Eval types={ev_types} (no overlap)")
        print(f"   Total type-mismatch QueryIDs (no overlap): {len(mismatches)}")

# =========================
# Main
# =========================
def main():
    # Load files safely
    gt_rows = load_jsonl_safe(GROUND_TRUTH_PATH)
    ev_rows = load_jsonl_safe(EVALUATION_PATH)

    # Report helpful cross-file type mismatches by QueryID
    type_mismatch_report(gt_rows, ev_rows)

    gt_map = build_key_map(gt_rows, "gt")
    ev_map = build_key_map(ev_rows, "ev")

    gt_keys = set(gt_map.keys())
    ev_keys = set(ev_map.keys())

    matched_keys  = sorted(gt_keys & ev_keys)
    unmatched_gt  = sorted(gt_keys - ev_keys)
    unmatched_ev  = sorted(ev_keys - gt_keys)

    print(f"Matched (QueryID,type) entries: {len(matched_keys)}")
    if unmatched_gt: print(f"⚠️ Unmatched GT keys (first 10): {unmatched_gt[:10]}")
    if unmatched_ev: print(f"⚠️ Unmatched Eval keys (first 10): {unmatched_ev[:10]}")

    # Optional Azure (reasoning only on mismatches)
    client = init_azure_client()

    # Models for text similarity
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    rouge = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)

    # Aggregates
    out_rows = []
    field_agreement = defaultdict(list)
    cos_sims, bert_f1s, rouge_ls = [], [], []
    verdicts_gt_all, verdicts_eval_all = [], []

    # Output fig dir next to OUTPUT_PATH
    fig_dir = ensure_dir(os.path.join(os.path.dirname(OUTPUT_PATH), "figures"))

    for (qid, typ) in tqdm(matched_keys, total=len(matched_keys)):
        gt_row = gt_map[(qid, typ)]
        ev_row = ev_map[(qid, typ)]

        gt_eval_raw = gt_row.get("evaluation_result", gt_row)
        ev_eval_raw = ev_row.get("evaluation_result", ev_row)

        gt_eval = normalize_eval_obj(gt_eval_raw)
        ev_eval = normalize_eval_obj(ev_eval_raw)

        # --- Field comparisons
        gt_verdict, ev_verdict = gt_eval["verdict"], ev_eval["verdict"]

        # satisfaction tolerance ±1 for agreement (but exact for κ)
        sat_gt, sat_ev = gt_eval["satisfaction_level"], ev_eval["satisfaction_level"]
        sat_diff = abs(sat_gt - sat_ev) if (sat_gt is not None and sat_ev is not None) else None
        sat_agree = (sat_diff is None) or (sat_diff <= 1)

        # reference usage exact boolean match for agreement
        ref_gt, ref_ev = gt_eval["reference_usage"], ev_eval["reference_usage"]
        ref_agree = (ref_gt is None and ref_ev is None) or (ref_gt == ref_ev)

        verdict_agree = (gt_verdict == ev_verdict)

        # --- Optional GPT reasoning when any key field mismatches
        reason = None
        if USE_GPT_REASONING and (not verdict_agree or not sat_agree or not ref_agree):
            prompt = (
                REASON_PROMPT_TEMPLATE
                .replace("__GT__", json.dumps(gt_eval_raw, ensure_ascii=False, indent=2))
                .replace("__EV__", json.dumps(ev_eval_raw, ensure_ascii=False, indent=2))
            )
            r = call_llm_json(client, prompt, f"{qid}|{typ}")
            if r and isinstance(r, dict):
                reason = str(r.get("reason", ""))[:600]

        # --- Record row
        cmp_result = {
            "verdict_match": verdict_agree,
            "satisfaction_match": sat_agree,
            "reference_match": ref_agree,
            "gt_verdict": gt_verdict,
            "eval_verdict": ev_verdict,
            "mismatch_reasoning_gpt": reason
        }

        # --- Text-type semantic similarity (not word-to-word)
        sim = {}
        if typ == "text":
            gt_text = json.dumps(gt_eval_raw, ensure_ascii=False)
            ev_text = json.dumps(ev_eval_raw, ensure_ascii=False)
            try:
                vecs = embedder.encode([gt_text, ev_text])
                sim["cosine_similarity"] = float(cosine_similarity([vecs[0]], [vecs[1]])[0][0])
                cos_sims.append(sim["cosine_similarity"])
            except Exception as e:
                sim["cosine_similarity_error"] = str(e)

            try:
                _, _, b_f1 = bertscore_score([ev_text], [gt_text], lang="en", verbose=False)
                sim["bertscore_f1"] = float(b_f1[0])
                bert_f1s.append(sim["bertscore_f1"])
            except Exception as e:
                sim["bertscore_error"] = str(e)

            try:
                r = rouge.score(ev_text, gt_text)['rougeL'].fmeasure
                sim["rougeL_f1"] = float(r)
                rouge_ls.append(sim["rougeL_f1"])
            except Exception as e:
                sim["rougeL_error"] = str(e)

        out_rows.append({
            "QueryID": qid,
            "type": typ,
            "ground_truth_eval": gt_eval_raw,
            "evaluator_eval": ev_eval_raw,
            "normalized_gt": gt_eval,
            "normalized_eval": ev_eval,
            "comparison_result": cmp_result,
            "text_similarity": sim if sim else None
        })

        # --- Aggregations for summary
        field_agreement["verdict"].append((gt_verdict, ev_verdict))
        field_agreement["satisfaction_level"].append((sat_gt, sat_ev))
        field_agreement["reference_usage"].append((ref_gt, ref_ev))

        verdicts_gt_all.append(gt_verdict)
        verdicts_eval_all.append(ev_verdict)

    # Write one clean JSONL
    write_jsonl_overwrite(OUTPUT_PATH, out_rows)
    print(f"\n✅ Wrote per-item comparison log to: {OUTPUT_PATH}")

    # ===== Field-level agreement =====
    print("\n📈 === FIELD-LEVEL AGREEMENT ===")
    # verdict
    v_pairs = field_agreement["verdict"]
    v_agree = sum(1 for a, b in v_pairs if verdict_only(a) == verdict_only(b))
    v_perc = 100 * v_agree / len(v_pairs) if v_pairs else 0.0
    v_kappa = cohen_kappa_score([verdict_only(a) for a, _ in v_pairs], [verdict_only(b) for _, b in v_pairs]) if v_pairs else None
    print(f"verdict: {v_perc:.2f}% agreement, κ = {v_kappa:.4f}" if v_kappa is not None else f"verdict: {v_perc:.2f}% agreement, κ = N/A")

    # satisfaction (±1 tolerated for agreement; κ on exact labels)
    s_pairs = field_agreement["satisfaction_level"]
    s_agree = 0; s_total = 0
    s_gt_exact, s_ev_exact = [], []
    for a, b in s_pairs:
        a_n, b_n = norm_sat(a), norm_sat(b)
        if a_n is None or b_n is None:
            continue
        s_total += 1
        if abs(a_n - b_n) <= 1: s_agree += 1
        s_gt_exact.append(a_n); s_ev_exact.append(b_n)
    s_perc = 100 * s_agree / s_total if s_total else 0.0
    s_kappa = cohen_kappa_score(s_gt_exact, s_ev_exact) if s_gt_exact and len(s_gt_exact) == len(s_ev_exact) else None
    print(f"satisfaction_level: {s_perc:.2f}% agreement, κ = {s_kappa:.4f}" if s_kappa is not None else f"satisfaction_level: {s_perc:.2f}% agreement, κ = N/A")

    # reference usage (boolean exact)
    r_pairs = field_agreement["reference_usage"]
    r_agree = 0; r_total = 0
    r_gt_exact, r_ev_exact = [], []
    for a, b in r_pairs:
        a_b, b_b = yesno_bool(a), yesno_bool(b)
        if a_b is None or b_b is None:
            continue
        r_total += 1
        if a_b == b_b: r_agree += 1
        r_gt_exact.append(str(a_b)); r_ev_exact.append(str(b_b))
    r_perc = 100 * r_agree / r_total if r_total else 0.0
    r_kappa = cohen_kappa_score(r_gt_exact, r_ev_exact) if r_gt_exact and len(r_gt_exact) == len(r_ev_exact) else None
    print(f"reference_usage: {r_perc:.2f}% agreement, κ = {r_kappa:.4f}" if r_kappa is not None else f"reference_usage: {r_perc:.2f}% agreement, κ = N/A")

    # ===== Overall verdict accuracy & confusion matrices =====
    print(f"\n🧪 GT verdicts:   {sorted(set(verdicts_gt_all))}")
    print(f"🧪 Eval verdicts: {sorted(set(verdicts_eval_all))}")

    # Filter to PASS/FAIL for binary metrics (exclude REFUSED)
    pf_pairs = [(g, e) for g, e in zip(verdicts_gt_all, verdicts_eval_all) if g in ("PASS","FAIL") and e in ("PASS","FAIL")]
    if pf_pairs:
        y_true_bin = [g for g, _ in pf_pairs]
        y_pred_bin = [e for _, e in pf_pairs]
        cm_bin = confusion_matrix(y_true_bin, y_pred_bin, labels=["PASS","FAIL"])
        print("\n🔍 === CLASSIFICATION REPORT (PASS vs FAIL) ===")
        print(classification_report(y_true_bin, y_pred_bin, labels=["PASS","FAIL"], zero_division=0))
        acc = sum(1 for g, a in pf_pairs if g == a) / len(pf_pairs)
        print(f"✅ Overall Accuracy (PASS/FAIL): {acc:.4f}")

        plt.figure(figsize=(6,5))
        sns.heatmap(cm_bin, annot=True, fmt='d', xticklabels=["PASS","FAIL"], yticklabels=["PASS","FAIL"], cmap='Blues')
        plt.title("Verdict Confusion Matrix (PASS/FAIL)")
        plt.xlabel("Evaluator Verdict")
        plt.ylabel("Ground Truth Verdict")
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, "verdict_confusion_matrix_pass_fail.png"), dpi=SAVE_FIG_DPI)
        plt.close()
    else:
        print("\n⚠️ Not enough PASS/FAIL diversity for binary CM.")

    # 3-class with REFUSED (if present anywhere)
    if INCLUDE_REFUSED_IN_CM and ("REFUSED" in verdicts_gt_all or "REFUSED" in verdicts_eval_all):
        labels3 = ["PASS", "FAIL", "REFUSED"]
        cm3 = confusion_matrix(verdicts_gt_all, verdicts_eval_all, labels=labels3)
        print("\n🔍 === 3-Class CLASSIFICATION REPORT (PASS/FAIL/REFUSED) ===")
        print(classification_report(verdicts_gt_all, verdicts_eval_all, labels=labels3, zero_division=0))

        plt.figure(figsize=(6.5,5.5))
        sns.heatmap(cm3, annot=True, fmt='d', xticklabels=labels3, yticklabels=labels3, cmap='Greens')
        plt.title("Verdict Confusion Matrix (PASS/FAIL/REFUSED)")
        plt.xlabel("Evaluator Verdict")
        plt.ylabel("Ground Truth Verdict")
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, "verdict_confusion_matrix_3class.png"), dpi=SAVE_FIG_DPI)
        plt.close()

    # Optional text similarity summary
    if cos_sims or bert_f1s or rouge_ls:
        print("\n📝 === TEXT SIMILARITY (type == 'text') ===")
        if cos_sims:  print(f"cosine_similarity (mean): {statistics.mean(cos_sims):.4f}")
        if bert_f1s:  print(f"bertscore_f1 (mean):     {statistics.mean(bert_f1s):.4f}")
        if rouge_ls:  print(f"rougeL_f1 (mean):        {statistics.mean(rouge_ls):.4f}")

    # Done
    print("\n🎯 Finished validation.")
    if unmatched_gt:
        print(f"🔎 GT-only (unmatched) count: {len(unmatched_gt)}")
    if unmatched_ev:
        print(f"🔎 Eval-only (unmatched) count: {len(unmatched_ev)}")

if __name__ == "__main__":
    main()
