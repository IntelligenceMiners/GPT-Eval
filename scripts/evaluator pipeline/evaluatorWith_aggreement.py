import json
from collections import defaultdict, Counter

input_path = r"C:\Users\b-tislam\tonny python\thesisFinal\Final_GPT_Judge\modifiedLatest\testDatasets\multiAgreement\modelbased_evaluatedMA_data\evaluatedMA_data4.1Nano.jsonl"
output_path = input_path.replace(".jsonl", "_with_consistency_optimized.jsonl")


grouped_data = defaultdict(lambda: {
    "final_entry": None,
    "final_history_len": -1,
    "intermediate_verdicts": []
})

# Reliability stat tracker
reliability_counter = Counter()


with open(input_path, "r", encoding="utf-8") as f:
    
    for line in f:
        entry = json.loads(line.strip())
        query_id = entry["QueryID"]
        history_len = len(entry.get("history", []))
        eval_result = entry.get("evaluation_result", {})
        verdict = eval_result.get("verdict") or eval_result.get("overall_verdict") or "UNKNOWN"

        group = grouped_data[query_id]

        if history_len > group["final_history_len"]:
            # Current entry is a new candidate for final step
            if group["final_entry"]:
                # Save previous final candidate verdict into intermediate
                prev_final = group["final_entry"]
                prev_verdict = prev_final["evaluation_result"].get("verdict") or prev_final["evaluation_result"].get("overall_verdict") or "UNKNOWN"
                group["intermediate_verdicts"].append(prev_verdict)

            group["final_entry"] = entry
            group["final_history_len"] = history_len
        else:
            group["intermediate_verdicts"].append(verdict)

# Write results with consistency block
multi_turn_count = 0
with open(output_path, "w", encoding="utf-8") as f:
    
    for query_id, data in grouped_data.items():
        final_entry = data["final_entry"]
        intermediate_verdicts = data["intermediate_verdicts"]
        if not intermediate_verdicts:
            continue  # Skip single-turn queries
        multi_turn_count += 1
        final_verdict = final_entry["evaluation_result"].get("verdict") or \
                        final_entry["evaluation_result"].get("overall_verdict")
        
        consistency = "N/A"
        reliability = "N/A"

        if final_verdict == "PASS":
            if any(v != "PASS" for v in intermediate_verdicts):
                consistency = "INCONSISTENT"
                reliability = "UNRELIABLE_FINAL_ONLY_EVALUATION"
            else:
                consistency = "CONSISTENT"
                reliability = "RELIABLE_FINAL_ONLY_EVALUATION"

        elif final_verdict == "FAIL":
            
            if intermediate_verdicts and all(v == "FAIL" for v in intermediate_verdicts):
                consistency = "CONSISTENT"
                reliability = "RELIABLE_FINAL_ONLY_EVALUATION"
            elif intermediate_verdicts and all(v == "PASS" for v in intermediate_verdicts):
                consistency = "REGRESSION"
                reliability = "UNRELIABLE_REGRESSION"
            else:
                consistency = "N/A"
                reliability = "N/A"

        # Count for statistics
        reliability_counter[reliability] += 1
        # Attach consistency block
        consistency_block = {
            "QueryID": query_id,
            "multiturn_consistency": {
                "is_multiturn": len(intermediate_verdicts) > 0,
                "intermediate_step_verdicts": intermediate_verdicts,
                "final_verdict": final_verdict,
                "consistency_label": consistency,
                "reliability": reliability
            }
        }

        # Include extra metadata optionally
        consistency_block["satisfaction_level"] = final_entry["evaluation_result"].get("satisfaction_level")
        consistency_block["satisfaction_score"] = final_entry["evaluation_result"].get("satisfaction_score")
        consistency_block["query"] = final_entry.get("query")
        consistency_block["history_length"] = len(final_entry.get("history", []))

        # Save to new file
        f.write(json.dumps(consistency_block, ensure_ascii=False) + "\n")

print(f"✅ Output saved to: {output_path}")

# --- STEP 3: Print Statistics ---
print(f"\n🔢 Total Multi-Turn Queries Processed: {multi_turn_count}")
print("\n📊 Multi-Turn Evaluation Reliability Summary:")
total = sum(reliability_counter.values())
for k, v in reliability_counter.items():
    pct = (v / total) * 100
    print(f"  {k}: {v} ({pct:.2f}%)")
print("\n✅ Evaluation completed successfully!")
