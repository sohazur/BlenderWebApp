from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
from celery import Celery
from celery.result import AsyncResult

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Set up Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Initialize Celery with Flask app context
def make_celery(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'], broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    save_path = os.path.join('uploads', file.filename)
    file.save(save_path)

    # Start the rendering process in the background
    task = process_blender_task.apply_async(args=[save_path])
    return jsonify({'task_id': task.id}), 202

@app.route('/status/<task_id>')
def task_status(task_id):
    task_result = AsyncResult(task_id, app=celery)
    status = task_result.status
    if status == 'SUCCESS':
        return jsonify({'status': 'completed', 'result': task_result.result}), 200
    elif status == 'PENDING':
        return jsonify({'status': 'pending'}), 202
    elif status == 'FAILURE':
        return jsonify({'status': 'failed', 'error': str(task_result.info)}), 500
    return jsonify({'status': 'unknown'}), 400

@celery.task(bind=True)
def process_blender_task(self, file_path):
    try:
        # Run Blender in headless mode
        subprocess.run(['blender', '-b', 'scripts/gateRenderer2.blend', '-P', 'scripts/gateRenderer.py'])
        return "Rendering complete"
    except Exception as e:
        raise self.retry(exc=e)

if __name__ == '__main__':
    app.run(port=5001, debug=True)
