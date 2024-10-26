from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess

app = Flask(__name__)
# Allow CORS only from your frontend origin
CORS(app, resources={r"/upload": {"origins": "http://localhost:3000"}})

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        save_path = os.path.join('uploads', file.filename)
        file.save(save_path)

        # Run Blender in headless mode with the gateRenderer.py script
        subprocess.run(['blender', '-b', 'scripts/gateRenderer2.blend', '-P', 'scripts/gateRenderer.py'])
        return jsonify({'status': 'Processing started'})
    except Exception as e:
        print("Error during file upload:", e)  # Log the error to the terminal
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
