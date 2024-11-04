# BlenderWebApp

BlenderWebApp is a project that processes 3D `.obj` files, applies textures, and renders images using Blender. The rendered images and their corresponding YOLO annotations are made available through a web interface.

## Features

- Upload `.obj` files
- Automatically apply textures to 3D models
- Render images from multiple angles
- Download rendered images and annotations
- Web interface for easy access

## Prerequisites

Before getting started, ensure you have the following installed:

1. **Python 3.x** (preferably Python 3.8 or higher)
2. **Blender** (version 4.2.3 LTS or later)
3. **Node.js** and **npm** (for running the frontend)
4. **Redis** (for managing Celery tasks)
5. **Git** (for cloning the repository)

## Repository Structure

````plaintext
BlenderWebApp/
├── backend/
│   ├── app.py               # Flask backend
│   ├── gateRenderer.py      # Blender script for rendering
│   ├── uploads/             # Folder for uploaded .obj files
│   ├── renders/             # Folder for rendered images
│   └── textures/            # Folder for texture files
└── frontend/
    ├── public/              # Public static files
    ├── src/
    │   └── App.js           # Main React app
    ├── package.json         # Frontend dependencies
    ├── README.md            # Frontend-specific readme
    └── requirements.txt     # Python dependencies

## Installation

### Clone the Repository

```bash
git clone https://github.com/sohazur/BlenderWebApp.git
cd BlenderWebApp
````

## Backend Setup

### 1. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install required packages:

```bash
pip install -r requirements.txt
```

### 3. Ensure Redis is running:

- On Linux/MacOS:

```bash
redis-server
```

- On Windows, you may need to download and install Redis separately.

### 4. Start the Celery worker:

Open a new terminal in the BlenderWebApp directory and activate the virtual environment:

```bash
source venv/bin/activate
```

Then start the worker:

```bash
celery -A backend.app.celery worker --loglevel=info
```

### 5. Run the Flask backend:

In another terminal, navigate to the BlenderWebApp/backend directory, activate the virtual environment, and run:

```bash
flask run --port=5001
```

The backend will start on http://localhost:5001.

## Frontend Setup

### 1. Navigate to the frontend directory:

```bash
cd frontend
```

### 2. Install the dependencies:

```bash
npm install
```

### 3. Start the frontend development server:

```bash
npm start
```

The frontend will start on http://localhost:3000.

## Using the Application

### 1. Open the frontend:

Navigate to http://localhost:3000 in your web browser.

### 2. Upload an OBJ file:

Use the upload button to select and upload an OBJ file.

### 3. Rendering Process:

After uploading, the backend processes the file. You can see the progress in the UI. Once completed, download links for the rendered images will appear.

### 4. Download Rendered Images:

Click on the download links to save the rendered images to your local machine.
