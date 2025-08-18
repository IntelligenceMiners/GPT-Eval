import jsonlines
from collections import defaultdict
import os

def merge_files(file_paths):
    industry_data = defaultdict(list)

    # Read each file and group by industry_id
    for file_path in file_paths:
        print(f"Reading file: {file_path}")
        with jsonlines.open(file_path, 'r') as reader:
            file_data_found = False  # Flag to track if data is found in the file
            for obj in reader:
                # Print the raw content of each object being read
                print(f"Raw data from {file_path}: {obj}")
                
                industry_id = obj.get("IndustryID")
                scenario_id = obj.get("ScenarioID")
                
                # Ensure IndustryID is treated as an integer
                if industry_id is not None:
                    industry_id = int(industry_id)  # Convert to integer if not None

                if industry_id is not None and scenario_id is not None:
                    file_data_found = True  # Mark that data was found
                    industry_data[industry_id].append((str(scenario_id), obj))
                else:
                    print(f"Skipping object without valid IndustryID or ScenarioID: {obj}")

            if not file_data_found:
                print(f"No valid data found in {file_path}")  # Print if no data found

    # Sort each group by scenario_id and merge the data
    merged_data = []
    for industry_id in sorted(industry_data.keys()):  # Sorting by integer IndustryID
        # Sort by scenario_id for each industry group
        industry_data[industry_id].sort(key=lambda x: x[0])

        query_counter = 1
        current_scenario = None
        for scenario_id, data in industry_data[industry_id]:
            if scenario_id != current_scenario:
                current_scenario = scenario_id
                query_counter = 1
            data["QueryId"] = f"{industry_id}_{scenario_id}_{query_counter}"
            query_counter += 1

            # Rebuild the dictionary to place QueryId after ScenarioID
            reordered_data = {
                "IndustryID": data["IndustryID"],
                "ScenarioID": data["ScenarioID"],
                "QueryId": data["QueryId"]
            }

            # Add the rest of the fields
            for key in data:
                if key not in reordered_data:
                    reordered_data[key] = data[key]

            merged_data.append(reordered_data)

    return merged_data

def save_merged_data(merged_data, output_file):
    with jsonlines.open(output_file, 'w') as writer:
        writer.write_all(merged_data)

# List of all the file paths
file_paths = [
    r'C:\Users\b-fkabir\Desktop\UniveralToolKits\Result\QuerySet\final01.jsonl',
    r'C:\Users\b-fkabir\Desktop\UniveralToolKits\Result\QuerySet\final02.jsonl',
    r'C:\Users\b-fkabir\Desktop\UniveralToolKits\Result\QuerySet\final03.jsonl',
    r'C:\Users\b-fkabir\Desktop\UniveralToolKits\Result\QuerySet\final04.jsonl',
    r'C:\Users\b-fkabir\Desktop\UniveralToolKits\Result\QuerySet\final05.jsonl',
    r'C:\Users\b-fkabir\Desktop\UniveralToolKits\Result\QuerySet\final06.jsonl',
    r'C:\Users\b-fkabir\Desktop\UniveralToolKits\Result\QuerySet\final05prime.jsonl',
    r'C:\Users\b-fkabir\Desktop\UniveralToolKits\Result\QuerySet\final07.jsonl',
    r'C:\Users\b-fkabir\Desktop\UniveralToolKits\Result\QuerySet\final08.jsonl',
    
]

# Merge the files
merged_data = merge_files(file_paths)

# Save the merged data to a new file
output_file = r'C:\Users\b-fkabir\Desktop\UniveralToolKits\Result\QuerySet\merged_data.jsonl'
save_merged_data(merged_data, output_file)

print(f'Merged data saved to {output_file}')
