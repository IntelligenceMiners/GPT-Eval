message_03 = [
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
]

message_06 = [
    {
        "role": "system",
        "content": """
        You are an AI specialized in generating example compound queries for a tool within various industries. 
Your task is to generate **five unique queries** for {tool_name} that belong to {newIndustry}. 
Each compound query should consist of two parts: one part's should have all the parameters same as the {tool_name}, while the other part's answer should not have any matched parameter any of the other four tools provided in {tools}.

### Guidelines:  
1. **Industry Specification**: The queries should align with a specified industry. Ensure that the queries are relevant to the domain and reflect real-world applications. 
   
2. **Extract Key Parameters**:  For each query, identify key parameters (e.g., location, date, price) and ensure that one part of the query is answered by {tool_name}, while the other part is not answered by any tool in {tools}.
3. **Generate Compound Queries**: Formulate queries that:
    - Include two subqueries within one main query as specified.
    - Call the {tool_name} in at least one subquery of each query based on the matched parameters
    - Maintain clarity, conciseness, and relevance

4. **Output**: Generate five compound queries of the {tool_name}.

### Output:
Industry: The specific industry for which the queries are generated.
Tool: The tool name for which the queries are generated.    
Queries: A list of 5 queries generated for the tool.

**A reusable prompt/query based on the user message**

###Example Output:
###Example Output:
  Tool: "equipment maintenance scheduler"
  Other tools: ['equipment_cost_calculator', 'equipment_efficiency_analyzer', 'equipment_comparison_tool', 'equipment_availability_checker']
    Query1: "When should I schedule the next maintenance for my combine harvester, which has been used for 500 hours since the last maintenance on 2024-07-10? Additionally, what are the recent advancements in combine harvester technology that improve grain quality during harvest, excluding comparisons based on power, fuel efficiency, or price?"
    Query2: "When should I plan the next maintenance for my plow with 300 hours of usage since the last service on 2023-11-15? Also, can you discuss recent innovations in plow design that enhance soil health, excluding any cost or fuel efficiency analysis?"
    Query3: "How should I approach scheduling maintenance for my irrigation system, with 1000 hours logged since the previous maintenance on 2023-09-05? Additionally, what new water conservation technologies in irrigation could be considered, independent of equipment availability at local dealerships?"
    Query4: "What factors should guide my next maintenance schedule for the tiller, which has been used for 400 hours since its last service on 2024-06-01? Moreover, how does the introduction of automation in agriculture influence labor efficiency, without reference to specific models or fuel consumption?."
    Query5: "For a sprayer with 320 hours of usage since its last maintenance on 2023-06-15, use the equipment maintenance scheduler to schedule its next maintenance. Meanwhile, explore regional farming forums for user experiences and recommendations on extending sprayer lifespan."
        """
    },
    {
        "role": "user",
        "content": "Generate 5 queries for the {toolName} tool of the {industry} industry"
    }
]

message_08 = [
    {
        "role": "system",
        "content": """"
       You are an AI specialized in extracting key queries from large bodies of text for specific tools within various industries. 
Your task is to identify and extract the **main query** from the provided text that is relevant to {tool_name}. The main query should be based on matched parameters that align with the tool's functionalities.

The query must identify the core parameter that is matched with the tool's functionalities.

### Guidelines:  
1. **Industry Specification**: The queries should align with a specified industry. Ensure that the queries are relevant to the domain and reflect real-world applications. 
2. **Text Analysis**: Carefully analyze the provided text to understand the context and identify relevant information.
   
3. **Extract Key Parameters**: From the large query, identify key parameters (e.g., location, date, price) and ensure that the query is answered by {tool_name}.
4. **Generate Large Queries**: Formulate queries that:
    - The query text should be large, which will have the key parameter that is matched with the tool's functionalities.
    - Must extract and summarize the large query into a simplified query that calls the given tool {tool_name} in at least one part of each query.
    - Maintain clarity, conciseness, and relevance.

5. **Output**: Generate 2 large text queries for the {tool_name}.

### Output:
Industry: The specific industry for which the queries are generated.
Tool: The tool name for which the queries are generated.    
Queries: A list of 2 large queries generated for the tool.

**A reusable prompt/query based on the user message**

###Example Output:
  Tool Name: 'fertilizer_recommendation_tool'
    Query1: 'As a farmer dedicated to maximizing the yield and health of my wheat crop, I am seeking guidance on the optimal fertilizer application. My wheat is currently planted in a field with clay soil, known for its compact nature and potential to retain moisture. The plants have just entered the vegetative stage, which is a critical phase for establishing a strong root system and promoting vigorous leaf growth. Considering these factors, I would appreciate detailed recommendations on specific fertilizers that can enhance nutrient uptake, improve soil structure, and ultimately boost the resilience and productivity of my wheat during this growth phase.'
    Query2: 'I am managing a rice cultivation project in an area predominantly composed of sandy soil, which poses unique challenges due to its high drainage capacity and low nutrient retention. My rice plants have reached the flowering stage, a pivotal period for reproductive development and grain setting. Given the soil's characteristics and the current growth stage of the rice, I am looking for comprehensive fertilizer recommendations that will not only provide the necessary nutrients to support optimal grain formation but also address potential nutrient leaching issues. Any insights on suitable fertilizers and application techniques that align with these conditions would be invaluable.'
    Query3: 'With a strong commitment to sustainable agriculture, I am growing soybeans in a loamy soil environment, which offers a balanced texture and good fertility. My soybean crops are now in the flowering stage, a crucial time for ensuring successful pod development and seed formation. I am interested in learning about environmentally friendly fertilizer options that can sustain high productivity while maintaining soil health. Detailed advice on specific products or nutrient management strategies that cater to the needs of soybeans in this growth stage and soil type would greatly assist in achieving my sustainability goals.'
    Query4: 'On my diversified farm, I am concurrently cultivating corn and tomato crops, each thriving in different soil types—corn in loamy soil and tomatoes in clay soil. Both crops are currently experiencing the vegetative growth stage, where maximizing nutrient absorption and promoting healthy plant structure are essential. I am seeking a thorough analysis of tailored fertilizer programs that can address the distinct nutrient requirements of each crop, considering their unique soil environments. Recommendations on how to effectively manage these needs to optimize growth and ensure robust development for both corn and tomatoes would be highly beneficial.'
    Query5: 'Preparing for the upcoming growing season, I am focused on establishing a successful barley crop in sandy soil, characterized by its quick drainage and limited nutrient holding capacity. The barley plants are at the seedling stage, which is vital for setting a strong foundation for subsequent growth. I am interested in receiving expert guidance on the best fertilizer practices that can enhance early root development, compensate for the soil's nutrient deficiencies, and support the plants through their initial growth phase. Detailed insights into suitable fertilizers and innovative application methods would help in achieving a successful start to the season.'

 
        """
  },
    {
        "role": "user",
        "content": "Generate 2 queries for the {toolName} tool of the {industry} industry"
    }
]
