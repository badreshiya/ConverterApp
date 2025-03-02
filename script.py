import pandas as pd
import os
import json

def flatten_json(nested_json, parent_key="", sep="_"):
    items = []
    if isinstance(nested_json, dict):
        for key, value in nested_json.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, (dict, list)):
                items.extend(flatten_json(value, new_key, sep=sep).items())
            else:
                items.append((new_key, value))
    elif isinstance(nested_json, list):
        for i, element in enumerate(nested_json):
            items.extend(flatten_json(element, f"{parent_key}{sep}{i}", sep=sep).items())
    return dict(items)

def convert_json_to_excel(json_filepath, output_folder):
    try:
        # Validate file
        if not os.path.isfile(json_filepath):
            return "File not found"
            
        with open(json_filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
            
        # Validate JSON structure
        if isinstance(data, dict):
            data = data.get("data", [data]) if "data" in data else [data]
            
        if not isinstance(data, list) or len(data) == 0:
            return "JSON root must be a non-empty array"
            
        # Process data
        flattened_data = [flatten_json(record) for record in data]
        df = pd.DataFrame(flattened_data)
        
        if df.empty:
            return "No valid data found in JSON"
            
        # Save Excel
        os.makedirs(output_folder, exist_ok=True)
        output_filename = os.path.basename(json_filepath).replace(".json", ".xlsx")
        excel_path = os.path.join(output_folder, output_filename)
        
        df.to_excel(excel_path, index=False, engine="openpyxl")
        return excel_path
        
    except json.JSONDecodeError:
        return "Invalid JSON format"
    except Exception as e:
        return f"Processing error: {str(e)}"