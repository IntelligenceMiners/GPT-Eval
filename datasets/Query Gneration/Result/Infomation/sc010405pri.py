data = {
    "Scenario": "one simple query needs 1 tool",
    "Scenario_ID": "1",
    "Message": [
        {
            "role": "system",
            "content": """You are an AI assistant tasked with generating 5 simple queries for a tool. 
The tool is called '{tool_name}' and its description is:
'{tool_description}'

Generate 5 simple and clear queries that could be used to invoke this tool, 
which will provide the user with the correct functionality. 
The queries should be in natural language, suitable for end-users to easily understand.
Each query should call the specific tool and include the required arguments.

### Output Format:
Return a list of 5 queries in natural language. Each query should be listed as a numbered item.

### Example:
Industry: Agricultural equipment manufacturing
Tool: equipment_maintenance_scheduler
Description: Schedules maintenance for agricultural equipment based on equipment type, usage hours, and last maintenance date. This tool helps farmers and equipment managers plan regular maintenance to ensure optimal performance and longevity of their machinery. By inputting the type of equipment, the number of hours it has been used, and the date of the last maintenance, users can receive a recommended maintenance schedule.

Parameters:
- equipment_type (string): Type of agricultural equipment (e.g., tractor, combine harvester).
- usage_hours (integer): Number of hours the equipment has been used since the last maintenance.
- last_maintenance_date (string): Date of the last maintenance (YYYY-MM-DD).

Queries:
1. When should I schedule the next maintenance for my tractor that has been used for 200 hours since the last maintenance on 2025-01-01?
2. What is the recommended maintenance schedule for a combine harvester used for 150 hours since the last maintenance on 2025-02-01?
3. Can you provide a maintenance schedule for a plow that has been used for 300 hours since the last maintenance on 2025-03-01?
4. How often should I maintain my tractor if it is used for 100 hours per month?
5. What maintenance is needed for a harvester that has been used for 500 hours since the last maintenance on 2025-04-01?"""
        },
        {
            "role": "user",
            "content": "Generate 5 queries for the tool"
        }
    ],
    "Contributor": "Farhana"
}

message_01 = [
    {
        "role": "system",
        "content": """
        You are an AI assistant tasked with generating 5 simple queries for a tool. 
        The tool is called '{tool_name}' and its description is:
        '{tool_description}'
        
        Generate 5 simple and clear queries that could be used to invoke this tool, 
        which will provide the user with the correct functionality. 
        The queries should be in natural language, suitable for end-users to easily understand.
        Each query should call the specific tool and include the required arguments.

        ### Output Format:
        Return a list of 5 queries in natural language. Each query should be listed as a numbered item.

        ### Example:
        Industry: Agricultural equipment manufacturing
        Tool: equipment_maintenance_scheduler
        Description: Schedules maintenance for agricultural equipment based on equipment type, usage hours, and last maintenance date. This tool helps farmers and equipment managers plan regular maintenance to ensure optimal performance and longevity of their machinery. By inputting the type of equipment, the number of hours it has been used, and the date of the last maintenance, users can receive a recommended maintenance schedule.
        Parameters: 
        - equipment_type (string): Type of agricultural equipment (e.g., tractor, combine harvester).
        - usage_hours (integer): Number of hours the equipment has been used since the last maintenance.
        - last_maintenance_date (string): Date of the last maintenance (YYYY-MM-DD).

        Queries:
        1. When should I schedule the next maintenance for my tractor that has been used for 200 hours since the last maintenance on 2025-01-01?
        2. What is the recommended maintenance schedule for a combine harvester used for 150 hours since the last maintenance on 2025-02-01?
        3. Can you provide a maintenance schedule for a plow that has been used for 300 hours since the last maintenance on 2025-03-01?
        4. How often should I maintain my tractor if it is used for 100 hours per month?
        5. What maintenance is needed for a harvester that has been used for 500 hours since the last maintenance on 2025-04-01?
        """
    },
    {
        "role": "user",
        "content": "Generate 5 queries for the tool"
    }
]

message_04 = [
    {
        "role": "system",
        "content": """
        You are an AI assistant tasked with generating 5 queries for a tool with some missing input parameters. 
        The tool is called '{tool_name}' and its description is:
        '{tool_description}'

        Generate 5 simple and clear queries that could be used to invoke this tool, 
        but for each query, leave some of the required input parameters missing. 
        For each query, instead of the tool, provide a response indicating which required input(s) are missing. 
        The missing inputs should be clearly mentioned.

        The missing inputs could be:
        - Missing parameter: equipment_type
        - Missing parameter: usage_hours
        - Missing parameter: last_maintenance_date

        ### Output Format:
        Return a list of 5 queries where the missing inputs are indicated clearly.

        ### Example:
        Industry: Agricultural equipment manufacturing
        Tool: equipment_maintenance_scheduler
        Description: Schedules maintenance for agricultural equipment based on equipment type, usage hours, and last maintenance date. This tool helps farmers and equipment managers plan regular maintenance to ensure optimal performance and longevity of their machinery. By inputting the type of equipment, the number of hours it has been used, and the date of the last maintenance, users can receive a recommended maintenance schedule.
        Parameters: 
        - equipment_type (string): Type of agricultural equipment (e.g., tractor, combine harvester).
        - usage_hours (integer): Number of hours the equipment has been used since the last maintenance.
        - last_maintenance_date (string): Date of the last maintenance (YYYY-MM-DD).

        Queries:
        1. When should I schedule the next maintenance for my tractor that has been used for 200 hours since the last maintenance on 2025-01-01? [Missing parameter: equipment_type]
        2. What is the recommended maintenance schedule for a combine harvester used for 150 hours since the last maintenance on 2025-02-01? [Missing parameter: last_maintenance_date]
        3. Can you provide a maintenance schedule for a plow that has been used for 300 hours since the last maintenance on 2025-03-01? [Missing parameter: usage_hours]
        4. How often should I maintain my tractor if it is used for 100 hours per month? [Missing parameter: last_maintenance_date]
        5. What maintenance is needed for a harvester that has been used for 500 hours since the last maintenance on 2025-04-01? [Missing parameter: equipment_type]
        """
    },
    {
        "role": "user",
        "content": "Generate 5 queries for the tool with some missing input parameters"
    }
]

message_05pri = [
    {
        "role": "system",
        "content": """
        You are an AI assistant tasked with generating 5 completely **unique** and **irrelevant** queries for an industry. 
        The industry is called '{industry_name}' and it includes the following tools:
        {tools_list}

        Generate 5 queries that are **completely unrelated** to the tools, their purposes, or the industry. These queries should be **randomly selected** from completely different domains such as science, geography, art, history, hobbies, or pop culture. Ensure there is **no similarity** to each other, and **avoid repetition**.

        Each query should:
        - Be a **distinct and unrelated question** that doesn't invoke any tool functionality.
        - Not be related to the tools listed, nor the industry.
        - Cover a variety of different topics for different queries (e.g., history, geography, entertainment, science, etc.).
        - Be unique in content and phrasing for each industry and each query.

        Please avoid making similar queries for different industries. The queries should **always be fresh** and **entirely random**.

        ### Output Format:
        Return only the 5 unrelated queries without including any industry or tool information.

        Queries:
        1. What is the process of making glass?
        2. How do you solve a Rubik's cube in under a minute?
        3. Who was the first woman to fly in space?
        4. What are the main ingredients in a traditional Japanese sushi roll?
        5. How does the Internet work?
        """
    },
    {
        "role": "user",
        "content": "Generate 5 irrelevant and unique simple different queries for the industry"
    }
]
