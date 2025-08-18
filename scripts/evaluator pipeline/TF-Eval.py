from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import logging
import os
import json
import statistics
import uuid
import time
from langchain.agents import Tool

# Initialize Azure OpenAI Service client with Entra ID authentication
endpoint = os.getenv("ENDPOINT_URL", "https://aoai-l-swedencentral.openai.azure.com/")
deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o-2024-08-06-global")

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)

client = AzureOpenAI(
    azure_endpoint=endpoint,
    azure_ad_token_provider=token_provider,
    api_version="2024-08-01-preview",
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_jsonl_line(path: str, data: dict):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def load_jsonl(file_path):
    """Reads a JSONL file and returns a list of dictionaries."""
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return []

    data = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                entry = json.loads(line.strip())
                if 'Tool' in entry:
                    data.append(entry['Tool'])
                else:
                    data.append(entry)
        return data
    except Exception as e:
        print(f"Error loading JSONL file: {e}")
        return []

#query_dataset_path = r"C:\Users\b-tislam\tonny python\thesisFinal\output_openai_format2.jsonl"

#query_dataset_path = r"C:\Users\b-tislam\tonny python\thesisFinal\Final_GPT_Judge\modifiedLatest\testDatasets\Toolexcute1.jsonl"
query_dataset_path = r"C:\Users\b-tislam\tonny python\thesisFinal\Final_GPT_Judge\modifiedLatest\testDatasets\Agent Final outputs\Model4.1.jsonl"
#output_jsonl_path = r"C:\Users\b-fkabir\Desktop\New folder\gorilla\Output Files2\processed_resultstext.jsonl"
output_jsonl_path = r"C:\Users\b-tislam\tonny python\thesisFinal\Final_GPT_Judge\modifiedLatest\outputs\processed_resultstools.jsonl"
tool_path = r"C:\Users\b-tislam\tonny python\thesisFinal\Final_GPT_Judge\modifiedLatest\filtered_tools_non_empty_queries.jsonl"
output_tool_path = output_jsonl_path.replace(".jsonl", "_tool.jsonl")
output_text_path = output_jsonl_path.replace(".jsonl", "_text.jsonl")

# Optional: Clear previous content
open(output_tool_path, 'w').close()
open(output_text_path, 'w').close()

query_data = load_jsonl(query_dataset_path)
print(f"Loaded {len(query_data)} queries ")

def detect_response_type(agent_output, history):
    if isinstance(agent_output, dict):
        if "tool_call" in agent_output or "function" in agent_output:
            return "tool"
        if any("tool_call" in turn.get("role", "") or "tool" in turn.get("role", "") for turn in history):
            return "text/tool"
        return "text"
    elif isinstance(agent_output, str):
        if any("tool_call" in turn.get("role", "") or "tool" in turn.get("role", "") for turn in history):
            return "text/tool"
        return "text"
    return "unknown"

def load_tools(jsonl_path: str):
    tools, param_map, tool_dict, required_map, tool_schemas, tool_ids = [], {}, {}, {}, [], {}

    with open(jsonl_path, 'r') as f:
        for line in f:
            obj = json.loads(line.strip())
            tool_data_list = obj.get("Tool", [])
            for tool_data in tool_data_list:
                func = tool_data["function"]
                name = func["name"]
                desc = func.get("description", "")
                parameters = func.get("parameters", {})
                

                # ✅ Fix schema if missing 'properties' 
                if "properties" not in parameters:
                    logger.warning(f"Fixing tool '{name}' with flattened parameters.")
                    parameters = {
                        "type": "object",
                        "properties": parameters
                    }

                tools.append({
                        "name": name,
                        "description": desc,
                        "parameters": parameters
                    })

        print(f"Loaded {len(tools)} tools")

    return tools

def make_tool_fn(name, desc):
    def fn(input_data):
        prompt = f"Tool: {name}\nDescription: {desc}\nInputs: {json.dumps(input_data)}\nReturn only a realistic JSON result. No explanation."
        try:
            response = client.invoke(prompt).content.strip()
            if response.startswith("```json"):
                response = response.split("```json")[-1].split("```")[0].strip()
            return json.loads(response)
        except Exception as e:
            return {"error": f"Tool failed: {str(e)}"}
    return fn
structured_response_tool={
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "evaluator_output_schema",
      "strict": True,
      "schema": {
        "type": "object",
        "properties": {
          "explanation": {
            "type": "string",
            "description": "A concise human-style explanation of the evaluation result, highlighting correctness or failure."
          },
          "type": {
            "type": "string",
            "enum": ["tool", "text", "text/tool"],
            "description": "The type of response used by the agent: tool call, text, or both."
          },
          "tool_call_validity": {
            "type": "string",
            "enum": ["Valid", "Unnecessary", "RequiredButMissing"],
            "description": "Whether using a tool was necessary and justified for the task. 'Valid' = correct use of tool; 'Unnecessary' = tool used when text was better; 'RequiredButMissing' = tool should have been used but wasn't."
          },
          "matched_parameters": {
            "type": "array",
            "items": { "type": "string" },
            "description": "List of parameter keys that were accurately provided in the agent's tool call."
          },
          "critical_mismatches": {
            "type": "array",
            "items": { "type": "string" },
            "description": "List of parameters that were missing or incorrect in a way that critically affects task completion."
          },
          "excluded_parameters": {
            "type": "array",
            "items": { "type": "string" },
            "description": "List of parameters that were part of the schema but not needed or referenced for this specific query."
          },
          "tool_usage": {
            "type": "object",
            "properties": {
              "tools_expected": {
                "type": "array",
                "items": { "type": "string" },
                "description": "List of tools that are logically expected to be used based on the query."
              },
              "tools_used": {
                "type": "array",
                "items": { "type": "string" },
                "description": "List of tools actually used by the agent in the tool call."
              },
              "redundant_tools": {
                "type": "array",
                "items": { "type": "string" },
                "description": "Tools that were used but unnecessary for the given task."
              },
              
            },
            "required": ["tools_expected", "tools_used", "redundant_tools"],
            "additionalProperties": False
          },
          "verdict": {
            "type": "string",
            "enum": ["PASS", "FAIL"],
            "description": "Final decision about the correctness of the tool call output."
          },

        },
        "required": [
          "explanation",
          "type",
          "matched_parameters",
          "critical_mismatches",
          "excluded_parameters",
          "tool_usage",
          "verdict",
          "tool_call_validity"
        ],
        "additionalProperties": False
      }
    }
  }
}
structured_response_text={
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "text_response_evaluation_schema",
      "strict": True,
      "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
          "explanation": {
            "type": "string",
            "description": "Summarizes the overall evaluation in 1–3 sentences."
          },
          "validation_of_result": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "source_verification": { "type": "boolean" },
              "consistency_with_previous_responses": { "type": "boolean" },
              "alignment_with_user_feedback": { "type": "boolean" }
            },
            "required": [
              "source_verification",
              "consistency_with_previous_responses",
              "alignment_with_user_feedback"
            ]
          },
          "evaluation_summary": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "completeness": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "is_complete": { "type": "boolean" },
                  "missing_elements": {
                    "type": "array",
                    "items": { "type": "string" }
                  }
                },
                "required": ["is_complete", "missing_elements"]
              },
              "relevance": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "is_relevant": { "type": "boolean" },
                  "irrelevant_details": {
                    "type": "array",
                    "items": { "type": "string"}
                  }
                },
                "required": ["is_relevant", "irrelevant_details"]
              },
              "clarity": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "is_clear": { "type": "boolean" },
                  "issues": {
                    "type": "array",
                    "items": { "type": "string"}
                  }
                },
                "required": ["is_clear", "issues"]
              },
              "accuracy": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "is_accurate": { "type": "boolean" },
                  "inaccuracies": {
                    "type": "array",
                    "items": { "type": "string" }
                  }
                },
                "required": ["is_accurate", "inaccuracies"]
              },
              "engagement": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "is_engaging": { "type": "boolean" },
                  "suggestions": {
                    "type": "array",
                    "items": { "type": "string" }
                  }
                },
                "required": ["is_engaging", "suggestions"]
              }
            },
            "required": [
              "completeness",
              "relevance",
              "clarity",
              "accuracy",
              "engagement"
            ]
          },
          "contextual_adaptation": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "use_of_real_time_data": { "type": "boolean" },
              "adaptation_to_context": { "type": "boolean" }
            },
            "required": ["use_of_real_time_data", "adaptation_to_context"]
          },
          "user_feedback": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "user_satisfaction": {
                "type": "string",
                "enum": ["low", "medium", "high"]
              },
              "feedback_comments": {
                "type": "array",
                "items": { "type": "string" }
              }
            },
            "required": ["user_satisfaction", "feedback_comments"]
          },
          "reference_usage": {
            "type": "string",
            "enum": ["Yes", "No", "N/A"],
            "description": "Indicates whether reference materials were used, unused, or not applicable in the assistant's response. Use 'Yes' if the assistant explicitly mentions, links to, or cites external sources (e.g., official websites, reports, databases). Also, mark 'Yes' if the assistant includes external links (e.g., to websites like FIFA.com), references official sources, or uses citation-like expressions. Use 'No' if reference materials were available but not referenced. Use 'N/A' only if no reference materials were needed or relevant for the task."
          },
          "overall_verdict": {
            "type": "string",
            "enum": ["PASS", "FAIL"],
            "description": "Final decision on whether the response meets the task requirements."
          },
          "additional_notes": {
            "type": "string",
            "description": "Optional extra observations or clarifications by the evaluator."
          }
        },
        "required": [
          "explanation",
          "validation_of_result",
          "evaluation_summary",
          "contextual_adaptation",
          "user_feedback",
          "overall_verdict",
          "additional_notes",
          "reference_usage"
        ]
      }
    }
  }
}

META_PROMPT = """
Act as an evaluation engine that reviews an assistant’s performance, which is responsible for assessing whether an AI assistant correctly understood a user's query and responded by selecting the appropriate tool, supplying accurate parameters, and avoiding unnecessary tool calls.
You will be given a natural language query, a list of all available tools (including their descriptions and schemas), and the actual tool call made by the assistant. Your job is to determine whether the tool selection and argument
usage were appropriate for the task, and to provide a structured judgment that includes a breakdown of matched parameters, critical mismatches, tool usage behavior, and an overall verdict (PASS or FAIL).An evaluation may be considered a PASS when all necessary tools were used correctly, and no unrelated tools were invoked.

You will be given the following information:

## User Query
_last_query: {query}  #The user qquery  that may be either single-turn or multi-turn interactions. Each query is intended to trigger the use of a specific tool from a predefined set of available tools designed for domain-specific tasks

## Available Tools (Full Schema)
{tools}  # These tools follow a structured format compliant with OpenAI function-calling standards and include elements such as a name, a detailed description, a mock function for simulation, a sample query, and a well-defined parameter schema

## Conversation History
{history}  # In addition to the _last_query query, the dataset also contains multi-turn conversations where the user’s intent is distributed across several exchanges. In such cases, evaluating tool-calling behavior requires understanding the full conversation 
history to reconstruct the complete context. The agent must effectively track and resolve parameters over multiple user inputs and assistant clarifications. This includes carrying forward relevant information, resolving ambiguities, and filling in implicit details as the dialogue progresses.

## Tool Call Made by Agent
{agent_output_label}  # The agent's response should include selecting the appropriate tool, populating its parameters based on the query, and optionally executing the tool to return an outpu

---

## Evaluation Criteria and guidelines

1. **Explaination**
   The explanation field should clearly articulate why the task was considered successfully completed. Specifically, explain that the agent:
    - Selected the correct tool that best aligns with the user's intent based on the domain and task requirements.
    -Accurately extracted and passed relevant parameters from the user query (and conversation history if multi-turn), ensuring that all critical information was captured and formatted correctly
    -Avoided unnecessary tool calls, invoking only the tools needed to fulfill the task efficiently, without redundant or excessive interactions.
    -Clearly justify whether invoking the tool at all was necessary.
2. **Tool Call Validity**
   - Evaluate whether using a tool call in this case was *necessary*, *efficient*, and *user-friendly*.
   - Sometimes, the task does not require structured computation or action. In such cases, a well-formed text answer would have been more appropriate and natural.
   - The evaluator should ask:
     - Could the assistant have simply responded  with a helpful natural language answer when tool usage wasn’t essential?
     - Did the tool call add value, or did it overcomplicate a task that could be done in plain language?
   - If the agent called a tool **just for the sake of using one**, and it wasn’t needed, this should be flagged.
   - This includes examples like:
     - Asking for a general explanation or advice
     - Conversational or non-actionable requests
     - Requests that do not require parameters or structured output

   -classify the tool call as:

    Valid: Tool use was justified and required.
    Unnecessary : The tool call could have been avoided; text would have sufficed.
    RequiredButMissing : A tool should have been used, but was not.

   - Even if the tool call was correct, The outcome may be marked as a failure in cases where if:
                    - Additional tools were called that were unnecessary
                    - The evaluator marks more than one `"tools_expected"` without distinct sub-tasks in the query


2. **Matched Parameters**
   - Normalize and flatten parameter structures (e.g., `a.b.c=value`).
   - Compare relevant parameters with expected keys.
   - Allow semantic or alias-based equivalence for parameters (e.g., 'SPX' and 'SPX:INDEXSP' are equivalent).
   - Minor formatting differences (prefixes, casing, abbreviations) should not be penalized as mismatches.


3. **Critical Mismatches**
   List parameters that were explicitly required or clearly implied in the user query but were:

   -Omitted (missing from the tool call),
   - Misaligned (included but with incorrect values), or
   - Incorrectly interpreted (semantically misunderstood)

4. **Excluded Parameters**
   - Parameters that are part of the schema but not needed for this specific query.

5. **Tool Usage Evaluation**
- Only include tools in `"tools_expected"` if they are **clearly required** to fulfill a distinct part of the user query.
- Do **not** include tools just because they are similar or offer overlapping data.
- Try not to assume multiple tools are needed unless the query explicitly asks for more than one task.
- Define:
  - `"tools_expected"` → Tools **Clearly required** for fulfilling the users query (one per clear sub-task)
  - `"tools_used"` → Tools the assistant actually called
  - `"redundant_tools"` → Tools that were called by the agent but were **not needed** for the query (indicate these even if they are partially related)
- Note if any **unnecessary tools** were used as `"redundant_tools"` if:
  - The tool's output was not clearly demanded by the user
  - The tool does not directly support the task
  - Its purpose is tangential or overlapping with another tool

6. **Explanation**
   - Write a short explanation (1–3 sentences) summarizing the outcome.
   - Clearly state whether the agent chose the correct tool, passed the required arguments, and avoided unnecessary tool calls.
   - Examples:
     - `"The agent selected the correct tool, provided accurate parameters, and used only necessary tool calls to fulfill the task."`
     - `"The agent chose the wrong tool and missed a critical parameter required to perform the task, resulting in a failure."`
7. **Reference Usage**
   - Check if the agent's response or tool call included or relied on any **reference materials**, documentation, prior knowledge, citations, or external sources.
   - Classify as:
     - Reference: Yes → If references are available regarding the query and meaningfully used to support the result.
     - Reference: No → If references are available regarding the query but not applied or integrated into the answer/tool logic.
     - Reference: N/A → If no references were involved or necessary.

8. **Final Verdict**
   - PASS → If the agent selected the correct tool, used correct parameters, and avoided confusion.
   - FAIL → If a required parameter is missing or wrong, or if the wrong tool was selected.

## Required Output Format: Please provide your answer in the specified JSON format..

""".strip()

META_PROMPT_TEXT = """
You are an intelligent evaluator tasked with assessing whether an AI assistant’s free-text response (not a tool call) effectively satisfies the user's intent based on clarity, completeness, accuracy, and relevance.

You will be given:

## User Query
{query}  #The user queries that may be either single-turn or multi-turn interactions. Each query is intended to trigger the use of a specific tool from a predefined set of available tools designed for domain-specific tasks

## Available Tools 
{tools}  # These tools follow a structured format compliant with OpenAI function-calling standards and include elements such as a name, a detailed description, a mock function for simulation, a sample query, and a well-defined parameter schema

## Conversation History
{history}  # In addition to single-turn queries, the dataset also contains multi-turn conversations where the user’s intent is distributed across several exchanges. In such cases, evaluating tool-calling behavior requires understanding the full conversation 
history to reconstruct the complete context. The agent must effectively track and resolve parameters over multiple user inputs and assistant clarifications. This includes carrying forward relevant information, resolving ambiguities, and filling in implicit details as the dialogue progresses.

## Tool Call Made by Agent
{agent_output_label}  # The `{agent_output_label}` contains the AI assistant’s response to the user query. In this evaluation scenario, the response is a **free-form text message**, not a structured tool call.

Your task is to evaluate if the assistant’s **textual response alone** was appropriate, sufficient, and helpful. The expected output format is a JSON object, following the structure below.

## Evaluation Criteria

### 1.Completeness
- Did the response address **all elements** of the user's request?
- Was anything **missing or partially addressed**?
- List missing elements if applicable.

### 2.Relevance
- Is the entire response **on-topic** and appropriate for the query?
- Flag any **off-topic, redundant, or unnecessary** information.

### 3.Clarity
- Is the response **easy to understand**, well-structured, and free from ambiguity?
- List any issues (e.g., overly technical, vague, or poorly phrased sections).

### 4. Accuracy
- Is the content **factually correct and contextually valid**?
- List specific inaccuracies if any are found.

### 5.Engagement
- Was the response **helpful, polite, and user-friendly**?
- Suggest improvements to tone or delivery if needed.

### 6.Validation of Results
Evaluate whether the assistant’s response aligns with expectations:
- `source_verification`: Did it appear grounded in reliable or plausible knowledge?
- `consistency_with_previous_responses`: Does it match prior assistant behavior?
- `alignment_with_user_feedback`: Would a user likely find it acceptable?

### 7.Contextual Adaptation
- Did the assistant use prior conversation turns to tailor the response?
- Was real-time context (e.g., location, time, user profile) reasonably reflected?

### 8. User Feedback (Simulated)
- Estimate the **user satisfaction** as `high`, `medium`, or `low`.
- Provide 1–2 simulated user comments (positive or critical).

### 9. **Reference Usage**
   - Check if the agent's response or tool call included or relied on any **reference materials**, documentation, prior knowledge, citations, or external sources.
   - Categorize  as:
     - Reference: Yes → If references are available regarding the query and meaningfully used to support the result.
     - Reference: No → If references are available regarding the query but not applied or integrated into the answer/tool logic.
     - Reference: N/A → If no references were involved or necessary.

### 10.Final Verdict
Pay particular attention to the following points :
Review the Available Tools section.

If any tool is explicitly capable of handling the user’s request, mark the text-only response as "FAIL", even if the text appears correct, complete, or helpful.

The assistant must prefer tool usage when an appropriate tool exists to ensure structured, traceable, and standardized execution.

Only "PASS" the text response if:

No suitable tool exists,

Or, the user explicitly rejects tool usage (e.g., "I just need a quick summary, no booking needed").
So, 
- `"PASS"` → if the response is complete, accurate, satisfying and no applicable tool was skipped
- `"FAIL"` → if :
  - Critical content is missing, inaccurate, or misleading,
  - **OR** the assistant skipped using an available tool that could have handled the query more appropriately.
- `"PartiallyComplete"` → if it’s mostly okay but not fully aligned with expectations.

## Required Output Format: Please use the provided response format. Keep your response concise and focused on the requested format.

""".strip()

def process_query_with_toolCall(query, tools, history, agent_output_label, task_or_prompt: str):
    response_type = detect_response_type(agent_output_label, history)
    if response_type in ["tool", "text/tool"]:
        formatted_prompt = META_PROMPT.format(
            query=query,
            tools=json.dumps(tools, indent=2),
            history=json.dumps(history, indent=2),
            agent_output_label=json.dumps(agent_output_label, indent=2)
        )
        response_schema = structured_response_tool["response_format"]
    else:
        formatted_prompt = META_PROMPT_TEXT.format(
            query=query,
            tools=json.dumps(tools, indent=2),
            history=json.dumps(history, indent=2),
            agent_output_label=json.dumps(agent_output_label, indent=2)
        )
        response_schema = structured_response_text["response_format"]
    time.sleep(3)
    completion = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": formatted_prompt},
            {"role": "user",  "content": "Task, Goal, or Current Prompt:\n" + task_or_prompt},
        ],
        response_format=response_schema
    )
    #print("Response:", completion.choices[0].message.content)
    return completion.choices[0].message.content

def evaluate_label(result_data):
    
    if result_data.get("type") in ["tool", "text/tool"]:
        score = 0
        if result_data.get("verdict") == "PASS":
            score += 1
        if result_data.get("tool_call_validity") == "Valid":
            score += 1
        if not result_data.get("critical_mismatches"):
            score += 1
        if result_data.get("matched_parameters"):
            score += 1
        usage = result_data.get("tool_usage", {})
        if usage.get("tools_expected") == usage.get("tools_used"):
            score += 1
        if not usage.get("redundant_tools"):
            score += 1
        if result_data.get("satisfaction_level") == "Excellent":
            score += 1

        if score >= 6:
            label = "Excellent"
        elif score >= 4:
            label = "Good"
        elif score >= 2:
            label = "Fair"
        else:
            label = "Poor"
        return score, label

    summary = result_data.get("evaluation_summary", {})
    adaptation = result_data.get("contextual_adaptation", {})

    metrics = {
        "completeness": summary.get("completeness", {}).get("is_complete", False),
        "relevance": summary.get("relevance", {}).get("is_relevant", False),
        "accuracy": summary.get("accuracy", {}).get("is_accurate", False),
        "clarity": summary.get("clarity", {}).get("is_clear", False),
        "engagement": summary.get("engagement", {}).get("is_engaging", False),
        "adaptation": adaptation.get("adaptation_to_context", False),
        "real_time": adaptation.get("use_of_real_time_data", False)
    }

    score = sum(metrics.values())
    if score >= 6:
        label = "Excellent"
    elif score >= 4:
        label = "Good"
    elif score >= 2:
        label = "Fair"
    else:
        label = "Poor"
    return score, label


def generate_aggregate_statistics(jsonl_path, label="ALL"):
    scores = []
    pass_count = 0
    fail_count = 0
    total = 0

    pass_path = jsonl_path.replace(".jsonl", "_pass.jsonl")
    fail_path = jsonl_path.replace(".jsonl", "_fail.jsonl")

    # Clear previous content
    with open(pass_path, "w", encoding="utf-8") as pf, open(fail_path, "w", encoding="utf-8") as ff:
        pass

    with open(jsonl_path, "r", encoding="utf-8") as file:
        for line in file:
            try:
                entry = json.loads(line.strip())
                eval_data = entry.get("evaluation_result", {})
                score = eval_data.get("satisfaction_score", None)
                verdict = eval_data.get("verdict") or eval_data.get("overall_verdict")

                if verdict == "PASS":
                    pass_count += 1
                    write_jsonl_line(pass_path, entry)
                elif verdict == "FAIL":
                    fail_count += 1
                    write_jsonl_line(fail_path, entry)

                if score is not None:
                    scores.append(score)

                total += 1
            except Exception as e:
                print(f"Skipping malformed line: {e}")
                continue

    pass_percent = (pass_count / total) * 100 if total else 0
    fail_percent = (fail_count / total) * 100 if total else 0

    print(f"\n📊 EVALUATION STATS FOR {label.upper()} RESPONSES")
    print(f"Total Evaluated: {total}")
    print(f"✅ PASS: {pass_count} ({pass_percent:.2f}%)")
    print(f"❌ FAIL: {fail_count} ({fail_percent:.2f}%)")

    if scores:
        print(f"⭐ Average Score: {sum(scores)/len(scores):.2f}")
        print(f"📉 Min Score: {min(scores)}")
        print(f"📈 Max Score: {max(scores)}")
        print(f"📊 Median Score: {statistics.median(scores)}")
    else:
        print("No valid satisfaction scores found.")


if __name__ == "__main__":
    tools_data = load_tools(tool_path)
    print(f" **********************************Loaded {len(tools_data)} tools")

    for query_entry in query_data:
        query_id = str(query_entry["QueryID"])
        query_text = query_entry["query"]
        #tools = query_entry["tools"]
        history = query_entry["history"]
        agent_output = query_entry["agent_output_label"]
        response_type = detect_response_type(agent_output, history)
        print(f"Response Type: {response_type}")
        task = f"Given the {query_text}, and {history}, evaluate the agent's response."

        result = process_query_with_toolCall(query_text,tools_data, history, agent_output, task)

        try:
            result_data = json.loads(result)
            satisfaction_score, satisfaction_label = evaluate_label(result_data)
            result_data["satisfaction_score"] = satisfaction_score
            result_data["satisfaction_level"] = satisfaction_label

            # Determine verdict key
            verdict_key = "verdict" if "verdict" in result_data else "overall_verdict" if "overall_verdict" in result_data else None

            # Extract tool usage info
            tools_expected = result_data.get("tool_usage", {}).get("tools_expected", [])
            tools_used = result_data.get("tool_usage", {}).get("tools_used", [])
            redundant_tools = result_data.get("tool_usage", {}).get("redundant_tools", [])

            # Explicit FAIL override for redundant tools
            if verdict_key and redundant_tools:
                result_data[verdict_key] = "FAIL"

            # Upgrade to PASS if score is Good or Excellent and no redundant tools
            elif verdict_key and satisfaction_label in ["Good", "Excellent"]:
                result_data[verdict_key] = "PASS"

            # Final output entry
            output_entry = {
                "QueryID": query_id,
                "query": query_text,
                "history": history,
                "agent_output_label": agent_output,
                "evaluation_result": result_data
            }

            # Write to main file
            write_jsonl_line(output_jsonl_path, output_entry)

            # Write to type-specific file
            if response_type == "tool":
                write_jsonl_line(output_tool_path, output_entry)
            elif response_type == "text":
                write_jsonl_line(output_text_path, output_entry)

        except Exception as e:
            print(f"Failed to parse/store evaluation result for QueryID {query_id}: {e}")

    # After loop finishes
    print("\n📊 OVERALL STATS:")
    generate_aggregate_statistics(output_jsonl_path, label="all")

    print("\n🛠 TOOL RESPONSES:")
    generate_aggregate_statistics(output_tool_path, label="tool")

    print("\n💬 TEXT RESPONSES:")
    generate_aggregate_statistics(output_text_path, label="text")
