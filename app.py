from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import time
import logging
from threading import Thread

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

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

@app.route("/")
def index():
    return render_template("index.html")

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
        output_path = convert_json_to_excel(file_path, OUTPUT_FOLDER)
        
        # Delete uploaded file immediately after conversion
        try:
            os.remove(file_path)
        except Exception as e:
            logging.warning(f"Error deleting uploaded file: {str(e)}")

        if output_path.startswith("Error"):
            return jsonify({"error": output_path}), 400
            
        return jsonify({
            "files": [{
                "filename": os.path.basename(output_path),
                "download_url": f"/download/{os.path.basename(output_path)}"
            }]
        })
        
    except Exception as e:
        logging.error(f"Processing error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/download/<filename>")
def download_file(filename):
    safe_filename = secure_filename(filename)
    filepath = os.path.join(OUTPUT_FOLDER, safe_filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)