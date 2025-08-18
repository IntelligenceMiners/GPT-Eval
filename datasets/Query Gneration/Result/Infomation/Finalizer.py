import json
Scenario_1 = {
    "Scenario": "one simple query needs 1 tool",
    "Scenario_ID": "01",
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
Scenario_2 = {
    "Scenario": "compound query needs 2 to 3 tools in parallel",
    "Scenario_ID": "2",
    "Message": [
        {
            "role": "system",
            "content": """You are an AI assistant specializing in generating queries for various industries based on the OpenAI tools provided. Your task is to create **queries** based on multiple **OpenAI tools** to fulfill the user's request.

### Guidelines:
1. **Understand the Tools**: Each tool comes with a specific functionality, and you need to combine these tools based on the user's needs. For example:
   - **Restaurant Recommender** (Suggests restaurants based on location, cuisine, and budget).
   - **Hotel Booking** (Books hotels based on location, check-in/check-out dates, and budget).
   - **Itinerary Planner** (Plans itineraries based on user interests and dates).
   
2. **Combine Multiple Tools**: Create queries that combine 2 or 3 tools at a time. Your goal is to generate queries where multiple tools are used together in a real-world scenario. For example:
   - If a user is planning a trip, you can combine **Hotel Booking**, **Flight Tracker**, and **Itinerary Planner** to generate queries that ask for hotels, flight information, and an itinerary at once.
   - The user should not have to ask for each tool separately.
   - You can assume the user is asking for a specific task that requires multiple tools to complete.
   - There is at least one tool combination with **3 tools**.

3. **Create Concise and Relevant Queries**: For each combination of tools, generate 5 different variations of queries. Make sure the queries are clear, concise, and relevant to the tools' functionality. Each query should include all the tool's parameters information.

4. **Ensure Completeness**: The queries should include all required inputs for the tools, even if the user only provides part of the information. You must assume default values where necessary (e.g., assuming a common hotel check-in date, or assuming a standard flight status check). 

5. **Output Format**: 
    - The output must be a list of JSON objects. 
    - Each JSON object should contain the **tool_names** and the **queries** generated for that combination of tools.    
    - You are required to generate queries for 5 distinct combinations of tools. 
    - For each combination of tools, generate 5 query variations. 
    - Ensure that there is at least one combination with 3 tools.

### Output Examples:
#### **Tourism Query JSON**
```json
[
    {
        "tool_names": ["restaurant_recommender", "hotel_booking"],
        "queries": {
            "query1": "Can you recommend some local restaurants in Paris that serve Pasta within a budget of 30 USD per meal? And can you book a hotel in Paris from 2025-02-01 to 2025-02-06 within a budget of 90 USD per night?",
            "query2": "I need to book a hotel in Paris from 2025-02-01 to 2025-02-06 within a budget of 90 USD per night and also find me some restaurants serving pasta within a budget of 30 USD per meal.",
            "query3": "Can you recommend a restaurant in Paris serving Italian pasta within a budget of 30 USD per meal and book a hotel for me in Paris from 2025-02-01 to 2025-02-06 within 90 USD per night?",
            "query4": "Please find me some top restaurants serving pasta in Paris within 30 USD per meal, and also book a hotel for me in Paris from 2025-02-01 to 2025-02-06 within 90 USD per night.",
            "query5": "Book me a hotel in Paris from 2025-02-01 to 2025-02-06 within a budget of 90 USD per night, and recommend some local restaurants in Paris that serve pasta within a 30 USD budget."
        }
    },
    {
        "tool_names": ["flight_tracker", "hotel_booking"],
        "queries": {
            "query1": "Can you track the status of flight SK2087 on 2025-02-25? And can you book a hotel in Paris from 2025-02-01 to 2025-02-06 within a budget of 90 USD per night?",
            "query2": "I need to track the status of flight SK2087 on 2025-02-25 and also book a hotel in Paris from 2025-02-01 to 2025-02-06 within a budget of 90 USD per night.",
            "query3": "Track flight SK2087 on 2025-02-25 and recommend a hotel in Paris from 2025-02-01 to 2025-02-06 with a budget of 90 USD per night.",
            "query4": "Can you help me track the flight SK2087 status on 2025-02-25 and book a hotel in Paris from 2025-02-01 to 2025-02-06 within a budget of 90 USD per night?",
            "query5": "I want to track the flight SK2087 status on 2025-02-25, and book a hotel in Paris from 2025-02-01 to 2025-02-06 within a budget of 90 USD per night."
        }
    },
    {
    "tool name": ["itinerary_planner", "restaurant_recommender", "hotel_booking"],
    "queries": {
        "query1": "Can you plan an itinerary for Paris from 2025-02-21 to 2025-02-25 including cycling? Also, recommend some local restaurants in Paris that serve Pasta within a budget of 30 USD per meal and book a hotel for me in Paris from 2025-02-01 to 2025-02-06 within 90 USD per night?",
        "query2": "I need a 5-day itinerary for Paris from 2025-02-21 to 2025-02-25 with cycling included, recommend some local restaurants that serve Pasta within a 30 USD budget per meal, and book a hotel for me in Paris from 2025-02-01 to 2025-02-06 within a 90 USD budget per night.",
        "query3": "Plan my itinerary in Paris from 2025-02-21 to 2025-02-25 with cycling, recommend some restaurants serving pasta within a budget of 30 USD per meal, and book a hotel for me in Paris from 2025-02-01 to 2025-02-06 with a 90 USD budget per night.",
        "query4": "Can you plan an itinerary for Paris from 2025-02-21 to 2025-02-25 including cycling, recommend restaurants serving pasta within 30 USD per meal, and help me book a hotel in Paris from 2025-02-01 to 2025-02-06 within 90 USD per night?",
        "query5": "I need an itinerary for Paris from 2025-02-21 to 2025-02-25 with cycling included, recommend some local restaurants serving pasta within a 30 USD budget, and book a hotel in Paris from 2025-02-01 to 2025-02-06 with a budget of 90 USD per night."
    }
},
{
    "tool name": ["tour_guide_recommender", "hotel_booking", "itinerary_planner"],
    "queries": {
        "query1": "Can you recommend a tour guide who speaks English and specializes in food tours? And can you book a hotel in Paris from 2025-02-01 to 2025-02-06 within a budget of 90 USD per night? Also, plan an itinerary for Paris from 2025-02-21 to 2025-02-25 including cycling.",
        "query2": "I need a tour guide who speaks English and specializes in food tours, book a hotel for me in Paris from 2025-02-01 to 2025-02-06 within a 90 USD per night budget, and plan an itinerary for Paris from 2025-02-21 to 2025-02-25 with cycling included.",
        "query3": "Can you find me a tour guide for a food tour in Paris who speaks English, book a hotel for me from 2025-02-01 to 2025-02-06 within a 90 USD per night budget, and plan an itinerary for Paris from 2025-02-21 to 2025-02-25 with cycling included?",
        "query4": "Recommend a tour guide for a food tour in Paris who speaks English, help me book a hotel in Paris from 2025-02-01 to 2025-02-06 within 90 USD per night, and plan an itinerary for Paris from 2025-02-21 to 2025-02-25 including cycling.",
        "query5": "I want a tour guide for a food tour in Paris who speaks English, book me a hotel in Paris from 2025-02-01 to 2025-02-06 within 90 USD per night, and plan an itinerary for Paris including cycling from 2025-02-21 to 2025-02-25."
    }
},
{
    "tool name": ["flight_tracker", "hotel_booking", "itinerary_planner"],
    "queries": {
        "query1": "Can you track the status of flight SK2087 on 2025-02-25? And can you book a hotel in Paris from 2025-02-01 to 2025-02-06 within a budget of 90 USD per night? Also, plan an itinerary for Paris from 2025-02-21 to 2025-02-25 including cycling.",
        "query2": "I need to track flight SK2087 on 2025-02-25, book a hotel in Paris from 2025-02-01 to 2025-02-06 within a 90 USD per night budget, and plan an itinerary for Paris with cycling from 2025-02-21 to 2025-02-25.",
        "query3": "Track the status of flight SK2087 on 2025-02-25, recommend a hotel in Paris from 2025-02-01 to 2025-02-06 with a 90 USD per night budget, and also plan an itinerary for Paris including cycling from 2025-02-21 to 2025-02-25.",
        "query4": "Please track the flight SK2087 status on 2025-02-25, book me a hotel in Paris from 2025-02-01 to 2025-02-06 with a 90 USD budget per night, and plan an itinerary for Paris from 2025-02-21 to 2025-02-25 with cycling.",
        "query5": "I need to track flight SK2087 on 2025-02-25, book a hotel in Paris from 2025-02-01 to 2025-02-06 with a 90 USD budget per night, and plan an itinerary including cycling for Paris from 2025-02-21 to 2025-02-25."
    }
]
```"""
        },
        {
            "role": "user",
            "content": "generate 5 irrelevant queries for the given tools {str(tools)}. These queries should still be relevant to {industry_name} but do not directly involve any of the {tools}"
        }
    ],
    "Contributor": "Qixin Ma"
}
Scenario_3 = {
    "Scenario": "compound query needs 2 to 3 calls on one same tool in parallel",
    "Scenario_ID": "04",
    "Message": [
      {
        "role": "system",
        "content": """
        You are an AI specialized in generating example cpmpound queries for a tool within various industries. 
        Your task is to generate **five unique queries** for {tool_name} that belong to {newIndustry}. 
        These compound queries should intelligently combine same tool calls based on shared parameters.

        ### Guidelines:  
        1. **Industry Specification**: The queries should align with a specified industry. Ensure that the queries are relevant to the domain and reflect real-world applications. 
   
        2. **Extract Key Parameters**: For each query, extract its key parameters (e.g., location, date, price) and identify which tool share the same parameters from {tools}.
   
        3. **Generate Compound Queries**: Formulate queries that:
            - Call the {tool_name} **at least twice** in a each query.
            - Maintain clarity, conciseness, and relevance.
            -Ensure that the same queries are not generated for the same tool.


        4. **Output**: Generate five compound queries of the {tool_name}.

        ### Output:
        Industry: The specific industry for which the queries are generated.
        Tool: The tool name for which the queries are generated.    
        Queries: A list of 5 queries generated for the tool.

        **A reusable prompt/query based on the user message**

        ###Example Output:
        Tool: 'equipment_maintenance_scheduler'
            Query1: 'Schedule maintenance for a tractor used for 500 hours since last maintenance on 2023-01-15 and a combine harvester used for 300 hours since last maintenance on 2023-02-10.'
            Query2: 'Plan maintenance for a plow with 200 hours of usage since last maintenance on 2023-03-05 and a seeder with 150 hours since last maintenance on 2023-04-01.'
            Query3: 'Determine maintenance schedule for a sprayer used for 400 hours since last maintenance on 2023-05-20 and a harrow used for 250 hours since last maintenance on 2023-06-15.'
            Query4: 'Set up maintenance for a baler with 350 hours of usage since last maintenance on 2023-07-10 and a mower with 180 hours since last maintenance on 2023-08-05.'  
            Query5: 'Organize maintenance for a tiller used for 220 hours since last maintenance on 2023-09-01 and a planter used for 270 hours since last maintenance on 2023-10-01.'
        """
    },
    {
        "role": "user",
        "content": "Generate queries for the {toolName} tool of the {industry} industry."
    }
    ],
    "Contributor": "Tabassum"
}
Scenario_4 = {
    "Scenario": "A simple query but some required arguments are missing",
    "Scenario_ID": "04",
    "Message": [
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
""".strip()
        },
        {
            "role": "user",
            "content": "Generate 5 queries for the tool with some missing input parameters"
        }
    ],
    "Contributor": "Farhana"
}
Scenario_5 = {
    "Scenario": "one simple but NO tools support",
    "Scenario_ID": "05",
    "Message": [
        {
            "role": "system",
            "content": """You are an AI assistant. Sometimes, users will ask questions that are not related to the tools available for the given industry. Your task is to generate **irrelevant queries** for the given tools. These queries should still be relevant to the **industry's general theme** but **do not directly involve any of the tools**. For example, if the tools are about **hotel booking**, **restaurant recommendations**, or **flight tracking**, a user might ask something that is completely unrelated, such as "Can you recommend books?" or "What is the weather in Paris today?"

### Guidelines:
1. **Generate Irrelevant Queries**: The goal is to generate queries that are unrelated to the tools listed, but still reasonable within the context of the industry. Eeach query must NOT include all the tool's parameters information


2. **Do Not Relate to Tools**: Ensure the queries do not directly require the use of any of the tools  but are still reasonable and relevant within the industry.

3. **Output Format**: 
    - The output must be a list of tools name and a list of irrelevant queries.
    - These queries should be contextually reasonable but do not correspond to the functionalities of the provided tools.


### Example Output for Tourism Industry:
```json
[
  {
    "tool name": ["restaurant_recommender", "hotel_booking", "flight_tracker", "itinerary_planner", "tour_guide_recommender"],
    "queries": {
      "query1": "Can you recommend some great travel books for my next trip?",
      "query2": "What is the best way to write a travel blog?",
      "query3": "How do I start a travel YouTube channel?",
      "query4": "What are some tips for saving money while traveling?",
      "query5": "What is the most popular tourist destination this year?"
    }
  }
]"""
        },
        {
            "role": "user",
            "content": "generate 5 irrelevant queries for the given tools {str(tools)}. These queries should still be relevant to {industry_name} but do not directly involve any of the {tools}"
        }
    ],
    "Contributor": "Qixin Ma"
}
Scenario_5pri = {
    "Scenario": "Irrelevent Query will return no tools",
    "Scenario_ID": "05'",
    "Message": [
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
    ],
    "Contributor": "Farhana"
}
Scenario_6 = {
    "Scenario": "compound query, there are tools support one part of the query but no tools support for other parts",
    "Scenario_ID": "06",
    "Message": [
       {
        "role": "system",
        "content": """
        You are an AI specialized in generating example compound queries for a tool within various industries. 
        Your task is to generate **five unique queries** for {tool_name} that belong to {newIndustry}. These compound queries should intelligently combine the tool calls based on shared parameters.

        Each compound query should consist of two parts: one part's answer should be found in the {tool_name}, while the other part's answer should not be found in any of the other four tools in {tools}.
        These compound queries should intelligently combine same tool calls based on shared {parameters}.

        ### Guidelines:  
        1. **Industry Specification**: The queries should align with a specified industry. Ensure that the queries are relevant to the domain and reflect real-world applications. 
   
        2. **Extract Key Parameters**:  For each query, identify key parameters (e.g., location, date, price) and ensure that one part of the query is answered by {tool_name}, while the other part is not answered by any tool in {tools}.
        3. **Generate Compound Queries**: Formulate queries that:
            - Include two distinct parts as specified.
            - Call the {tool_name} in at least one part of each query.
            - Maintain clarity, conciseness, and relevance

        4. **Output**: Generate five compound queries of the {tool_name}.

        ### Output:
        Industry: The specific industry for which the queries are generated.
        Tool: The tool name for which the queries are generated.    
        Queries: A list of 5 queries generated for the tool.

        **A reusable prompt/query based on the user message**

        ###Example Output:
        Tool: "equipment maintenance scheduler"
        Other tools: ['equipment_cost_calculator', 'equipment_efficiency_analyzer', 'equipment_comparison_tool', 'equipment_availability_checker']
            Query1: "For a tractor used for 250 hours since the last maintenance on 2023-02-01, determine the next maintenance schedule using the equipment maintenance scheduler. Additionally, gather anecdotal advice from local farmers on common signs of wear to watch for in similar tractors."
            Query2: "Schedule the next maintenance for a combine harvester that has been used for 400 hours since the last maintenance on 2023-03-10 using the equipment maintenance scheduler. Also, research historical maintenance records in the local library to find any recurring issues with this model."
            Query3: "Using the equipment maintenance scheduler, plan the maintenance for a plow with 150 hours of usage since the last maintenance on 2023-04-20. Simultaneously, consult with a veteran mechanic to gather insights on any additional preventive maintenance tips for plows."
            Query4: "Determine the maintenance schedule for a seeder that has operated for 180 hours since its last maintenance on 2023-05-05 using the equipment maintenance scheduler. In addition, interview local agricultural historians to uncover any traditional maintenance techniques specific to seeders."
            Query5: "For a sprayer with 320 hours of usage since its last maintenance on 2023-06-15, use the equipment maintenance scheduler to schedule its next maintenance. Meanwhile, explore regional farming forums for user experiences and recommendations on extending sprayer lifespan."
        """
    },
    {
        "role": "user",
        "content": "Generate 5 queries for the {toolName} tool of the {industry} industry"
    }
    ],
    "Contributor": "Tabassum"
}
Scenario_7 = {
    "Scenario": "Compound query that requires multiple tools in sequence.",
    "Scenario_ID": "07",
    "Message": [
        {
            "role": "system",
            "content": """
### You are a query generator. You need to generate 5 queries for the tools listed above in the industry {industry_name}.
### The tools are: {tools}
### The requirements for the queries are:
1. The queries should call at least 2 of the listed tools.
2. The queries should use the tools in sequence. The next tool should be called based on the result of the previous tool, meaning that the result of the first tool determines the next tool to be used. Include at least two possible cases based on different results.
3. The format of the response should be exactly the same as the example queries below.
4. Use industry-specific background knowledge to generate meaningful arguments in the queries instead of placeholders like A, B, C or 1, 2, 3.
5. Use precise language, e.g., "lower than 5 liters" instead of "lower than expected."
6. Generate 5 queries in total.

-------------------------------------------------------------------------------------------------------
### Example of a Query:
We have a list of tools: {tools_example}
The generated query should be: 
{json.dumps(example_queries, indent=2)}
""".strip()
        },
        {
            "role": "user",
            "content": "Generate 5 queries for the tools listed above in the industry {industry_name}."
        }
    ],
    "Contributor": "Xinyi Liu"
}

# Combine all scenarios into a single dictionary
all_scenarios = {
    "Scenario_1": Scenario_1,
    "Scenario_2": Scenario_2,
    "Scenario_3": Scenario_3,
    "Scenario_4": Scenario_4,
    "Scenario_5": Scenario_5,
    "Scenario_5pri": Scenario_5pri,
    "Scenario_6": Scenario_6,
    "Scenario_7": Scenario_7
}

# Write all scenarios to a JSON file
with open("output.json", "w", encoding="utf-8") as json_file:
    json.dump(all_scenarios, json_file, indent=4, ensure_ascii=False)

print("All scenarios have been written to output.json")
