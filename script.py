import pandas as pd
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"

def flatten_json(nested_json, parent_key="", sep="_"):
    items = []
    if isinstance(nested_json, dict):
        for k, v in nested_json.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, (dict, list)):
                items.extend(flatten_json(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
    elif isinstance(nested_json, list):
        for i, element in enumerate(nested_json):
            items.extend(flatten_json(element, f"{parent_key}{sep}{i}", sep=sep).items())
    return dict(items)

def convert_json_to_excel(json_filepath, excel_path):
    try:
        # Validate input file path
        if not isinstance(json_filepath, str) or not json_filepath:
            raise ValueError("JSON file path must be a non-empty string.")
        if not os.path.isfile(json_filepath):
            raise FileNotFoundError(f"File not found: {json_filepath}")

        # Validate output file path
        if not isinstance(excel_path, str) or not excel_path:
            raise ValueError("Excel file path must be a non-empty string.")

        with open(json_filepath, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format in {json_filepath}: {e}")

        # Validate JSON structure
        if isinstance(data, dict):
            data = data.get("data", [data]) if "data" in data else [data]
        if not isinstance(data, list) or not data:
            raise ValueError(f"JSON data in {json_filepath} must be a non-empty array.")

        # Process data
        flattened_data = [flatten_json(record) for record in data]
        try:
            df = pd.DataFrame(flattened_data)
        except Exception as e:
            raise ValueError(f"Error creating DataFrame from {json_filepath}: {e}")

        if df.empty:
            raise ValueError(f"No valid data found in {json_filepath} after flattening.")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(excel_path), exist_ok=True)

        # Save Excel file
        try:
            df.to_excel(excel_path, index=False, engine="openpyxl")
        except Exception as e:
            raise OSError(f"Failed to write Excel file {excel_path}: {e}")

        # Verify output file
        if not os.path.exists(excel_path):
            raise OSError(f"Failed to create Excel file at {excel_path}")

        # Cleanup: Remove the uploaded JSON file after successful conversion
        os.remove(json_filepath)

        logging.info(f"Conversion successful: {json_filepath} -> {excel_path}")
        return True, excel_path

    except (FileNotFoundError, ValueError, OSError) as e:
        logging.error(f"Conversion error: {e}")
        return False, str(e)
    except Exception as e:
        logging.error(f"Unexpected conversion error: {e}")
        return False, str(e)

def delete_converted_file(filepath):
    """Deletes the converted file after it has been downloaded."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logging.info(f"Deleted file: {filepath}")
    except Exception as e:
        logging.error(f"Error deleting file {filepath}: {e}")
