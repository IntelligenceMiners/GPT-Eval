import pandas as pd
import json
import re
import os  
import base64
from openai import AzureOpenAI, BadRequestError  
from azure.identity import DefaultAzureCredential, get_bearer_token_provider  
import time
import random
        
endpoint = os.getenv("ENDPOINT_URL", "https://aoai-l-swedencentral.openai.azure.com/")  
deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o-mini-2024-07-18-global")    

# Initialize Azure OpenAI Service client with Entra ID authentication
token_provider = get_bearer_token_provider(  
    DefaultAzureCredential(),  
    "https://cognitiveservices.azure.com/.default"  
)  

client = AzureOpenAI(  
    azure_endpoint=endpoint,  
    azure_ad_token_provider=token_provider,  
    api_version="2024-06-01",  
) 

META_PROMPT_02 = """
You are an AI assistant specializing in generating queries for various industries based on the OpenAI tools provided. Your task is to create **queries** based on multiple **OpenAI tools** to fulfill the user's request.

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

3. **Create Concise and Relevant Queries**: For each combination of tools, generate 5 different variations of queries. Make sure the queries are clear, concise, and relevant to the tools' functionality. Eeach query should include all the tool's parameters information

4. **Ensure Completeness**: The queries should include all required inputs for the tools, even if the user only provides part of the information. You must assume default values where necessary (e.g., assuming a common hotel check-in date, or assuming a standard flight status check). 

5. **Output Format**: 
    - The output must be a list of json objects. 
    - Each JSON object should contain the **tool names** and the **queries** generated for that combination of tools.    
    - You are required to generate queries for 5 distinct combinations of tools. 
    - For each combination of tools, generate 5 query variations. 
    - Ensure that there is at least one combination with 3 tools.

### Output Examples:
#### **Tourism Query JSON**
```json
[
{
    "tool name": ["restaurant_recommender", "hotel_booking"],
    "queries": {
        "query1": "Can you recommend some local restaurants in Paris that serve Pasta within a budget of 30 USD per meal? And can you book a hotel in Paris from 2025-02-01 to 2025-02-06 within a budget of 90 USD per night?",
        "query2": "I need to book a hotel in Paris from 2025-02-01 to 2025-02-06 within a budget of 90 USD per night and also find me some restaurants serving pasta within a budget of 30 USD per meal.",
        "query3": "Can you recommend a restaurant in Paris serving Italian pasta within a budget of 30 USD per meal and book a hotel for me in Paris from 2025-02-01 to 2025-02-06 within 90 USD per night?",
        "query4": "Please find me some top restaurants serving pasta in Paris within 30 USD per meal, and also book a hotel for me in Paris from 2025-02-01 to 2025-02-06 within 90 USD per night.",
        "query5": "Book me a hotel in Paris from 2025-02-01 to 2025-02-06 within a budget of 90 USD per night, and recommend some local restaurants in Paris that serve pasta within a 30 USD budget."
    }
},
{
    "tool name": ["flight_tracker", "hotel_booking"],
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
}
]

""".strip()

META_PROMPT_05 = """
You are an AI assistant. Sometimes, users will ask questions that are not related to the tools available for the given industry. Your task is to generate **irrelevant queries** for the given tools. These queries should still be relevant to the **industry's general theme** but **do not directly involve any of the tools**. For example, if the tools are about **hotel booking**, **restaurant recommendations**, or **flight tracking**, a user might ask something that is completely unrelated, such as "Can you recommend books?" or "What is the weather in Paris today?"

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
]

""".strip()


def OpenAI_tool_calling_scenario_02(tools: list):
    
    completion = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": META_PROMPT_02,
            },
            {
                "role": "user",
                "content": "Generate queries based on the following OpenAI tools: " + str(tools) + "try 5 different combinations of these tools,and generate 5 queries for each combination "
            },
        ],
        temperature=0.0,
        max_tokens=10000,
        top_p=1.0,
        presence_penalty=0.0,
        stream=False,
        stop=None,
        tools=tools
    )

    return completion.choices[0].message.content



def generate_queries_for_industries_02(jsonl_file_path):
    tools = []  # List to store tools for each industry
    previous_industry_name = None  # To track the previous industry name
    industry_id_map = {}  # Dictionary to store industry IDs

    # Open the JSONL file for reading
    with open(jsonl_file_path, 'r') as file:
        for line in file:
            data = json.loads(line.strip())  # Parse the JSON object from the line
            industry_name = data['IndustryName']
            industry_id = data['IndustryID']  # Assuming 'IndustryID' is in the JSON data
            tool = data['Tool']

            # If the industry changes, reset the tools list
            if industry_name != previous_industry_name:
                # Clear the tools list for the new industry
                tools.clear()
                previous_industry_name = industry_name  # Update to the new industry

            # Append the tool to the list
            tools.append(tool)

            # Save IndustryID and associate it with the industry name
            industry_id_map[industry_name] = industry_id

            if len(tools) == 5:
                # Include IndustryID in the AI response
                ai_response = OpenAI_tool_calling_scenario_02(tools)
                # Sleep for a random time between 1 and 5 seconds
                time.sleep(random.uniform(1, 5))  # Random sleep between 1 and 5 seconds
                formatted_response = format_response(ai_response)

                # Reorder the fields and put industryid at the start
                for response in formatted_response:
                    reordered_response = {
                        "industryid": industry_id_map[industry_name],  # Place industryid first
                        **response  # Unpack the original response after the industryid
                    }
                    # Replace the original response with the reordered one
                    response.clear()
                    response.update(reordered_response)

                # Save the formatted response to a .jsonl file
                save_to_jsonl(formatted_response, 'C:/Users/b-qixinma/Desktop/UniveralToolKits/Result/4o-08-06/queries02.jsonl')
                print(ai_response)

                tools.clear()  # Reset the tools list for the next batch


def OpenAI_tool_calling_scenarion_05(tools: list,industry_name:str):
    
    completion = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": META_PROMPT_05,
            },
            {
                "role": "user",
                "content": f'generate 5 irrelevant queries for the given tools {str(tools)}. These queries should still be relevant to {industry_name} but do not directly involve any of the {tools}'
            },
        ],
        temperature=0.0,
        max_tokens=10000,
        top_p=1.0,
        presence_penalty=0.0,
        stream=False,
        stop=None,
        tools=tools,
        tool_choice = "auto"
    )

    return completion.choices[0].message.content


def generate_queries_for_industries_05(jsonl_file_path):
    tools = []  # List to store tools for each industry
    previous_industry_name = None  # To track the previous industry name
    industry_id_map = {}  # Dictionary to store industry IDs

    # Open the JSONL file for reading
    with open(jsonl_file_path, 'r') as file:
        for line in file:
            data = json.loads(line.strip())  # Parse the JSON object from the line
            industry_name = data['IndustryName']
            industry_id = data['IndustryID']  # Assuming 'IndustryID' is in the JSON data
            tool = data['Tool']

            # If the industry changes, reset the tools list
            if industry_name != previous_industry_name:
                # Clear the tools list for the new industry
                tools.clear()
                previous_industry_name = industry_name  # Update to the new industry

            # Append the tool to the list
            tools.append(tool)

            # Save IndustryID and associate it with the industry name
            industry_id_map[industry_name] = industry_id

            if len(tools) == 5:
                # Include IndustryID in the AI response
                ai_response = OpenAI_tool_calling_scenarion_05(tools,industry_name)
                # Sleep for a random time between 1 and 5 seconds
                time.sleep(random.uniform(1, 5))  # Random sleep between 1 and 5 seconds
                formatted_response = format_response(ai_response)

                # Reorder the fields and put industryid at the start
                for response in formatted_response:
                    reordered_response = {
                        "industryid": industry_id_map[industry_name],  # Place industryid first
                        **response  # Unpack the original response after the industryid
                    }
                    # Replace the original response with the reordered one
                    response.clear()
                    response.update(reordered_response)

                # Save the formatted response to a .jsonl file
                save_to_jsonl(formatted_response, 'C:/Users/b-qixinma/Desktop/UniveralToolKits/Result/4o-08-06/queries05.jsonl')

                tools.clear()  # Reset the tools list for the next batch


def format_response(ai_response):
    # Step 1: Extract the JSON portion from the response using a regular expression
    print(ai_response)
    json_string = re.search(r'```json\n(.*?)\n```', ai_response, re.DOTALL)
    if not json_string:
        print("No JSON found!")
        return []
    # Step 2: Extract the JSON content (the portion between the triple backticks)
    json_content = json_string.group(1)
   
    # Step 3: Parse the cleaned JSON content into a Python dictionary
    try:
        query_data = json.loads(json_content)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON content:", e)
        return []

    # Step 4: Format the response
    formatted_response = []
    for response in query_data:
        # Extract necessary fields
        tool_name = response["tools"]
        query = response["queries"]
        
        # Construct the formatted tool object
        formatted_tool = {
            "tool": tool_name,
            "query": query
        }
        formatted_response.append(formatted_tool)

    return formatted_response


def save_to_jsonl(data, filename):
    """Save each tool as a JSON object on a new line in a .jsonl file."""
    with open(filename, 'a') as output_file:
        for item in data:
            # Ensure the item is a valid JSON string and write it to the file, one per line.
            json_line = json.dumps(item)  # Convert the Python dictionary to a JSON string
            output_file.write(json_line + "\n")  # Write to file with newline


def split_queries(jsonl_file_path, output_file_path,scenarioid):
    # Open the JSONL file for reading
    with open(jsonl_file_path, 'r') as file:
        lines = file.readlines()
    
    # List to hold the split queries
    all_entries = []

    for line in lines:
        data = json.loads(line.strip())  # Parse the JSON object from the line
        industryid = data['industryid']
        tools = data['tool']
        query_dict = data['query']

        # For each query in the query dictionary, create a new entry
        for query_key, query in query_dict.items():
            entry = {
                "IndustryID": industryid,
                "ScenarioID": scenarioid,   # Copy the industryid
                "Tools": tools,  # Copy the tool list
                "Queries": query  # Add query_value for the actual query content
            }
            all_entries.append(entry)

    # Write the updated entries to the output JSONL file
    with open(output_file_path, 'w') as output_file:
        for entry in all_entries:
            output_file.write(json.dumps(entry) + '\n')


