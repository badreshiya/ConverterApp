import os
import json
import pandas as pd
from flask import Flask, request, render_template, send_file, jsonify
from dotenv import load_dotenv
import logging
import boto3
from botocore.exceptions import ClientError
from datetime import datetime  # Import datetime

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

application = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'json'}
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_REGION = os.environ.get('S3_REGION_NAME')
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Initialize S3 client
s3 = boto3.client('s3')

if not S3_BUCKET:
    logging.error("S3_BUCKET environment variable is not set or is empty.")
    raise ValueError("S3 bucket configuration is missing.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_json_to_excel(json_filepath):
    """Converts a JSON file to an Excel file (xlsx).  Handles file opening/closing.
       Now takes file path, opens and closes file *within* the function.

    Args:
        json_filepath: Path to the JSON file.

    Returns:
        The filepath of the created Excel file, or None if an error occurred.
    """
    try:
       with open(json_filepath, 'r', encoding='utf-8') as f:
          try:
               data = json.load(f)
          except json.JSONDecodeError as e:
            logging.error(f"JSONDecodeError: Invalid JSON format {e}") # Log specific JSON error
            logging.error(f"File causing JSONDecodeError: {json_filepath}") # Log file path
            return None

        #check data key exist
       if not isinstance(data, list):
          if isinstance(data, dict) and 'data' in data:
             data = data['data']
             if not isinstance(data, list):
               raise ValueError("JSON 'data' field must contain a list.")
          else:
              raise ValueError("Invalid JSON data structure.")

       df = pd.DataFrame(data)
       excel_filepath = json_filepath.replace('.json', '.xlsx')
       df.to_excel(excel_filepath, index=False, engine='openpyxl')  # Specify openpyxl
       return excel_filepath

    except Exception as e:
        logging.error(f"Error converting JSON to Excel: {e}")
        return None


def upload_to_s3(file_path, bucket_name, s3_prefix):
    """Uploads a file to an S3 bucket.

    Args:
        file_path: The local path to the file to upload.
        bucket_name: The name of the S3 bucket.
        object_name: The desired S3 object name (key).

    Returns:
        The S3 URL of the uploaded object, or None if the upload failed.
    """
    try:
        file_name = os.path.basename(file_path)
        s3_key = f"{s3_prefix}/{file_name}"  # Corrected: Use provided prefix
        s3.upload_file(file_path, bucket_name, s3_key)
        s3_url = f"https://{bucket_name}.s3.{S3_REGION}.amazonaws.com/{s3_key}"  # Full URL
        logging.info(f"File uploaded to S3: {s3_url}")
        return s3_url
    except ClientError as e:
        logging.error(f"S3 upload failed: {e}")
        return None
    except FileNotFoundError:  # Handle file not found
        logging.error(f"File not found for S3 upload: {file_path}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during S3 upload: {e}")
        return None


@application.route('/', methods=['GET', 'POST'])
def upload_file():
    """Handles file uploads and conversion to Excel."""
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
             # Generate a unique filename to avoid collisions
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"  # Add timestamp to the filename

            filepath = os.path.join(application.config['UPLOAD_FOLDER'], filename)

            file.save(filepath)
            logging.info(f"File saved to {filepath}")

            excel_file = convert_json_to_excel(filepath)
            if excel_file:
                # Upload the EXCEL file to S3
                s3_url = upload_to_s3(excel_file, S3_BUCKET, "converted")  # Use "converted" prefix
                if s3_url:

                   # Delete the local Excel file *after* successful S3 upload
                   try:
                      os.remove(excel_file)
                      logging.info(f"Deleted local Excel file after S3 upload: {excel_file}")
                   except OSError as e:
                       logging.warning(f"Failed to delete local Excel file {excel_file}: {e}")

                   return jsonify({'message': 'File converted and uploaded successfully', 'download_url': s3_url}), 200
                else: # S3 upload failed
                    return jsonify({'error': 'File converted, but S3 upload failed'}), 500
            else:
              return jsonify({'error': 'Failed to convert JSON to Excel'}), 400
        else:
            return jsonify({'error': 'Invalid file type'}), 400 #Invalid file type

    return render_template('index.html')


@application.route('/download/<filename>')
def download_file(filename):
     #No need to create this route, as we are generating s3 url.
     pass

if __name__ == '__main__':
    # Ensure the S3_BUCKET is set.
    if not S3_BUCKET or not S3_REGION:
        raise ValueError("S3_BUCKET and S3_REGION_NAME environment variables must be set.")
    application.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))