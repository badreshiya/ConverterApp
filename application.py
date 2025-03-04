import os
import json
import pandas as pd
from flask import Flask, request, render_template, send_file, jsonify, after_this_request
from dotenv import load_dotenv
import logging
from datetime import datetime
from script import convert_json_to_excel

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

application = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
ALLOWED_EXTENSIONS = {'json'}
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
application.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

# Ensure upload and converted folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@application.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@application.route('/upload', methods=['POST'])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        # Generate timestamped filename
        original_name = os.path.splitext(file.filename)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"{original_name}_{timestamp}.xlsx"
        excel_path = os.path.join(CONVERTED_FOLDER, excel_filename)

        # Save uploaded file temporarily
        upload_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(upload_path)

        # Convert using the script function
        success, result = convert_json_to_excel(upload_path, excel_path)

        if success:
            return jsonify({"file_path": f"/download/{excel_filename}"})
        return jsonify({"error": result}), 500

    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

@application.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(CONVERTED_FOLDER, filename)

    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return jsonify({'error': 'File not found'}), 404

    @after_this_request
    def cleanup(response):
        try:
            os.remove(file_path)
            logging.info(f"Deleted converted file: {file_path}")
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")
        return response

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename  # Preserve the timestamped filename
    )

if __name__ == '__main__':
    application.run(debug=True)