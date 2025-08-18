import json
import uuid
import os
import random

# ---- INPUT AND OUTPUT PATHS ----
input_path = r"C:\Users\b-fkabir\Downloads\huggingface.json"
output_dir = r"C:\Users\b-fkabir\Desktop\New folder\gorilla\input files"
os.makedirs(output_dir, exist_ok=True)

query_output = os.path.join(output_dir, "t_eval_queries.jsonl")
tool_output = os.path.join(output_dir, "t_eval_tools.jsonl")
gt_output = os.path.join(output_dir, "t_eval_ground_truth.jsonl")

# ---- INDUSTRY FILTER (optional) ----
allowed_keywords = ["finance", "crypto", "stock", "investment", "market", "ethereum", "currency"]

# ---- HELPERS ----
def safe_json_load(x):
    try:
        return json.loads(x) if isinstance(x, str) else x
    except:
        return None

def save_jsonl(path, data):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

# ---- LOAD RAW DATA ----
with open(input_path, "r", encoding="utf-8") as f:
    full_data = json.load(f)

query_set = []
tool_set = []
gt_set = []
tool_map = {}
used_ids = set()

# ---- SHUFFLE + FILTER ----
random.shuffle(full_data)
count = 0

for entry in full_data:
    query = entry.get("query", "").strip()
    answers = safe_json_load(entry.get("answers"))
    tools = safe_json_load(entry.get("tools"))

    if not query or not answers or not tools:
        continue

    # Filter by keyword (optional)
    if not any(k in query.lower() for k in allowed_keywords):
        continue

    # Collect valid tool calls with >=2 arguments
    valid_tool_calls = []
    for ans in answers:
        args = ans.get("arguments", {})
        if isinstance(args, dict) and len(args) >= 2:
            valid_tool_calls.append({
                "type": "function",
                "function": {
                    "name": ans.get("name"),
                    "arguments": args
                },
                "tool_id": f"gt_{ans.get('name')}"
            })

    if not valid_tool_calls:
        continue

    # Assign ID
    query_id = f"hf_{uuid.uuid4().hex[:8]}"
    if query_id in used_ids:
        continue
    used_ids.add(query_id)

    # Save query
    query_set.append({"QueryID": query_id, "query": query})

    # Save tools (unique)
    for tool in tools:
        name = tool.get("name")
        if name and name not in tool_map:
            tool_map[name] = True
            tool_set.append({
                "Tool": [ {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                }],
                "IndustryName": "HuggingFace",
                "IndustryID": "hf",
                "FunctionName": name,
                "FunctionID": name,
                "Mock_Function": f"mock_{name}()",
                "Query": f"Use {name} for a query."
            })

    # Save grouped ground truth
    gt_set.append({
        "QueryID": query_id,
        "query": query,
        "agent_output_label": {
            "tool_call": valid_tool_calls
        }
    })

    count += 1
    if count >= 200:
        break

# ---- SAVE ----
save_jsonl(query_output, query_set)
save_jsonl(tool_output, tool_set)
save_jsonl(gt_output, gt_set)

print(f"✅ Saved {len(query_set)} queries")
print(f"✅ Saved {len(tool_set)} tools")
print(f"✅ Saved {len(gt_set)} ground truth entries (grouped multi-tools)")
