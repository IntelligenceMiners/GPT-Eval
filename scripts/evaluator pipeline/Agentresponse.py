import os
import json
import logging
import asyncio
import uuid
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain_openai import AzureChatOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from collections import Counter
import re
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
endpoint = os.getenv("ENDPOINT_URL", "https://aoai-l-swedencentral.openai.azure.com/")
deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o-2024-08-06-global")
api_version = "2024-06-01"

# Azure OpenAI auth
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)

# LLM Setup
llm = AzureChatOpenAI(
    azure_endpoint=endpoint,
    azure_ad_token_provider=token_provider,
    deployment_name=deployment,
    openai_api_version=api_version,
    temperature=0.2
)

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

                #  Fix schema if missing 'properties' 
                if "properties" not in parameters:
                    logger.warning(f"Fixing tool '{name}' with flattened parameters.")
                    parameters = {
                        "type": "object",
                        "properties": parameters
                    }

                props = parameters["properties"]
                required = parameters.get("required", list(props.keys()))  # Default: all required

                tool_id = str(uuid.uuid4())
                tool_schemas.append({
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": desc,
                        "parameters": parameters
                    },
                    "tool_id": tool_id
                })

                tool = Tool(name=name, func=make_tool_fn(name, desc), description=desc, return_direct=True)
                tools.append(tool)

                param_map[name] = list(props.keys())
                required_map[name] = required
                tool_dict[name] = tool
                tool_ids[name] = tool_id

    return tools, param_map, tool_dict, required_map, tool_schemas, tool_ids


def make_tool_fn(name, desc):
    def fn(input_data):
        prompt = f"Tool: {name}\nDescription: {desc}\nInputs: {json.dumps(input_data)}\nReturn only a realistic JSON result. No explanation."
        try:
            response = llm.invoke(prompt).content.strip()
            if response.startswith("```json"):
                response = response.split("```json")[-1].split("```")[0].strip()
            return json.loads(response)
        except Exception as e:
            return {"error": f"Tool failed: {str(e)}"}
    return fn

def parse_json_content(content: str):
    try:
        if content.startswith("```json"):
            content = content.split("```json")[-1].split("```")[0].strip()
        return json.loads(content)
    except Exception:
        return None

def write_jsonl_line(path: str, data: dict):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data) + "\n")

def extract_tool_names_and_descriptions(tool_schemas):
    tools_info = []
    for tool in tool_schemas:
        name = tool["function"]["name"]
        desc = tool["function"].get("description", "")
        props = tool["function"]["parameters"].get("properties", {})
        param_descriptions = " | ".join(f"{k}: {v.get('description', '')}" for k, v in props.items())
        tools_info.append({
            "name": name,
            "description": f"{desc} — Parameters: {param_descriptions}"
        })
    return tools_info

def is_followup_query(current_query: str, previous_history: List[Dict]) -> bool:
    if not previous_history:
        return False
    history_text = "\n".join(f"{m['role']}: {m.get('content', '')}" for m in previous_history[-6:])
    prompt = f"""Determine whether the following user query is a continuation of the previous conversation.

Previous conversation:
{history_text}

New query:
{current_query}

Is this query a follow-up? Reply only with 'Yes' or 'No'."""
    try:
        response = llm.invoke(prompt).content.strip().lower()
        return response.startswith("yes")
    except Exception as e:
        logger.error(f"Follow-up check failed: {e}")
        return False

async def call_tool_async(tool_fn, tool_args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, tool_fn, tool_args)

def generate_short_response(tool_name, output):
    return f"{tool_name} result: {list(output.values())[0] if isinstance(output, dict) else output}"

def generate_natural_summary(tool_name, description, inputs, output):
    prompt = f"Tool: {tool_name}\nInputs: {json.dumps(inputs)}\nOutput: {json.dumps(output)}\nExplain the result naturally to the user."
    return llm.invoke(prompt).content.strip()

async def run_agent_async(index: int, query_dict: Dict, tools_data, output_path: str, full_convo: List[List[Dict]]):
    query = query_dict["query"]
    query_id = query_dict.get("QueryID", f"q_{str(uuid.uuid4())[:8]}")
    tools, param_map, tool_dict, required_map, tool_schemas, tool_ids = tools_data

    #  Allow all tools for planning
    allowed_tool_names = [tool["function"]["name"] for tool in tool_schemas]
    tool_subset = tool_schemas
    param_map_subset = param_map
    tool_dict_subset = tool_dict
    required_map_subset = required_map
    tool_ids_subset = tool_ids

    previous_history = full_convo[-1] if full_convo else []
    use_history = is_followup_query(query, previous_history)
    print(f"[{query_id}] Using previous history? {use_history}")
    history = previous_history.copy() if use_history else []
    history.append({"role": "user", "content": query})

    tool_prompt = "\n".join(f"{name}: {param_map_subset[name]}" for name in param_map_subset)
    context_text = "\n".join(f"{m['role']}: {m.get('content') or ''}" for m in history)

    planning_prompt = f"""

You must always invoke at least one of the available tools. The user query cannot be answered without tools.

TOOLS:
{tool_prompt}

CONTEXT:
{context_text}

QUERY:
{query}

OUTPUT FORMAT:
Return only a valid JSON array, where each item contains:
- tool_name: the selected tool's name
- parameters: a dictionary of required arguments for that tool

EXAMPLE:
[
  {{
    "tool_name": "weather_forecast",
    "parameters": {{
      "city": "Paris",
      "date": "2024-08-20"
    }}
  }}
]

DO NOT add explanations. Only return the JSON list.
""".strip()

    try:
        plan_response = llm.invoke(planning_prompt)
        time.sleep(3)
        plan = parse_json_content(plan_response.content.strip())

        plan = [p for p in plan if p.get("tool_name") in tool_dict_subset]


        if not plan:
           logger.warning(f"[{query_id}] No tool selected. Falling back to natural response.")
           fallback = llm.invoke(f"Respond naturally to the following user query:\n{query}").content.strip()
           history.append({"role": "assistant", "content": fallback})
           write_jsonl_line(output_path, {
               "QueryID": query_id,
               "query": query,
               "tools": [],
               "history": history,
               "agent_output_label": {"agent_output": fallback}
         })
           full_convo.append(history)
           return

        for p in plan:
            if "tool" in p and "tool_name" not in p:
                p["tool_name"] = p.pop("tool")

        tool_calls = [{
            "id": str(uuid.uuid4()),
            "type": "function",
            "function": {
                "name": p["tool_name"],
                "arguments": p["parameters"]
            },
            "tool_id": tool_ids_subset[p["tool_name"]]
        } for p in plan]

        write_jsonl_line(output_path, {
            "QueryID": query_id,
            "query": query,
            "tools": [],
            "history": history,
            "agent_output_label": {
                "tool_call": tool_calls if len(tool_calls) > 1 else tool_calls[0]
            }
        })

        history.append({
            "role": "assistant",
            "tool_call": tool_calls if len(tool_calls) > 1 else tool_calls[0]
        })

        summaries = []
        for p in plan:
            tool_name = p["tool_name"]
            tool_args = p["parameters"]
            output = await call_tool_async(tool_dict_subset[tool_name].func, tool_args)
            history.append({"role": "tool", "content": generate_short_response(tool_name, output)})

            if isinstance(output, dict) and "error" in output:
                fallback_response = f"The tool `{tool_name}` could not be executed successfully. Reason: {output['error']}"
                history.append({"role": "assistant", "content": fallback_response})
                write_jsonl_line(output_path, {
                    "QueryID": query_id,
                    "query": query,
                    "tools": [],
                    "history": history,
                    "agent_output_label": {
                        "agent_output": fallback_response
                    }
                })
                full_convo.append(history)
                return

            summaries.append(generate_natural_summary(tool_name, tool_dict_subset[tool_name].description, tool_args, output))

        history.append({"role": "assistant", "content": " ".join(summaries)})
        write_jsonl_line(output_path, {
            "QueryID": query_id,
            "query": query,
            "tools": [],
            "history": history,
            "agent_output_label": {
                "agent_output": " ".join(summaries)
            }
        })

        full_convo.append(history)

    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        fallback = llm.invoke(f"Respond naturally to the following message: {query}").content.strip()
        history.append({"role": "assistant", "content": fallback})
        write_jsonl_line(output_path, {
            "QueryID": query_id,
            "query": query,
            #"tools": "filtered_tools_non_empty_queries1.jsonl",
            #"tools": tool_subset,
             "tools": [],
            "history": history,
            "agent_output_label": {"agent_output": fallback}
        })
        full_convo.append(history)

def load_query_dataset(path: str) -> List[Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line.strip()) for line in f]

# MAIN
if __name__ == "__main__":
    query_path = r"C:\Users\b-fkabir\Desktop\New folder\gorilla\input files\text.jsonl"

    tool_path = r"C:\Users\b-fkabir\Desktop\New folder\gorilla\input files\filtered_tools_non_empty_queries1.jsonl"
    tool_path = r"C:\Users\b-fkabir\Desktop\New folder\gorilla\input files\t_eval_tools.jsonl"
    output_path = r"C:\Users\b-fkabir\Desktop\New folder\gorilla\Output Files1\textforcedtool.jsonl"

    open(output_path, 'w').close()
    queries = load_query_dataset(query_path)
    tools_data = load_tools(tool_path)
    full_convo = []

    for i, q in enumerate(queries):
        logger.info(f"Running query {i+1}/{len(queries)}: {q['query']}")
        asyncio.run(run_agent_async(i, q, tools_data, output_path, full_convo))
