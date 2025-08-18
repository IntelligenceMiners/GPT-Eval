import json
import os

ScenarioID = 7
Scenario_description = "Component query that requires multiple tools in sequence."

example_queries = [
    {
        "tools": ["equipment_comparison_tool", "equipment_availability_checker", "equipment_cost_calculator"],
        "Query": "Compare the John Deere 5075E and Kubota M7060 based on power, fuel efficiency, and price using the equipment_comparison_tool. If one model is more efficient, check its availability at dealerships near Springfield using the equipment_availability_checker. Otherwise, calculate the total cost of ownership for the Kubota M7060 using the equipment_cost_calculator with a purchase price of $95,000, an annual maintenance cost of $3,000, fuel consumption of 12 liters per hour, and 1,200 operating hours per year."
    },
    {
        "tools": ["equipment_efficiency_analyzer", "equipment_comparison_tool", "equipment_availability_checker"],
        "Query": "Analyze my tractor's efficiency using the equipment_efficiency_analyzer. It consumes 10 liters of fuel per hour and plows 50 acres per hour. If its efficiency is lower than 6 acres per liter, compare the John Deere 5075E and Kubota M7060 in terms of power, fuel efficiency, and price using the equipment_comparison_tool. Otherwise, check the availability of the John Deere 6155M at dealerships near Springfield using the equipment_availability_checker."
    },
    {
        "tools": ["equipment_maintenance_scheduler", "equipment_cost_calculator", "equipment_comparison_tool"],
        "Query": "Schedule maintenance for my tractor using the equipment_maintenance_scheduler. It has been used for 200 hours since the last maintenance on 2025-01-01. If the next maintenance is earlier than 2025-06-01, calculate its total cost of ownership using the equipment_cost_calculator. The tractor was purchased for $80,000, has an annual maintenance cost of $2,500, consumes 10 liters of fuel per hour, and operates 1,500 hours per year. If the total ownership cost exceeds $100,000 over 5 years, analyze its fuel efficiency using the equipment_efficiency_analyzer. Otherwise, compare its fuel efficiency with a newer model using the equipment_comparison_tool."
    },
    {
        "tools": ["equipment_cost_calculator", "equipment_comparison_tool", "equipment_availability_checker"],
        "Query": "Calculate the total cost of owning a combine harvester using the equipment_cost_calculator. It has a purchase price of $250,000, an annual maintenance cost of $5,000, and a fuel consumption of 20 liters per hour, operating 1,000 hours per year. If the cost is too high, compare the John Deere S780 and the Case IH 8250 based on power, fuel efficiency, and price using the equipment_comparison_tool. Otherwise, check the availability of used John Deere S780 models in dealerships near Des Moines using the equipment_availability_checker."
    },
    {
        "tools": ["equipment_efficiency_analyzer", "equipment_comparison_tool", "equipment_cost_calculator"],
        "Query": "Analyze my tractor's efficiency using the equipment_efficiency_analyzer. It consumes 12 liters of fuel per hour and plows 55 acres per hour. If its efficiency is lower than 5 acres per liter, compare the John Deere 5075E and Kubota M7060 based on power, fuel efficiency, and price using the equipment_comparison_tool. If one model is significantly more efficient, check its availability at dealerships near Springfield using the equipment_availability_checker. Otherwise, calculate the total cost of ownership for the more efficient model using the equipment_cost_calculator with a purchase price of $100,000, an annual maintenance cost of $3,500, fuel consumption of 10 liters per hour, and 1,500 operating hours per year."
    }
]


system_message = f"""
### You are a query generator. You need to generate 5 queries for the tools listed above in the industry {industry_name}.
### The tools are: {tools}
### The requirements for the queries are:
1. The queries should call at least 2 of the listed tools.
2. The queries should use the tools in sequence, the next tool should be called based on the result of the previous tool, that means, the result of the first tool calling determines different afterwards tool callings, ask for at lease two cases based on the result. This determination should be given obviously in the query.
3. The format of the response should be exactly the same as the example queries below.
4. Please use the corresponding background knowledge of this industry to generate arguments for the queries, don't use A,B,C or 1,2,3 instead.
5. Try to use more accurate words instead of general words, for example, use "lower than 5 liters" instead of "lower than expected".
6. Generate 5 queries in total.
-------------------------------------------------------------------------------------------------------
### Here is the example of a query:
We have a list of tools: {tools_example}
The generated query should be: 
{json.dumps(example_queries, indent=2)}
""".strip()

user_message = f"""
Generate 5 queries for the tools listed above in the industry {industry_name}.
"""