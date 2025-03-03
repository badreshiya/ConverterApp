from flask import Flask, request, render_template, jsonify
import os
import boto3
import pandas as pd
import json
from werkzeug.utils import secure_filename
import logging

application = Flask(__name__)

# Configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"json"}
S3_BUCKET = "your-s3-bucket-name"
S3_REGION = "us-east-1"
application.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# AWS S3 Client
s3_client = boto3.client("s3")

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def json_to_excel(json_path, excel_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            raise ValueError("Invalid JSON format. Root should be a list of objects.")

        df = pd.DataFrame(data)
        df.to_excel(excel_path, index=False)
        return True
    except Exception as e:
        logging.error(f"Error processing JSON: {str(e)}")
        return False

@application.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            json_path = os.path.join(application.config["UPLOAD_FOLDER"], filename)
            file.save(json_path)
            excel_path = json_path.replace(".json", ".xlsx")
            
            if json_to_excel(json_path, excel_path):
                s3_key = f"converted/{os.path.basename(excel_path)}"
                s3_client.upload_file(excel_path, S3_BUCKET, s3_key)
                file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
                return jsonify({"success": True, "download_url": file_url})
            else:
                return jsonify({"error": "Failed to convert JSON to Excel"}), 500

    return render_template("index.html")

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000)
