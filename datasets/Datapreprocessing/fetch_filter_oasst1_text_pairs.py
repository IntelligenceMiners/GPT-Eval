from datasets import load_dataset
import json
import uuid

# Path to save final dataset
output_path = r"C:\Users\b-fkabir\Desktop\New folder\gorilla\data\oasst1_text_groundtruth_cleaned.jsonl"

# Load the OASST1 dataset (train split)
dataset = load_dataset("OpenAssistant/oasst1", split="train")

# Build ID-to-text mapping for threading
id_to_text = {ex["message_id"]: ex["text"] for ex in dataset}

# Simple relevance filter (optional but improves quality)
def is_relevant_pair(query, answer):
    query = query.lower()
    answer = answer.lower()
    keywords = ["what", "why", "how", "explain", "describe", "tell", "define"]
    return any(kw in query and kw in answer for kw in keywords)

# Extract clean user–assistant pairs with unique queries
filtered = []
seen_queries = set()

for example in dataset:
    if (
        example["role"] == "assistant"
        and example["lang"] == "en"
        and (example.get("rank") is None or example["rank"] >= 3)
    ):
        parent_id = example.get("parent_id")
        if parent_id and parent_id in id_to_text:
            user_text = id_to_text[parent_id].strip()
            assistant_text = example["text"].strip()

            if (
                user_text
                and assistant_text
                and is_relevant_pair(user_text, assistant_text)
                and user_text not in seen_queries
            ):
                seen_queries.add(user_text)
                filtered.append({
                    "QueryID": f"oasst_{str(uuid.uuid4())[:8]}",
                    "query": user_text,
                    "agent_output_label": assistant_text
                })

    if len(filtered) >= 200:
        break

# Save the filtered dataset
with open(output_path, "w", encoding="utf-8") as f:
    for entry in filtered:
        json.dump(entry, f, ensure_ascii=False)
        f.write("\n")

print(f"✅ Saved {len(filtered)} clean UNIQUE examples to: {output_path}")
