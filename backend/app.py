from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from celery import Celery
from celery.result import AsyncResult
import subprocess
import time

app = Flask(__name__)
CORS(app)

app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

UPLOAD_DIR = os.path.join(os.getcwd(), 'uploads')
RENDERS_DIR = os.path.join(os.getcwd(), 'renders')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file.save(save_path)
    task = process_blender_task.apply_async(args=[save_path])
    return jsonify({'task_id': task.id}), 202

@app.route('/status/<task_id>', methods=['GET'])
def task_status(task_id):
    task_result = AsyncResult(task_id, app=celery)
    status = task_result.status
    if status == 'SUCCESS':
        return jsonify({
            'status': 'completed', 
            'file_paths': [f"/renders/{file}" for file in task_result.result]
        })
    elif status == 'PENDING':
        return jsonify({'status': 'pending'}), 202
    elif status == 'FAILURE':
        return jsonify({'status': 'failed', 'error': str(task_result.info)}), 500
    return jsonify({'status': 'unknown'}), 400

# @app.route('/renders/<path:filename>')
# def serve_rendered_file(filename):
#     # Check if the file exists in the directory before serving
#     full_path = os.path.join(RENDERS_DIR, filename)
#     if not os.path.exists(full_path):
#         print(f"File not found: {full_path}")  # Debug print to confirm file existence
#         return "File not found", 404
#     return send_from_directory(RENDERS_DIR, filename)

@app.route('/renders/<path:filename>')
def serve_rendered_file(filename):
    return send_from_directory(RENDERS_DIR, filename)


@celery.task(bind=True)
def process_blender_task(self, file_path):
    try:
        output_dir = RENDERS_DIR
        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(file_path))[0]

        subprocess.run([
            'blender', '-b', 'scripts/gateRenderer2.blend',
            '-P', 'scripts/gateRenderer.py', '--', file_path
        ], check=True)

        output_files = [f"{base_name}_rendered_{i}.jpg" for i in range(5)]
        output_paths = [os.path.join(output_dir, filename) for filename in output_files]

        existing_files = [path for path in output_paths if os.path.exists(path)]
        print("Expected output paths:", output_paths)  # Debug output
        print("Existing files found:", existing_files)  # Debug output

        if len(existing_files) != len(output_paths):
            missing_files = set(output_paths) - set(existing_files)
            print("Missing files:", missing_files)
            raise FileNotFoundError("Not all expected render output files were found.")

        return [f"{os.path.basename(path)}" for path in existing_files]
    except Exception as e:
        print("Error in process_blender_task:", e)
        raise self.retry(exc=e)
    
@app.route('/renders/<path:filename>')
def download_file(filename):
    return send_from_directory(
        directory= RENDERS_DIR,
        path=filename,
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(port=5001, debug=True)
