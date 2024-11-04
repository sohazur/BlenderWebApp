import bpy
import bpy_extras
import random
import math
from mathutils import Vector, Euler
import os
import sys

# Get the file path passed from the command line (set by Flask)
file_path = sys.argv[-1]
base_name = os.path.splitext(os.path.basename(file_path))[0]
output_path_template = os.path.join(os.getcwd(), 'renders', f"{base_name}_rendered_{{}}.jpg")

# Clear existing objects in the scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Manual import of OBJ file (enhanced to handle complex face definitions)
try:
    # Manually reading the .obj file
    with open(file_path, 'r') as obj_file:
        lines = obj_file.readlines()
        
    verts = []
    faces = []
    
    for line in lines:
        if line.startswith('v '):
            parts = line.split()
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif line.startswith('f '):
            parts = line.split()
            face = []
            for part in parts[1:]:
                indices = part.split('/')
                vertex_index = int(indices[0]) - 1  # Convert 1-based index to 0-based
                face.append(vertex_index)
            faces.append(tuple(face))
    
    # Create a new mesh and object
    mesh = bpy.data.meshes.new(name="ImportedMesh")
    obj = bpy.data.objects.new(name="ImportedOBJ", object_data=mesh)
    
    for obj in bpy.data.objects:
        print(f"Object: {obj.name}, Type: {obj.type}")
    
    # Link object to scene
    bpy.context.collection.objects.link(obj)
    
    # Create the mesh from vertices and faces
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    imported_obj = obj
    print(f"Successfully manually imported OBJ file: {file_path}")
except Exception as e:
    print(f"Failed to manually import OBJ file: {e}")
    sys.exit(1)

# Function to calculate the center of the bounding box of an object
def get_object_center(obj):
    local_bbox_center = 0.125 * sum((Vector(corner) for corner in obj.bound_box), Vector())
    global_bbox_center = obj.matrix_world @ local_bbox_center
    return global_bbox_center

# Function to calculate the coordinates of bounding box corners in camera space
def get_bbox_in_camera_view(cam, obj):
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    scene = bpy.context.scene
    bbox_2d = []

    for corner in bbox_corners:
        co_ndc = bpy_extras.object_utils.world_to_camera_view(scene, cam, corner)
        # Ensure coordinates are within 0-1 bounds
        co_ndc.x = max(0, min(co_ndc.x, 1))
        co_ndc.y = max(0, min(co_ndc.y, 1))
        bbox_2d.append((co_ndc.x, co_ndc.y))

    if not bbox_2d:
        return None  # Object not visible in camera

    # Find min and max values (xmin, ymin) and (xmax, ymax)
    min_x = min([coord[0] for coord in bbox_2d])
    max_x = max([coord[0] for coord in bbox_2d])
    min_y = min([coord[1] for coord in bbox_2d])
    max_y = max([coord[1] for coord in bbox_2d])

    # Normalized coordinates for center, width, and height
    x_center = (min_x + max_x) / 2
    y_center = (min_y + max_y) / 2
    width = max_x - min_x
    height = max_y - min_y

    return (x_center, y_center, width, height)

# Function to create a .txt file with YOLO labels
def create_yolo_label_file(output_image_path, cam, obj, class_id=0):
    bbox = get_bbox_in_camera_view(cam, obj)
    if bbox is None:
        print("Object not visible in camera.")
        return

    x_center, y_center, width, height = bbox
    txt_output_path = output_image_path.replace('.jpg', '.txt')
    with open(txt_output_path, 'w') as f:
        f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")
    print(f"YOLO label file saved: {txt_output_path}")

# Function to add point lights
def add_lights():
    for light in bpy.data.objects:
        if light.type == 'LIGHT':
            bpy.data.objects.remove(light)

    for i in range(2):
        light_data = bpy.data.lights.new(name=f"PointLight_{i}", type='POINT')
        light_object = bpy.data.objects.new(name=f"PointLight_{i}", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        light_object.location = (random.uniform(-100, 100), random.uniform(-100, 100), random.uniform(0, 250))
        light_data.energy = random.uniform(2000, 10000)

# Function to add ambient light using an environment texture
def add_ambient_light(texture_path):
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    env_texture_node = world.node_tree.nodes.new(type="ShaderNodeTexEnvironment")
    env_texture_node.image = bpy.data.images.load(texture_path)
    bg_node = world.node_tree.nodes.new(type="ShaderNodeBackground")
    world.node_tree.links.new(env_texture_node.outputs[0], bg_node.inputs[0])
    bg_node.inputs[1].default_value = 1.0
    output_node = world.node_tree.nodes.get("World Output") or world.node_tree.nodes.new(type="ShaderNodeOutputWorld")
    world.node_tree.links.new(bg_node.outputs[0], output_node.inputs[0])

# Add and configure the camera
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam_data.lens = 12
cam_data.clip_end = 5000

# Function to generate random camera positions
def random_camera_position(radius_range, angle_range):
    radius = random.uniform(*radius_range)
    theta_ranges = [(0, 80), (100, 260), (280, 360)]
    selected_range = random.choice(theta_ranges)
    theta = random.uniform(math.radians(selected_range[0]), math.radians(selected_range[1]))
    phi = random.uniform(math.pi / 2 - 0.35, math.pi / 2 + 0.35)
    x = radius * math.sin(phi) * math.cos(theta)
    y = radius * math.sin(phi) * math.sin(theta)
    z = radius * math.cos(phi)
    return (x, y, z)

# Function to randomly rotate the object
def random_object_rotation(obj):
    obj.rotation_euler = Euler((
        random.uniform(0, 2 * math.pi),
        random.uniform(0, 2 * math.pi),
        random.uniform(0, 2 * math.pi)
    ), 'XYZ')

# Render settings
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.device = 'CPU'
bpy.context.scene.render.resolution_x = 640
bpy.context.scene.render.resolution_y = 640
bpy.context.scene.cycles.samples = 128
bpy.context.scene.render.image_settings.file_format = 'JPEG'

# Number of images to render
num_images = 5

# Set texture folder relative to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
texture_folder = os.path.join(script_dir, 'textures')

# Ensure the directory exists
if not os.path.exists(texture_folder):
    print(f"Textures folder not found: {texture_folder}")
    sys.exit(1)

texture_files = [f for f in os.listdir(texture_folder) if f.endswith('.exr')]

for i in range(num_images):
    add_lights()
    texture_path = os.path.join(texture_folder, random.choice(texture_files))
    add_ambient_light(texture_path)
    cam.location = random_camera_position(radius_range=(450, 1500), angle_range=(0, 2 * math.pi))
    random_object_rotation(imported_obj)  # Rotate the object
    obj_center = get_object_center(imported_obj)
    direction = obj_center - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.render.filepath = output_path_template.format(i)
    
    try:
        bpy.ops.render.render(write_still=True)
        print(f"Rendered: {output_path_template.format(i)}")
        create_yolo_label_file(output_image_path=output_path_template.format(i), cam=cam, obj=imported_obj, class_id=0)
    except Exception as e:
        print(f"Error rendering image {i}: {e}")
