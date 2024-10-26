from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess

app = Flask(__name__)
CORS(app)  # Allows React to access the backend

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    save_path = os.path.join('uploads', file.filename)
    file.save(save_path)

    # Run Blender in headless mode with the gateRenderer.py script
    subprocess.run(['blender', '-b', 'scripts/gateRenderer2.blend', '-P', 'scripts/gateRenderer.py'])
    return jsonify({'status': 'Processing started'})

if __name__ == '__main__':
    app.run(debug=True)
