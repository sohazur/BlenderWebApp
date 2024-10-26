import bpy
import bpy_extras
import random
import math
from mathutils import Vector
import os

obj_name = "gateModel"
obj = bpy.data.objects.get(obj_name)

if obj is None:
    raise ValueError(f"Obiekt o nazwie '{obj_name}' nie został znaleziony.")

# Funkcja obliczająca środek bounding box obiektu
def get_object_center(obj):
    local_bbox_center = 0.125 * sum((Vector(corner) for corner in obj.bound_box), Vector())
    global_bbox_center = obj.matrix_world @ local_bbox_center
    return global_bbox_center

# Funkcja obliczająca współrzędne narożników bounding boxa w przestrzeni kamery
def get_bbox_in_camera_view(cam, obj):
    # Pobierz bounding box obiektu w przestrzeni świata
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

    # Przekonwertuj narożniki do przestrzeni kamery
    scene = bpy.context.scene
    camera_matrix = cam.matrix_world.inverted()

    # Lista na współrzędne 2D
    bbox_2d = []

    for corner in bbox_corners:
        co_local = camera_matrix @ corner
        co_ndc = bpy_extras.object_utils.world_to_camera_view(scene, cam, corner)
        
        # Upewnij się, że współrzędne są w granicach 0-1
        if co_ndc.x > 1: co_ndc.x = 1
        elif co_ndc.x < 0: co_ndc.x = 0
        if co_ndc.y > 1: co_ndc.y = 1
        elif co_ndc.y < 0: co_ndc.y = 0

        bbox_2d.append((co_ndc.x, co_ndc.y))

    if not bbox_2d:
        return None  # Obiekt nie jest widoczny w kamerze

    # Znajdź minimalne i maksymalne wartości (xmin, ymin) oraz (xmax, ymax)
    min_x = min([coord[0] for coord in bbox_2d])
    max_x = max([coord[0] for coord in bbox_2d])
    min_y = min([coord[1] for coord in bbox_2d])
    max_y = max([coord[1] for coord in bbox_2d])

    # Znormalizowane współrzędne środka, szerokości i wysokości
    x_center = (min_x + max_x) / 2
    y_center = (min_y + max_y) / 2
    width = max_x - min_x
    height = max_y - min_y

    return (x_center, y_center, width, height)

# Funkcja do tworzenia pliku .txt z etykietami w formacie YOLO
def create_yolo_label_file(output_image_path, cam, obj, class_id=0):
    bbox = get_bbox_in_camera_view(cam, obj)
    
    if bbox is None:
        print("Obiekt nie jest widoczny w kamerze.")
        return

    x_center, y_center, width, height = bbox

    # Tworzenie ścieżki do pliku tekstowego
    txt_output_path = output_image_path.replace('.jpg', '.txt')
    
    with open(txt_output_path, 'w') as f:
        # Format: <class_id> <x_center> <y_center> <width> <height>
        f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")
    
    print(f"Plik txt został zapisany: {txt_output_path}")


# Funkcja do dodawania punktowych źródeł światła
def add_lights():
    # Usuń istniejące źródła światła
    for light in bpy.data.objects:
        if light.type == 'LIGHT':
            bpy.data.objects.remove(light)

    # Dodaj 2 nowe źródła światła
    for i in range(2):
        light_data = bpy.data.lights.new(name=f"PointLight_{i}", type='POINT')
        light_object = bpy.data.objects.new(name=f"PointLight_{i}", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        
        # Losowe położenie i moc światła
        light_object.location = (random.uniform(-100, 100), random.uniform(-100,100), random.uniform(0, 250))
        light_data.energy = random.uniform(2000, 10000)  # Zmienna moc światła

# Funkcja do dodawania ambient light (oświetlenie środowiskowe)
def add_ambient_light(texture_path):
    # Sprawdź, czy istnieje obiekt świata
    if bpy.context.scene.world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    else:
        world = bpy.context.scene.world

    # Ustawienia oświetlenia w scenie
    world.use_nodes = True
    
    # Upewnij się, że jest drzewo węzłów
    if world.node_tree is None:
        world.node_tree = bpy.data.node_groups.new("WorldNodeTree", 'ShaderNodeTree')

    # Dodaj węzeł tekstury
    env_texture_node = world.node_tree.nodes.new(type="ShaderNodeTexEnvironment")
    env_texture_node.image = bpy.data.images.load(texture_path)  # Wczytaj teksturę
    env_texture_node.location = (-300, 0)  # Ustawienie pozycji węzła

    # Ustaw węzeł Background
    bg_node = world.node_tree.nodes.new(type="ShaderNodeBackground")

    # Połącz węzeł tekstury z węzłem Background
    world.node_tree.links.new(env_texture_node.outputs[0], bg_node.inputs[0])

    # Ustawienia intensywności
    bg_node.inputs[1].default_value = 1.0

    # Węzeł Output
    output_node = world.node_tree.nodes.get("World Output")
    if output_node is None:
        output_node = world.node_tree.nodes.new(type="ShaderNodeOutputWorld")

    # Podłącz węzeł Background do węzła Output
    world.node_tree.links.new(bg_node.outputs[0], output_node.inputs[0])

# Dodaj kamerę
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam

cam_data.lens = 12

cam_data.clip_end = 5000  # Zmienny zasięg widoczności kamery

# Funkcja generująca losowe położenie kamery z ograniczeniem odchylenia o 20 stopni od poziomu
def random_camera_position(radius_range, angle_range):
    radius = random.uniform(*radius_range)
    # Zakresy dla kąta theta
    theta_ranges = [(0, 80), (100, 260), (280, 360)]
    
    # Wybierz losowy zakres
    selected_range = random.choice(theta_ranges)
    # Wybierz losowy kąt w wybranym zakresie
    theta = random.uniform(math.radians(selected_range[0]), math.radians(selected_range[1]))
    
    # Kąt pionowy phi odchylony o maksymalnie 20 stopni od poziomu
    phi = random.uniform(math.pi / 2 - 0.35, math.pi / 2 + 0.35)
    
    x = radius * math.sin(phi) * math.cos(theta)
    y = radius * math.sin(phi) * math.sin(theta)
    z = radius * math.cos(phi)
    return (x, y, z)

# Ustawienia renderowania
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.device = 'CPU'
bpy.context.scene.render.resolution_x = 640
bpy.context.scene.render.resolution_y = 640
bpy.context.scene.cycles.samples = 128

bpy.context.scene.render.image_settings.file_format = 'JPEG'

# Liczba obrazów do renderowania
num_images = 5
output_path = "/Users/sohazur/Desktop/a2rl/BlenderWebApp/backend/renders/gateRenderTest43_{}.jpg"
texture_folder = "/Users/sohazur/Desktop/a2rl/BlenderWebApp/backend/scripts/textures/"
texture_files = [f for f in os.listdir(texture_folder) if f.endswith('.exr')]

for i in range(num_images):
    # Dodaj światła przed każdym renderem
    add_lights()
    
    # Wybierz losową teksturę
    texture_path = os.path.join(texture_folder, random.choice(texture_files))
    add_ambient_light(texture_path)  # Dodaj ambient light z wybraną teksturą

    cam.location = random_camera_position(
        radius_range=(450, 1500),
        angle_range=(0, 2 * math.pi)
    )
    
    # Oblicz środek obiektu
    obj_center = get_object_center(obj)
    
    # Skieruj kamerę na środek obiektu
    direction = obj_center - cam.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam.rotation_euler = rot_quat.to_euler()
    
    # Ustaw ścieżkę wyjściową
    bpy.context.scene.render.filepath = output_path.format(i)

    # Renderuj obraz
    try:
        bpy.ops.render.render(write_still=True)
        print(f"Rendered: {output_path.format(i)}")
    # Tworzenie pliku txt z etykietą YOLO  
        create_yolo_label_file(output_image_path=output_path.format(i), cam=cam, obj=obj, class_id=0)
    except Exception as e:
        print(f"Error rendering image {i}: {e}")