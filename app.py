from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import pandas as pd
import json
import os
import uuid
import time
import logging
from threading import Thread
import shutil

app = Flask(__name__)
ALLOWED_EXTENSIONS = {'json'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE # Ensure consistency

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
REPOSITORY_FOLDER = "repository_data" # New folder for persistent files
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(REPOSITORY_FOLDER, exist_ok=True)

file_metadata = {} # In-memory dictionary to track file metadata

# File cleanup thread (uploads only)
def clean_old_files():
    while True:
        time.sleep(3600)  # Run hourly
        now = time.time()
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.getmtime(filepath) < now - 3600:
                try:
                    os.remove(filepath)
                except Exception as e:
                    logging.warning(f"Error deleting {filepath}: {e}")

# Start cleanup thread
cleaner = Thread(target=clean_old_files, daemon=True)
cleaner.start()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', error='No file part')
        file = request.files['file']
        if file.filename == '':
            return render_template('index.html', error='No selected file')
        if file and allowed_file(file.filename):
            if len(file.read()) > MAX_FILE_SIZE:
                return render_template('index.html', error='File size exceeded')
            file.seek(0) #reset file pointer after read.
            try:
                data = json.load(file)
                df = pd.DataFrame(data)
                excel_filename = f"{uuid.uuid4()}.xlsx" #unique file name.
                excel_path = os.path.join(app.root_path, excel_filename)
                df.to_excel(excel_path, index=False)
                return send_file(excel_path, as_attachment=True, download_name='converted.xlsx')
            except json.JSONDecodeError:
                return render_template('index.html', error='Invalid JSON file')
            except Exception as e:
                return render_template('index.html', error=f'An error occurred: {e}')
        else:
            return render_template('index.html', error='Invalid file type')
    return render_template('index.html')

@app.route("/upload", methods=["POST"])
def upload_files():
    if "jsonFiles" not in request.files:
        return jsonify({"error": "No file selected"}), 400

    file = request.files["jsonFiles"]
    if not file or file.filename == "":
        return jsonify({"error": "Empty file"}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".json"):
        return jsonify({"error": "Only JSON files allowed"}), 400

    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        from script import convert_json_to_excel
        output_filename = os.path.basename(convert_json_to_excel(file_path, OUTPUT_FOLDER))
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Copy to repository
        repository_path = os.path.join(REPOSITORY_FOLDER, output_filename)
        shutil.copy2(output_path, repository_path)

        # Delete from output folder
        os.remove(output_path)

        # Delete uploaded file immediately after conversion
        try:
            os.remove(file_path)
        except Exception as e:
            logging.warning(f"Error deleting uploaded file: {str(e)}")

        expiration_time = time.time() + 120 # 2 minutes expiration
        file_metadata[output_filename] = expiration_time

        return jsonify({
            "files": [{
                "filename": output_filename,
                "download_url": f"/download/{output_filename}"
            }]
        })

    except Exception as e:
        logging.error(f"Processing error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/download/<filename>")
def download_file(filename):
    safe_filename = secure_filename(filename)
    filepath = os.path.join(REPOSITORY_FOLDER, safe_filename) # changed to repository
    if safe_filename in file_metadata:
        if time.time() < file_metadata[safe_filename]:
            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            del file_metadata[safe_filename] #remove metadata
            return jsonify({"error": "Download link expired"}), 404
    return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)