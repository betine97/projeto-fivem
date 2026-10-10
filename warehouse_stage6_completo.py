import bpy
import math
import random
from mathutils import Vector

# ============================================================
# INDUSTRIAL WAREHOUSE ENVIRONMENT — STAGE 6 / INDUSTRIAL SERVICES AND CEILING VENTS
# Blender 4.x / pure bpy / no external add-ons
# ============================================================
# Standalone environment: architecture, racks and Stage 5 visual props:
# shell + architecture + drain + doors + structural steel +
# electrical infrastructure + ventilation + ducting + fans +
# industrial lighting + procedural preview materials.
#
# All dimensions are in METERS.
# 1 Blender Unit = 1 meter.
# ============================================================

# ============================================================
# 01 CONFIG
# ============================================================

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Build mode --------------------------------------------------
REBUILD_COMPLETE_ENVIRONMENT = True
ROOT_COLLECTION_NAME = "ENV_WAREHOUSE_STAGE6"
LEGACY_ROOT_COLLECTIONS = (
    "ENV_WAREHOUSE_STAGE5",
    "ENV_WAREHOUSE_STAGE4",
    "ENV_WAREHOUSE_STAGE3",
    "ENV_WAREHOUSE_STAGE2",
    "ENV_WAREHOUSE_STAGE1",
    "WAREHOUSE_SHELL",
)

# Feature toggles ---------------------------------------------
CREATE_SHELL = True
CREATE_DOORS = True
CREATE_DRAIN = True
CREATE_WALL_RELIEF = True
CREATE_BEAMS = False
CREATE_TECHNICAL_RAILS = False
CREATE_ELECTRICAL = True
CREATE_CONDUITS = True
CREATE_VENTILATION = True
CREATE_MAIN_DUCT = True
CREATE_EXHAUST_FANS = True
CREATE_LIGHT_FIXTURES = True
CREATE_REAL_LIGHTS = True
CREATE_MATERIALS = True
CREATE_CEILING = True
CREATE_PREVIEW_CAMERA = False

# Room --------------------------------------------------------
ROOM_WIDTH = 8.00
ROOM_LENGTH = 12.00
WALL_HEIGHT = 3.60
WALL_THICKNESS = 0.20
FLOOR_THICKNESS = 0.20
CEILING_THICKNESS = 0.15

# Openings ----------------------------------------------------
BACK_DOOR_WIDTH = 1.10
BACK_DOOR_HEIGHT = 2.20
BACK_DOOR_X = 0.00

SIDE_DOOR_WIDTH = 1.10
SIDE_DOOR_HEIGHT = 2.20
SIDE_DOOR_Y = -3.60

FRONT_GATE_WIDTH = 3.20
FRONT_GATE_HEIGHT = 2.80
FRONT_GATE_X = 0.00

# Trims / frames ----------------------------------------------
DOOR_FRAME_WIDTH = 0.10
DOOR_FRAME_DEPTH = 0.10
GATE_FRAME_WIDTH = 0.14
GATE_FRAME_DEPTH = 0.14
DOOR_LEAF_THICKNESS = 0.055
DOOR_GAP = 0.022
THRESHOLD_HEIGHT = 0.025
THRESHOLD_DEPTH = 0.30
BASEBOARD_HEIGHT = 0.12
BASEBOARD_DEPTH = 0.045
WALL_RELIEF_WIDTH = 0.12
WALL_RELIEF_DEPTH = 0.045
TOP_WALL_BAND_HEIGHT = 0.10
TOP_WALL_BAND_DEPTH = 0.045

# Floor / drain -----------------------------------------------
DRAIN_WIDTH = 0.24
DRAIN_DEPTH = 0.045
DRAIN_FRONT_MARGIN = 0.40
DRAIN_BACK_MARGIN = 0.55
DRAIN_GRATE_MODULE_LENGTH = 0.90
DRAIN_GRATE_BAR_WIDTH = 0.018
DRAIN_GRATE_BAR_SPACING = 0.085
FLOOR_JOINT_WIDTH = 0.012
FLOOR_TRANSVERSE_JOINTS = (-2.75, 0.00, 2.75)
FLOOR_LONGITUDINAL_JOINTS = (-2.00, 2.00)

# Structural --------------------------------------------------
BEAM_WIDTH = 0.12
BEAM_HEIGHT = 0.18
BEAM_Y_POSITIONS = (-4.50, -1.50, 1.50, 4.50)
BEAM_Z = WALL_HEIGHT - 0.22
TECH_RAIL_X_POSITIONS = (-2.25, 2.25)
TECH_RAIL_HEIGHT = 0.07
TECH_RAIL_WIDTH = 0.07
TECH_RAIL_Z = WALL_HEIGHT - 0.38

# Electrical --------------------------------------------------
MAIN_PANEL_X = -1.55
MAIN_PANEL_Z = 1.80
MAIN_PANEL_WIDTH = 0.62
MAIN_PANEL_HEIGHT = 0.82
MAIN_PANEL_DEPTH = 0.12
JUNCTION_BOX_WIDTH = 0.28
JUNCTION_BOX_HEIGHT = 0.34
JUNCTION_BOX_DEPTH = 0.10
CONDUIT_RADIUS = 0.018
HIGH_CONDUIT_Z = 3.08
SIDE_CONDUIT_Z = 2.85

# Stage 3 duct system -----------------------------------------
DUCT_DIAMETER = 0.56
DUCT_RADIUS = DUCT_DIAMETER / 2.0
DUCT_CENTER_Y = ROOM_LENGTH / 2.0 - 0.31
DUCT_HEIGHT = 3.08
DUCT_MAIN_X_MIN = -2.60
DUCT_MAIN_X_MAX = 2.62
DUCT_SEGMENT_TARGET = 1.05
DUCT_RING_EXTRA_RADIUS = 0.022
DUCT_RING_LENGTH = 0.045
DUCT_ELBOW_SEGMENTS = 7
DUCT_SUPPORT_X = (-2.15, -0.80, 0.65, 2.05)

# Fans --------------------------------------------------------
FAN_DIAMETER = 0.84
FAN_DEPTH = 0.18
FAN_BLADE_COUNT = 6
FAN_GRILLE_RINGS = 4
FAN_LEFT_X = -3.15
FAN_RIGHT_X = 3.15
FAN_Z = 2.93
FAN_CENTER_Y = ROOM_LENGTH / 2.0 - 0.10

# Reference layout: two continuous side racks, three bays per rack.
CREATE_RACKS = True
RACK_DEPTH = 2.55
RACK_LENGTH = 7.40
RACK_HEIGHT = 2.05
RACK_WALL_CLEARANCE = 0.25
RACK_CENTER_Y = -0.80
RACK_MODULE_COUNT = 3
RACK_POST_WIDTH = 0.055
RACK_BASE_Z = 0.22
RACK_X_POSITIONS = (
    -ROOM_WIDTH / 2.0 + RACK_WALL_CLEARANCE + RACK_DEPTH / 2.0,
    ROOM_WIDTH / 2.0 - RACK_WALL_CLEARANCE - RACK_DEPTH / 2.0,
)
RACK_BAY_LENGTH = RACK_LENGTH / RACK_MODULE_COUNT
RACK_Y_MIN = RACK_CENTER_Y - RACK_LENGTH / 2.0
RACK_Y_MAX = RACK_CENTER_Y + RACK_LENGTH / 2.0
CENTRAL_CORRIDOR_WIDTH = ROOM_WIDTH - 2.0 * (RACK_WALL_CLEARANCE + RACK_DEPTH)
assert CENTRAL_CORRIDOR_WIDTH > DRAIN_WIDTH, "Racks overlap the central drain"
assert RACK_Y_MIN > -ROOM_LENGTH / 2.0 and RACK_Y_MAX < ROOM_LENGTH / 2.0

# Lighting: a transverse fixture over the exact center of each bay.
LIGHT_X_POSITIONS = RACK_X_POSITIONS
LIGHT_Y_POSITIONS = tuple(
    RACK_Y_MIN + (i + 0.5) * RACK_BAY_LENGTH
    for i in range(RACK_MODULE_COUNT)
)
LIGHT_FIXTURE_LENGTH = RACK_DEPTH - 0.30
LIGHT_FIXTURE_WIDTH = 0.28
LIGHT_FIXTURE_HEIGHT = 0.055
LIGHT_FIXTURE_Z = RACK_HEIGHT - 0.16
LIGHT_HANGER_TOP_Z = RACK_HEIGHT - 0.045
LIGHT_EMISSION_STRENGTH = 9.0
LED_EMISSION_COLOR = (1.0, 0.035, 0.32, 1.0)
LED_LIGHT_COLOR = (1.0, 0.065, 0.36)
AREA_LIGHT_ENERGY = 120.0
AREA_LIGHT_SIZE = LIGHT_FIXTURE_LENGTH * 0.88
AREA_LIGHT_SIZE_Y = LIGHT_FIXTURE_WIDTH * 0.85

# Stage 5: generic visual placeholders only.
CREATE_PLANT_PLACEHOLDERS = True
CREATE_TECHNICAL_PROPS = True
CREATE_SIDE_FANS = True
# Set 3 for a transverse row or 4 for a balanced 2 x 2 arrangement.
PLACEHOLDERS_PER_MODULE = 3
assert PLACEHOLDERS_PER_MODULE in (3, 4)
POT_HEIGHT = 0.40
POT_TOP_RADIUS = 0.23
POT_BOTTOM_RADIUS = 0.17
PLATFORM_TOP_Z = RACK_BASE_Z + 0.035 + 0.025 / 2.0
CANOPY_CENTER_Z = 1.12
CANOPY_DIMENSIONS = (0.62, 0.68, 0.72)
SIDE_FAN_DIAMETER = 0.82
SIDE_FAN_Z = 2.60

# Stage 6 overhead infrastructure; all dimensions in meters.
CREATE_WALL_SERVICES = True
CREATE_CEILING_DUCTS = True
CEILING_DUCT_DIAMETER = 0.68
CEILING_DUCT_Z = 3.16
CEILING_VENT_DIAMETER = 0.90
CEILING_VENT_FACE_Z = 2.52

# Vent placeholders -------------------------------------------
VENT_PORT_RADIUS = 0.27
VENT_PORT_DEPTH = 0.09
VENT_PORT_Z = 3.00
VENT_PORT_X_POSITIONS = (-2.85, 2.85)

# Geometry quality --------------------------------------------
LARGE_CYLINDER_SIDES = 32
MEDIUM_CYLINDER_SIDES = 24
SMALL_CYLINDER_SIDES = 12
BOLT_SIDES = 6

# Preview -----------------------------------------------------
WORLD_STRENGTH = 0.28
PREVIEW_CAMERA_LOCATION = (10.5, -15.0, 11.5)
PREVIEW_CAMERA_TARGET = (0.0, 0.5, 1.5)


# ============================================================
# 02 CLEANUP
# ============================================================

def _collection_parents(target):
    parents = []
    scene_root = bpy.context.scene.collection
    if scene_root.children.get(target.name) is target:
        parents.append(scene_root)
    for col in bpy.data.collections:
        if col.children.get(target.name) is target:
            parents.append(col)
    return parents


def remove_collection_tree(collection):
    """Remove generated collection hierarchy and contained objects."""
    for child in list(collection.children):
        remove_collection_tree(child)

    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    for parent in _collection_parents(collection):
        try:
            parent.children.unlink(collection)
        except RuntimeError:
            pass

    if collection.name in bpy.data.collections:
        bpy.data.collections.remove(collection)


def cleanup_generated_environment():
    if not REBUILD_COMPLETE_ENVIRONMENT:
        return

    names = [ROOT_COLLECTION_NAME] + list(LEGACY_ROOT_COLLECTIONS)
    seen = set()
    for name in names:
        col = bpy.data.collections.get(name)
        if col and col.name not in seen:
            seen.add(col.name)
            remove_collection_tree(col)

    # Remove stale generated empties/lights if they survived outside collections.
    for obj_name in ("WAREHOUSE_ORIGIN", "VENT_SYSTEM_ROOT", "LIGHT_SYSTEM_ROOT", "PREVIEW_CAMERA"):
        obj = bpy.data.objects.get(obj_name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


cleanup_generated_environment()

# Remove only the untouched Blender starter cube, if present.
starter = bpy.data.objects.get("Cube")
if (starter is not None and starter.type == 'MESH' and starter.parent is None
        and len(starter.data.vertices) == 8 and len(starter.data.polygons) == 6
        and len(starter.modifiers) == 0
        and all(mat is None or mat.name == "Material" for mat in starter.data.materials)
        and starter.location.length < 1e-6
        and all(abs(v) < 1e-6 for v in starter.rotation_euler)
        and all(abs(v - 2.0) < 1e-6 for v in starter.dimensions)):
    bpy.data.objects.remove(starter, do_unlink=True)

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.unit_settings.length_unit = 'METERS'


# ============================================================
# 03 COLLECTIONS
# ============================================================

def ensure_collection(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)

    if parent is None:
        if scene.collection.children.get(col.name) is None:
            scene.collection.children.link(col)
    else:
        if parent.children.get(col.name) is None:
            parent.children.link(col)
    return col


# Continue an older generated root instead of creating duplicates.
if not REBUILD_COMPLETE_ENVIRONMENT and bpy.data.collections.get(ROOT_COLLECTION_NAME) is None:
    for legacy_name in LEGACY_ROOT_COLLECTIONS:
        legacy = bpy.data.collections.get(legacy_name)
        if legacy:
            legacy.name = ROOT_COLLECTION_NAME
            break

ROOT = ensure_collection(ROOT_COLLECTION_NAME)

COL_SHELL = ensure_collection("ENV_SHELL", ROOT)
COL_DOORS = ensure_collection("ENV_DOORS", ROOT)
COL_TRIMS = ensure_collection("ENV_TRIMS", ROOT)
COL_FLOOR = ensure_collection("ENV_FLOOR", ROOT)
COL_INFRA = ensure_collection("ENV_INFRA", ROOT)
COL_CEILING = ensure_collection("ENV_CEILING", ROOT)
COL_ELECTRICAL = ensure_collection("ENV_ELECTRICAL", ROOT)
COL_VENT = ensure_collection("ENV_VENT", ROOT)
COL_LIGHT_POINTS = ensure_collection("ENV_LIGHTING_POINTS", ROOT)
COL_DUCTS = ensure_collection("ENV_DUCTS", ROOT)
COL_FANS = ensure_collection("ENV_FANS", ROOT)
COL_LIGHTS = ensure_collection("ENV_LIGHT_FIXTURES", ROOT)
COL_STRUCT = ensure_collection("ENV_STRUCTURAL_DETAILS", ROOT)
COL_RACKS = ensure_collection("ENV_RACKS", ROOT)
COL_PLACEHOLDERS = ensure_collection("ENV_PLANT_PLACEHOLDERS", ROOT)
COL_TECH_PROPS = ensure_collection("ENV_TECHNICAL_PROPS", ROOT)
COL_SIDE_FANS = ensure_collection("ENV_SIDE_FANS", ROOT)
COL_WALL_SERVICES = ensure_collection("ENV_WALL_SERVICES", ROOT)
COL_CEILING_DUCTS = ensure_collection("ENV_CEILING_DUCTS", ROOT)


def ensure_empty(name, collection, location=(0.0, 0.0, 0.0), display='PLAIN_AXES', size=0.5):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        collection.objects.link(obj)
        obj.location = location
    obj.empty_display_type = display
    obj.empty_display_size = size
    return obj


WAREHOUSE_ORIGIN = ensure_empty("WAREHOUSE_ORIGIN", ROOT, (0.0, 0.0, 0.0), 'PLAIN_AXES', 0.5)
VENT_SYSTEM_ROOT = ensure_empty("VENT_SYSTEM_ROOT", COL_DUCTS, (0.0, 0.0, 0.0), 'PLAIN_AXES', 0.35)
LIGHT_SYSTEM_ROOT = ensure_empty("LIGHT_SYSTEM_ROOT", COL_LIGHTS, (0.0, 0.0, 0.0), 'PLAIN_AXES', 0.35)


# ============================================================
# 04 MATERIALS
# ============================================================

def clear_nodes(mat):
    if mat.use_nodes:
        mat.node_tree.nodes.clear()


def get_or_create_material(name):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    return mat


def make_simple_material(name, color, roughness=0.6, metallic=0.0):
    mat = get_or_create_material(name)
    if CREATE_MATERIALS:
        clear_nodes(mat)
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        out = nodes.new("ShaderNodeOutputMaterial")
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.diffuse_color = (*color, 1.0)
    return mat


def make_wall_material(name, horizontal_axis='X'):
    """World/object-space concrete block suggestion using a fixed scene origin."""
    mat = get_or_create_material(name)
    if not CREATE_MATERIALS:
        mat.diffuse_color = (0.36, 0.37, 0.36, 1.0)
        return mat

    clear_nodes(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexCoord")
    tex.object = WAREHOUSE_ORIGIN
    sep = nodes.new("ShaderNodeSeparateXYZ")
    comb = nodes.new("ShaderNodeCombineXYZ")
    brick = nodes.new("ShaderNodeTexBrick")
    noise = nodes.new("ShaderNodeTexNoise")
    mix = nodes.new("ShaderNodeMixRGB")
    bump = nodes.new("ShaderNodeBump")

    if horizontal_axis == 'X':
        links.new(tex.outputs["Object"], sep.inputs[0])
        links.new(sep.outputs["X"], comb.inputs["X"])
        links.new(sep.outputs["Z"], comb.inputs["Y"])
    else:
        links.new(tex.outputs["Object"], sep.inputs[0])
        links.new(sep.outputs["Y"], comb.inputs["X"])
        links.new(sep.outputs["Z"], comb.inputs["Y"])

    brick.inputs["Color1"].default_value = (0.34, 0.35, 0.34, 1.0)
    brick.inputs["Color2"].default_value = (0.39, 0.40, 0.39, 1.0)
    brick.inputs["Mortar"].default_value = (0.20, 0.205, 0.20, 1.0)
    brick.inputs["Scale"].default_value = 5.0
    brick.inputs["Mortar Size"].default_value = 0.018
    brick.inputs["Mortar Smooth"].default_value = 0.01
    brick.inputs["Brick Width"].default_value = 0.55
    brick.inputs["Row Height"].default_value = 0.27

    noise.inputs["Scale"].default_value = 3.5
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.65

    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 0.16

    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.025

    links.new(comb.outputs["Vector"], brick.inputs["Vector"])
    links.new(tex.outputs["Object"], noise.inputs["Vector"])
    links.new(brick.outputs["Color"], mix.inputs[1])
    links.new(noise.outputs["Fac"], mix.inputs[2])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(brick.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    bsdf.inputs["Roughness"].default_value = 0.80
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.diffuse_color = (0.36, 0.37, 0.36, 1.0)
    return mat


def make_floor_material():
    mat = get_or_create_material("MAT_Concrete_Floor")
    if not CREATE_MATERIALS:
        mat.diffuse_color = (0.26, 0.27, 0.26, 1.0)
        return mat

    clear_nodes(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexCoord")
    tex.object = WAREHOUSE_ORIGIN
    noise_large = nodes.new("ShaderNodeTexNoise")
    noise_micro = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")

    noise_large.inputs["Scale"].default_value = 1.9
    noise_large.inputs["Detail"].default_value = 4.0
    noise_large.inputs["Roughness"].default_value = 0.72
    noise_micro.inputs["Scale"].default_value = 32.0
    noise_micro.inputs["Detail"].default_value = 2.0
    noise_micro.inputs["Roughness"].default_value = 0.55

    ramp.color_ramp.elements[0].position = 0.26
    ramp.color_ramp.elements[0].color = (0.19, 0.195, 0.19, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (0.34, 0.345, 0.335, 1.0)

    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.018

    links.new(tex.outputs["Object"], noise_large.inputs["Vector"])
    links.new(tex.outputs["Object"], noise_micro.inputs["Vector"])
    links.new(noise_large.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise_micro.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.64
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.diffuse_color = (0.27, 0.28, 0.27, 1.0)
    return mat


def make_galvanized_material():
    mat = get_or_create_material("MAT_Galvanized_Metal")
    if not CREATE_MATERIALS:
        mat.diffuse_color = (0.42, 0.44, 0.45, 1.0)
        return mat

    clear_nodes(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexCoord")
    tex.object = WAREHOUSE_ORIGIN
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")

    noise.inputs["Scale"].default_value = 7.0
    noise.inputs["Detail"].default_value = 2.5
    noise.inputs["Roughness"].default_value = 0.55
    ramp.color_ramp.elements[0].color = (0.28, 0.30, 0.31, 1.0)
    ramp.color_ramp.elements[1].color = (0.58, 0.60, 0.61, 1.0)
    ramp.color_ramp.elements[0].position = 0.28
    ramp.color_ramp.elements[1].position = 0.72

    links.new(tex.outputs["Object"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.88
    bsdf.inputs["Roughness"].default_value = 0.34
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.diffuse_color = (0.46, 0.48, 0.49, 1.0)
    return mat


def make_emission_material():
    mat = get_or_create_material("MAT_Light_Diffuser_Emission")
    if not CREATE_MATERIALS:
        return mat
    clear_nodes(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    out = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = LED_EMISSION_COLOR
    emission.inputs["Strength"].default_value = LIGHT_EMISSION_STRENGTH
    links.new(emission.outputs["Emission"], out.inputs["Surface"])
    mat.diffuse_color = LED_EMISSION_COLOR
    return mat


MAT_WALL_X = make_wall_material("MAT_Concrete_Wall_XZ", 'X')
MAT_WALL_Y = make_wall_material("MAT_Concrete_Wall_YZ", 'Y')
MAT_WALL_ACCENT = make_simple_material("MAT_Concrete_Accent", (0.25, 0.26, 0.25), 0.82, 0.0)
MAT_FLOOR = make_floor_material()
MAT_FLOOR_JOINT = make_simple_material("MAT_Floor_Joint", (0.045, 0.05, 0.045), 0.9, 0.0)
MAT_STRUCTURAL = make_simple_material("MAT_Structural_Dark", (0.045, 0.05, 0.055), 0.42, 0.72)
MAT_DARK_METAL = make_simple_material("MAT_Dark_Metal", (0.07, 0.075, 0.08), 0.44, 0.76)
MAT_GALV = make_galvanized_material()
MAT_DOOR = make_simple_material("MAT_Door_Metal", (0.09, 0.095, 0.10), 0.48, 0.68)
MAT_ELECTRICAL = make_simple_material("MAT_Electrical_Metal", (0.18, 0.19, 0.195), 0.48, 0.66)
MAT_BLACK = make_simple_material("MAT_Vent_Inner", (0.018, 0.020, 0.022), 0.58, 0.35)
MAT_RUBBER = make_simple_material("MAT_Rubber", (0.018, 0.018, 0.018), 0.74, 0.0)
MAT_EMISSION = make_emission_material()
MAT_POT = make_simple_material("MAT_Generic_Pot", (0.08, 0.085, 0.08), 0.78)
MAT_POT_FILL = make_simple_material("MAT_Pot_Fill", (0.065, 0.047, 0.031), 0.95)
MAT_PLACEHOLDER_A = make_simple_material("MAT_Canopy_Placeholder_A", (0.16, 0.28, 0.10), 0.9)
MAT_PLACEHOLDER_B = make_simple_material("MAT_Canopy_Placeholder_B", (0.23, 0.34, 0.13), 0.9)
MAT_BLUE_TANK = make_simple_material("MAT_Blue_Tank", (0.015, 0.10, 0.42), 0.4)
MAT_CONTAINER = make_simple_material("MAT_Closed_Container", (0.40, 0.43, 0.38), 0.7)
MAT_CRATE = make_simple_material("MAT_Generic_Crate", (0.21, 0.23, 0.24), 0.7)
MAT_CABLE_ACCENT = make_simple_material("MAT_Cable_Accent", (0.16, 0.075, 0.045), 0.7)
MAT_BUCKET = make_simple_material("MAT_Generic_Bucket", (0.62, 0.63, 0.56), 0.6)


# ============================================================
# 05 HELPERS
# ============================================================

def object_exists(name):
    return bpy.data.objects.get(name) is not None


def link_object_to_collection(obj, collection):
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    # Keep generated objects in their intended collection only when possible.
    for col in list(obj.users_collection):
        if col != collection:
            try:
                col.objects.unlink(obj)
            except RuntimeError:
                pass


def assign_material(obj, material, slot=0):
    if obj is None or material is None or not hasattr(obj.data, 'materials'):
        return
    if len(obj.data.materials) == 0:
        obj.data.materials.append(material)
    elif slot < len(obj.data.materials):
        obj.data.materials[slot] = material
    else:
        obj.data.materials.append(material)


def apply_scale(obj):
    if obj is None or obj.type != 'MESH':
        return
    # Data API-friendly enough for Text Editor execution; transform_apply does not require VIEW_3D.
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    except RuntimeError:
        pass
    obj.select_set(False)


def shade_smooth(obj):
    if obj is None or obj.type != 'MESH':
        return
    for poly in obj.data.polygons:
        poly.use_smooth = True


def add_bevel(obj, width=0.006, segments=2, apply=False):
    if obj is None or obj.type != 'MESH' or width <= 0:
        return None
    # Avoid duplicate bevel modifiers in continuation mode.
    existing = obj.modifiers.get("ENV_Bevel")
    if existing:
        return existing
    mod = obj.modifiers.new("ENV_Bevel", 'BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    if apply:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except RuntimeError:
            pass
        obj.select_set(False)
    return mod


def create_box(name, location, dimensions, collection, material=None, bevel=0.0, parent=None):
    existing = bpy.data.objects.get(name)
    if existing:
        return existing

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    apply_scale(obj)
    link_object_to_collection(obj, collection)
    if material:
        assign_material(obj, material)
    if bevel > 0:
        add_bevel(obj, bevel, 2, apply=False)
    if parent:
        obj.parent = parent
    return obj


def create_cylinder(name, location, radius, depth, collection, material=None,
                    vertices=24, rotation=(0.0, 0.0, 0.0), bevel=0.0,
                    smooth=True, parent=None):
    existing = bpy.data.objects.get(name)
    if existing:
        return existing

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        end_fill_type='NGON',
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    link_object_to_collection(obj, collection)
    if material:
        assign_material(obj, material)
    if smooth:
        shade_smooth(obj)
    if bevel > 0:
        add_bevel(obj, bevel, 2, apply=False)
    if parent:
        obj.parent = parent
    return obj


def create_cylinder_between(name, p1, p2, radius, collection, material=None,
                            vertices=24, bevel=0.0, smooth=True, parent=None):
    existing = bpy.data.objects.get(name)
    if existing:
        return existing

    p1 = Vector(p1)
    p2 = Vector(p2)
    delta = p2 - p1
    length = delta.length
    if length <= 1e-6:
        return None
    mid = (p1 + p2) * 0.5

    obj = create_cylinder(
        name,
        mid,
        radius,
        length,
        collection,
        material,
        vertices=vertices,
        bevel=bevel,
        smooth=smooth,
        parent=parent,
    )
    if obj and obj.name == name:
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(delta.normalized())
    return obj


def create_hex_bolt(name, location, axis='Z', radius=0.025, depth=0.018,
                    collection=COL_STRUCT, material=MAT_DARK_METAL, parent=None):
    rot = (0.0, 0.0, 0.0)
    if axis == 'X':
        rot = (0.0, math.radians(90.0), 0.0)
    elif axis == 'Y':
        rot = (math.radians(90.0), 0.0, 0.0)
    return create_cylinder(
        name, location, radius, depth, collection, material,
        vertices=BOLT_SIDES, rotation=rot, bevel=0.002, smooth=False, parent=parent
    )


def create_poly_curve(name, points, collection, material, radius=0.018,
                      bevel_resolution=1, resolution=2, parent=None):
    existing = bpy.data.objects.get(name)
    if existing:
        return existing

    curve_data = bpy.data.curves.new(name + "_DATA", 'CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = resolution
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = bevel_resolution
    curve_data.resolution_u = resolution
    curve_data.fill_mode = 'FULL'

    spline = curve_data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for i, p in enumerate(points):
        spline.points[i].co = (p[0], p[1], p[2], 1.0)

    obj = bpy.data.objects.new(name, curve_data)
    collection.objects.link(obj)
    if material:
        curve_data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def create_bezier_curve(name, points, collection, material, radius,
                        bevel_resolution=3, parent=None):
    existing = bpy.data.objects.get(name)
    if existing:
        return existing

    curve_data = bpy.data.curves.new(name + "_DATA", 'CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 8
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = bevel_resolution
    curve_data.fill_mode = 'FULL'

    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(len(points) - 1)
    for i, p in enumerate(points):
        bp = spline.bezier_points[i]
        bp.co = p
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    obj = bpy.data.objects.new(name, curve_data)
    collection.objects.link(obj)
    if material:
        curve_data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def create_ring_collar(name, center, axis, radius, length, collection,
                       material=MAT_GALV, parent=None):
    """Visual collar: a short, slightly oversized cylinder around a pipe axis."""
    cx, cy, cz = center
    half = length * 0.5
    if axis == 'X':
        p1, p2 = (cx - half, cy, cz), (cx + half, cy, cz)
    elif axis == 'Y':
        p1, p2 = (cx, cy - half, cz), (cx, cy + half, cz)
    else:
        p1, p2 = (cx, cy, cz - half), (cx, cy, cz + half)
    return create_cylinder_between(
        name, p1, p2, radius, collection, material,
        vertices=LARGE_CYLINDER_SIDES, bevel=0.004, parent=parent
    )


def create_panel_box(name, location, dimensions, collection, body_material,
                     face_material=None, face_offset=0.012, bevel=0.018, normal_axis='Y'):
    body = create_box(name + "_BODY", location, dimensions, collection, body_material, bevel)
    if bpy.data.objects.get(name + "_LID"):
        return body

    x, y, z = location
    dx, dy, dz = dimensions
    if normal_axis == 'Y':
        lid_loc = (x, y - dy / 2.0 - face_offset / 2.0, z)
        lid_dim = (dx - 0.045, face_offset, dz - 0.045)
    elif normal_axis == 'X_NEG':
        lid_loc = (x + dx / 2.0 + face_offset / 2.0, y, z)
        lid_dim = (face_offset, dy - 0.045, dz - 0.045)
    else:
        lid_loc = (x - dx / 2.0 - face_offset / 2.0, y, z)
        lid_dim = (face_offset, dy - 0.045, dz - 0.045)

    create_box(name + "_LID", lid_loc, lid_dim, collection,
               face_material or body_material, max(0.004, bevel * 0.65))
    return body


def create_area_light(name, location, energy, size, size_y, collection, parent=None):
    obj = bpy.data.objects.get(name)
    if obj is None:
        data = bpy.data.lights.new(name + "_DATA", type='AREA')
        obj = bpy.data.objects.new(name, data)
        collection.objects.link(obj)
    elif obj.type != 'LIGHT' or obj.data.type != 'AREA':
        raise ValueError(f"{name} exists but is not an AREA light")

    data = obj.data
    data.energy = energy
    data.shape = 'RECTANGLE'
    # Fixtures run along X, matching the transverse rack lights.
    data.size = size
    data.size_y = size_y
    data.color = LED_LIGHT_COLOR
    # Use world coordinates so no parent rotation can tilt the light.
    obj.parent = None
    for constraint in list(obj.constraints):
        obj.constraints.remove(constraint)
    obj.location = location
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    return obj


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


# ============================================================
# 06 SHELL
# ============================================================

BACK_Y = ROOM_LENGTH / 2.0 + WALL_THICKNESS / 2.0
FRONT_Y = -ROOM_LENGTH / 2.0 - WALL_THICKNESS / 2.0
LEFT_X = -ROOM_WIDTH / 2.0 - WALL_THICKNESS / 2.0
RIGHT_X = ROOM_WIDTH / 2.0 + WALL_THICKNESS / 2.0


def build_x_wall_with_opening(prefix, y, width, opening_center, opening_width,
                              opening_height, material):
    x_min = -width / 2.0
    x_max = width / 2.0
    open_min = opening_center - opening_width / 2.0
    open_max = opening_center + opening_width / 2.0

    left_width = open_min - x_min
    right_width = x_max - open_max
    top_height = WALL_HEIGHT - opening_height

    if left_width > 0:
        create_box(prefix + "_LEFT",
                   (x_min + left_width / 2.0, y, WALL_HEIGHT / 2.0),
                   (left_width, WALL_THICKNESS, WALL_HEIGHT),
                   COL_SHELL, material, 0.004)
    if right_width > 0:
        create_box(prefix + "_RIGHT",
                   (open_max + right_width / 2.0, y, WALL_HEIGHT / 2.0),
                   (right_width, WALL_THICKNESS, WALL_HEIGHT),
                   COL_SHELL, material, 0.004)
    if top_height > 0:
        create_box(prefix + "_HEADER",
                   (opening_center, y, opening_height + top_height / 2.0),
                   (opening_width, WALL_THICKNESS, top_height),
                   COL_SHELL, material, 0.004)


def build_y_wall_with_opening(prefix, x, length, opening_center, opening_width,
                              opening_height, material):
    y_min = -length / 2.0
    y_max = length / 2.0
    open_min = opening_center - opening_width / 2.0
    open_max = opening_center + opening_width / 2.0

    a = open_min - y_min
    b = y_max - open_max
    top_height = WALL_HEIGHT - opening_height

    if a > 0:
        create_box(prefix + "_A",
                   (x, y_min + a / 2.0, WALL_HEIGHT / 2.0),
                   (WALL_THICKNESS, a, WALL_HEIGHT),
                   COL_SHELL, material, 0.004)
    if b > 0:
        create_box(prefix + "_B",
                   (x, open_max + b / 2.0, WALL_HEIGHT / 2.0),
                   (WALL_THICKNESS, b, WALL_HEIGHT),
                   COL_SHELL, material, 0.004)
    if top_height > 0:
        create_box(prefix + "_HEADER",
                   (x, opening_center, opening_height + top_height / 2.0),
                   (WALL_THICKNESS, opening_width, top_height),
                   COL_SHELL, material, 0.004)


if CREATE_SHELL:
    build_x_wall_with_opening("WALL_BACK", BACK_Y, ROOM_WIDTH,
                              BACK_DOOR_X, BACK_DOOR_WIDTH, BACK_DOOR_HEIGHT, MAT_WALL_X)
    build_x_wall_with_opening("WALL_FRONT", FRONT_Y, ROOM_WIDTH,
                              FRONT_GATE_X, FRONT_GATE_WIDTH, FRONT_GATE_HEIGHT, MAT_WALL_X)
    build_y_wall_with_opening("WALL_LEFT", LEFT_X, ROOM_LENGTH,
                              SIDE_DOOR_Y, SIDE_DOOR_WIDTH, SIDE_DOOR_HEIGHT, MAT_WALL_Y)
    create_box("WALL_RIGHT", (RIGHT_X, 0.0, WALL_HEIGHT / 2.0),
               (WALL_THICKNESS, ROOM_LENGTH, WALL_HEIGHT),
               COL_SHELL, MAT_WALL_Y, 0.004)

    if CREATE_CEILING:
        create_box("CEILING_SLAB", (0.0, 0.0, WALL_HEIGHT + CEILING_THICKNESS / 2.0),
                   (ROOM_WIDTH + WALL_THICKNESS * 2.0,
                    ROOM_LENGTH + WALL_THICKNESS * 2.0,
                    CEILING_THICKNESS),
                   COL_CEILING, MAT_WALL_X, 0.003)


# ============================================================
# 07 FLOOR
# ============================================================

half_drain = DRAIN_WIDTH / 2.0
floor_side_width = ROOM_WIDTH / 2.0 - half_drain
floor_center_offset = half_drain + floor_side_width / 2.0

create_box("FLOOR_LEFT", (-floor_center_offset, 0.0, -FLOOR_THICKNESS / 2.0),
           (floor_side_width, ROOM_LENGTH, FLOOR_THICKNESS),
           COL_FLOOR, MAT_FLOOR, 0.002)
create_box("FLOOR_RIGHT", (floor_center_offset, 0.0, -FLOOR_THICKNESS / 2.0),
           (floor_side_width, ROOM_LENGTH, FLOOR_THICKNESS),
           COL_FLOOR, MAT_FLOOR, 0.002)

DRAIN_Y_MIN = -ROOM_LENGTH / 2.0 + DRAIN_FRONT_MARGIN
DRAIN_Y_MAX = ROOM_LENGTH / 2.0 - DRAIN_BACK_MARGIN
DRAIN_LENGTH = DRAIN_Y_MAX - DRAIN_Y_MIN
DRAIN_CENTER_Y = (DRAIN_Y_MIN + DRAIN_Y_MAX) / 2.0

if CREATE_DRAIN:
    create_box("FLOOR_DRAIN_FRONT_CAP",
               (0.0, -ROOM_LENGTH / 2.0 + DRAIN_FRONT_MARGIN / 2.0,
                -FLOOR_THICKNESS / 2.0),
               (DRAIN_WIDTH, DRAIN_FRONT_MARGIN, FLOOR_THICKNESS),
               COL_FLOOR, MAT_FLOOR)
    create_box("FLOOR_DRAIN_BACK_CAP",
               (0.0, ROOM_LENGTH / 2.0 - DRAIN_BACK_MARGIN / 2.0,
                -FLOOR_THICKNESS / 2.0),
               (DRAIN_WIDTH, DRAIN_BACK_MARGIN, FLOOR_THICKNESS),
               COL_FLOOR, MAT_FLOOR)

    create_box("DRAIN_CHANNEL",
               (0.0, DRAIN_CENTER_Y, -DRAIN_DEPTH - 0.012),
               (DRAIN_WIDTH, DRAIN_LENGTH, 0.025),
               COL_FLOOR, MAT_BLACK)

    shoulder = 0.025
    create_box("DRAIN_EDGE_LEFT",
               (-(DRAIN_WIDTH / 2.0 + shoulder / 2.0), DRAIN_CENTER_Y, -DRAIN_DEPTH / 2.0),
               (shoulder, DRAIN_LENGTH, DRAIN_DEPTH), COL_FLOOR, MAT_GALV, 0.002)
    create_box("DRAIN_EDGE_RIGHT",
               ((DRAIN_WIDTH / 2.0 + shoulder / 2.0), DRAIN_CENTER_Y, -DRAIN_DEPTH / 2.0),
               (shoulder, DRAIN_LENGTH, DRAIN_DEPTH), COL_FLOOR, MAT_GALV, 0.002)

# Panel joints
for i, y in enumerate(FLOOR_TRANSVERSE_JOINTS):
    span = ROOM_WIDTH / 2.0 - DRAIN_WIDTH / 2.0
    create_box(f"FLOOR_JOINT_T_{i:02d}_L",
               (-(ROOM_WIDTH / 4.0 + DRAIN_WIDTH / 4.0), y, 0.002),
               (span, FLOOR_JOINT_WIDTH, 0.004), COL_FLOOR, MAT_FLOOR_JOINT)
    create_box(f"FLOOR_JOINT_T_{i:02d}_R",
               ((ROOM_WIDTH / 4.0 + DRAIN_WIDTH / 4.0), y, 0.002),
               (span, FLOOR_JOINT_WIDTH, 0.004), COL_FLOOR, MAT_FLOOR_JOINT)

for i, x in enumerate(FLOOR_LONGITUDINAL_JOINTS):
    create_box(f"FLOOR_JOINT_L_{i:02d}", (x, 0.0, 0.002),
               (FLOOR_JOINT_WIDTH, ROOM_LENGTH - 0.10, 0.004),
               COL_FLOOR, MAT_FLOOR_JOINT)


# ============================================================
# 08 DRAIN GRATING
# ============================================================

DRAIN_MODULE_COUNT = 0
if CREATE_DRAIN:
    DRAIN_MODULE_COUNT = max(1, math.ceil(DRAIN_LENGTH / DRAIN_GRATE_MODULE_LENGTH))
    module_len = DRAIN_LENGTH / DRAIN_MODULE_COUNT

    for m in range(DRAIN_MODULE_COUNT):
        cy = DRAIN_Y_MIN + module_len * (m + 0.5)
        rail_w = 0.022
        create_box(f"DRAIN_GRATE_MODULE_{m:02d}_RAIL_L",
                   (-DRAIN_WIDTH / 2.0 + rail_w / 2.0, cy, 0.009),
                   (rail_w, module_len - 0.012, 0.018), COL_FLOOR, MAT_GALV, 0.002)
        create_box(f"DRAIN_GRATE_MODULE_{m:02d}_RAIL_R",
                   (DRAIN_WIDTH / 2.0 - rail_w / 2.0, cy, 0.009),
                   (rail_w, module_len - 0.012, 0.018), COL_FLOOR, MAT_GALV, 0.002)

        usable = module_len - 0.08
        bar_count = max(3, int(usable / DRAIN_GRATE_BAR_SPACING))
        for b in range(bar_count):
            t = 0.5 if bar_count == 1 else b / (bar_count - 1)
            by = cy - usable / 2.0 + usable * t
            create_box(f"DRAIN_GRATE_MODULE_{m:02d}_BAR_{b:02d}",
                       (0.0, by, 0.011),
                       (DRAIN_WIDTH - 0.035, DRAIN_GRATE_BAR_WIDTH, 0.018),
                       COL_FLOOR, MAT_GALV, 0.0015)


# ============================================================
# 09 TRIMS
# ============================================================

def create_back_door_frame():
    y = ROOM_LENGTH / 2.0 - DOOR_FRAME_DEPTH / 2.0
    sx = BACK_DOOR_WIDTH / 2.0 + DOOR_FRAME_WIDTH / 2.0
    create_box("BACK_DOOR_FRAME_LEFT", (-sx, y, BACK_DOOR_HEIGHT / 2.0),
               (DOOR_FRAME_WIDTH, DOOR_FRAME_DEPTH, BACK_DOOR_HEIGHT),
               COL_TRIMS, MAT_STRUCTURAL, 0.008)
    create_box("BACK_DOOR_FRAME_RIGHT", (sx, y, BACK_DOOR_HEIGHT / 2.0),
               (DOOR_FRAME_WIDTH, DOOR_FRAME_DEPTH, BACK_DOOR_HEIGHT),
               COL_TRIMS, MAT_STRUCTURAL, 0.008)
    create_box("BACK_DOOR_FRAME_TOP",
               (0.0, y, BACK_DOOR_HEIGHT + DOOR_FRAME_WIDTH / 2.0),
               (BACK_DOOR_WIDTH + DOOR_FRAME_WIDTH * 2.0,
                DOOR_FRAME_DEPTH, DOOR_FRAME_WIDTH),
               COL_TRIMS, MAT_STRUCTURAL, 0.008)


def create_side_door_frame():
    x = -ROOM_WIDTH / 2.0 + DOOR_FRAME_DEPTH / 2.0
    sy = SIDE_DOOR_WIDTH / 2.0 + DOOR_FRAME_WIDTH / 2.0
    create_box("SIDE_DOOR_FRAME_A", (x, SIDE_DOOR_Y - sy, SIDE_DOOR_HEIGHT / 2.0),
               (DOOR_FRAME_DEPTH, DOOR_FRAME_WIDTH, SIDE_DOOR_HEIGHT),
               COL_TRIMS, MAT_STRUCTURAL, 0.008)
    create_box("SIDE_DOOR_FRAME_B", (x, SIDE_DOOR_Y + sy, SIDE_DOOR_HEIGHT / 2.0),
               (DOOR_FRAME_DEPTH, DOOR_FRAME_WIDTH, SIDE_DOOR_HEIGHT),
               COL_TRIMS, MAT_STRUCTURAL, 0.008)
    create_box("SIDE_DOOR_FRAME_TOP",
               (x, SIDE_DOOR_Y, SIDE_DOOR_HEIGHT + DOOR_FRAME_WIDTH / 2.0),
               (DOOR_FRAME_DEPTH, SIDE_DOOR_WIDTH + DOOR_FRAME_WIDTH * 2.0,
                DOOR_FRAME_WIDTH),
               COL_TRIMS, MAT_STRUCTURAL, 0.008)


def create_front_gate_frame():
    y = -ROOM_LENGTH / 2.0 + GATE_FRAME_DEPTH / 2.0
    sx = FRONT_GATE_WIDTH / 2.0 + GATE_FRAME_WIDTH / 2.0
    create_box("FRONT_GATE_FRAME_LEFT", (-sx, y, FRONT_GATE_HEIGHT / 2.0),
               (GATE_FRAME_WIDTH, GATE_FRAME_DEPTH, FRONT_GATE_HEIGHT),
               COL_TRIMS, MAT_STRUCTURAL, 0.010)
    create_box("FRONT_GATE_FRAME_RIGHT", (sx, y, FRONT_GATE_HEIGHT / 2.0),
               (GATE_FRAME_WIDTH, GATE_FRAME_DEPTH, FRONT_GATE_HEIGHT),
               COL_TRIMS, MAT_STRUCTURAL, 0.010)
    create_box("FRONT_GATE_FRAME_TOP",
               (0.0, y, FRONT_GATE_HEIGHT + GATE_FRAME_WIDTH / 2.0),
               (FRONT_GATE_WIDTH + GATE_FRAME_WIDTH * 2.0,
                GATE_FRAME_DEPTH, GATE_FRAME_WIDTH),
               COL_TRIMS, MAT_STRUCTURAL, 0.010)


create_back_door_frame()
create_side_door_frame()
create_front_gate_frame()

create_box("THRESHOLD_BACK_DOOR",
           (BACK_DOOR_X, ROOM_LENGTH / 2.0, THRESHOLD_HEIGHT / 2.0),
           (BACK_DOOR_WIDTH + 0.06, THRESHOLD_DEPTH, THRESHOLD_HEIGHT),
           COL_TRIMS, MAT_GALV, 0.005)
create_box("THRESHOLD_SIDE_DOOR",
           (-ROOM_WIDTH / 2.0, SIDE_DOOR_Y, THRESHOLD_HEIGHT / 2.0),
           (THRESHOLD_DEPTH, SIDE_DOOR_WIDTH + 0.06, THRESHOLD_HEIGHT),
           COL_TRIMS, MAT_GALV, 0.005)


def add_baseboard_x(name, x1, x2, y):
    if x2 <= x1:
        return
    create_box(name, ((x1 + x2) / 2.0, y, BASEBOARD_HEIGHT / 2.0),
               (x2 - x1, BASEBOARD_DEPTH, BASEBOARD_HEIGHT),
               COL_TRIMS, MAT_WALL_ACCENT, 0.003)


def add_baseboard_y(name, y1, y2, x):
    if y2 <= y1:
        return
    create_box(name, (x, (y1 + y2) / 2.0, BASEBOARD_HEIGHT / 2.0),
               (BASEBOARD_DEPTH, y2 - y1, BASEBOARD_HEIGHT),
               COL_TRIMS, MAT_WALL_ACCENT, 0.003)


# Baseboards interrupted at openings
back_min = BACK_DOOR_X - BACK_DOOR_WIDTH / 2.0
back_max = BACK_DOOR_X + BACK_DOOR_WIDTH / 2.0
front_min = FRONT_GATE_X - FRONT_GATE_WIDTH / 2.0
front_max = FRONT_GATE_X + FRONT_GATE_WIDTH / 2.0
side_min = SIDE_DOOR_Y - SIDE_DOOR_WIDTH / 2.0
side_max = SIDE_DOOR_Y + SIDE_DOOR_WIDTH / 2.0

add_baseboard_x("BASEBOARD_BACK_L", -ROOM_WIDTH / 2.0, back_min,
                ROOM_LENGTH / 2.0 - BASEBOARD_DEPTH / 2.0)
add_baseboard_x("BASEBOARD_BACK_R", back_max, ROOM_WIDTH / 2.0,
                ROOM_LENGTH / 2.0 - BASEBOARD_DEPTH / 2.0)
add_baseboard_x("BASEBOARD_FRONT_L", -ROOM_WIDTH / 2.0, front_min,
                -ROOM_LENGTH / 2.0 + BASEBOARD_DEPTH / 2.0)
add_baseboard_x("BASEBOARD_FRONT_R", front_max, ROOM_WIDTH / 2.0,
                -ROOM_LENGTH / 2.0 + BASEBOARD_DEPTH / 2.0)
add_baseboard_y("BASEBOARD_LEFT_A", -ROOM_LENGTH / 2.0, side_min,
                -ROOM_WIDTH / 2.0 + BASEBOARD_DEPTH / 2.0)
add_baseboard_y("BASEBOARD_LEFT_B", side_max, ROOM_LENGTH / 2.0,
                -ROOM_WIDTH / 2.0 + BASEBOARD_DEPTH / 2.0)
add_baseboard_y("BASEBOARD_RIGHT", -ROOM_LENGTH / 2.0, ROOM_LENGTH / 2.0,
                ROOM_WIDTH / 2.0 - BASEBOARD_DEPTH / 2.0)

if CREATE_WALL_RELIEF:
    relief_height = WALL_HEIGHT - BASEBOARD_HEIGHT - 0.42
    relief_z = BASEBOARD_HEIGHT + relief_height / 2.0
    for i, y in enumerate((-4.80, -2.10, 0.70, 3.50)):
        if abs(y - SIDE_DOOR_Y) > 0.80:
            create_box(f"WALL_RELIEF_LEFT_{i:02d}",
                       (-ROOM_WIDTH / 2.0 + WALL_RELIEF_DEPTH / 2.0, y, relief_z),
                       (WALL_RELIEF_DEPTH, WALL_RELIEF_WIDTH, relief_height),
                       COL_TRIMS, MAT_WALL_ACCENT, 0.003)
        create_box(f"WALL_RELIEF_RIGHT_{i:02d}",
                   (ROOM_WIDTH / 2.0 - WALL_RELIEF_DEPTH / 2.0, y, relief_z),
                   (WALL_RELIEF_DEPTH, WALL_RELIEF_WIDTH, relief_height),
                   COL_TRIMS, MAT_WALL_ACCENT, 0.003)

    for i, x in enumerate((-3.05, 3.05)):
        create_box(f"WALL_RELIEF_BACK_{i:02d}",
                   (x, ROOM_LENGTH / 2.0 - WALL_RELIEF_DEPTH / 2.0, relief_z),
                   (WALL_RELIEF_WIDTH, WALL_RELIEF_DEPTH, relief_height),
                   COL_TRIMS, MAT_WALL_ACCENT, 0.003)

    create_box("TOP_BAND_LEFT",
               (-ROOM_WIDTH / 2.0 + TOP_WALL_BAND_DEPTH / 2.0, 0.0, WALL_HEIGHT - 0.28),
               (TOP_WALL_BAND_DEPTH, ROOM_LENGTH - 0.12, TOP_WALL_BAND_HEIGHT),
               COL_TRIMS, MAT_WALL_ACCENT, 0.003)
    create_box("TOP_BAND_RIGHT",
               (ROOM_WIDTH / 2.0 - TOP_WALL_BAND_DEPTH / 2.0, 0.0, WALL_HEIGHT - 0.28),
               (TOP_WALL_BAND_DEPTH, ROOM_LENGTH - 0.12, TOP_WALL_BAND_HEIGHT),
               COL_TRIMS, MAT_WALL_ACCENT, 0.003)
    create_box("TOP_BAND_BACK",
               (0.0, ROOM_LENGTH / 2.0 - TOP_WALL_BAND_DEPTH / 2.0, WALL_HEIGHT - 0.28),
               (ROOM_WIDTH - 0.12, TOP_WALL_BAND_DEPTH, TOP_WALL_BAND_HEIGHT),
               COL_TRIMS, MAT_WALL_ACCENT, 0.003)

# Corner guards
for nm, x, y in (
    ("CORNER_GUARD_FL", -ROOM_WIDTH / 2.0 + 0.04, -ROOM_LENGTH / 2.0 + 0.04),
    ("CORNER_GUARD_FR", ROOM_WIDTH / 2.0 - 0.04, -ROOM_LENGTH / 2.0 + 0.04),
    ("CORNER_GUARD_BL", -ROOM_WIDTH / 2.0 + 0.04, ROOM_LENGTH / 2.0 - 0.04),
    ("CORNER_GUARD_BR", ROOM_WIDTH / 2.0 - 0.04, ROOM_LENGTH / 2.0 - 0.04),
):
    create_box(nm, (x, y, 0.275), (0.075, 0.075, 0.55),
               COL_TRIMS, MAT_STRUCTURAL, 0.008)


# ============================================================
# 10 DOORS
# ============================================================

if CREATE_DOORS:
    back_y = ROOM_LENGTH / 2.0 + 0.012
    create_box("DOOR_BACK_LEAF", (0.0, back_y, BACK_DOOR_HEIGHT / 2.0),
               (BACK_DOOR_WIDTH - DOOR_GAP * 2.0,
                DOOR_LEAF_THICKNESS,
                BACK_DOOR_HEIGHT - DOOR_GAP * 2.0),
               COL_DOORS, MAT_DOOR, 0.010)
    create_box("DOOR_BACK_INNER_PANEL", (0.0, back_y - 0.031, BACK_DOOR_HEIGHT / 2.0),
               (BACK_DOOR_WIDTH - 0.16, 0.018, BACK_DOOR_HEIGHT - 0.18),
               COL_DOORS, MAT_DARK_METAL, 0.005)

    create_box("DOOR_BACK_HANDLE_PLATE", (0.34, back_y - 0.048, 1.03),
               (0.09, 0.025, 0.18), COL_DOORS, MAT_DARK_METAL, 0.006)
    create_box("DOOR_BACK_HANDLE", (0.385, back_y - 0.078, 1.03),
               (0.17, 0.055, 0.035), COL_DOORS, MAT_GALV, 0.008)

    for i, z in enumerate((0.45, 1.65)):
        create_box(f"DOOR_BACK_HINGE_{i:02d}",
                   (-BACK_DOOR_WIDTH / 2.0 + 0.045, back_y - 0.040, z),
                   (0.060, 0.040, 0.17), COL_DOORS, MAT_GALV, 0.005)

    side_x = -ROOM_WIDTH / 2.0 - 0.012
    create_box("DOOR_SIDE_LEAF", (side_x, SIDE_DOOR_Y, SIDE_DOOR_HEIGHT / 2.0),
               (DOOR_LEAF_THICKNESS,
                SIDE_DOOR_WIDTH - DOOR_GAP * 2.0,
                SIDE_DOOR_HEIGHT - DOOR_GAP * 2.0),
               COL_DOORS, MAT_DOOR, 0.010)
    create_box("DOOR_SIDE_INNER_PANEL", (side_x + 0.031, SIDE_DOOR_Y, SIDE_DOOR_HEIGHT / 2.0),
               (0.018, SIDE_DOOR_WIDTH - 0.16, SIDE_DOOR_HEIGHT - 0.18),
               COL_DOORS, MAT_DARK_METAL, 0.005)
    create_box("DOOR_SIDE_HANDLE_PLATE", (side_x + 0.048, SIDE_DOOR_Y + 0.34, 1.03),
               (0.025, 0.09, 0.18), COL_DOORS, MAT_DARK_METAL, 0.006)
    create_box("DOOR_SIDE_HANDLE", (side_x + 0.078, SIDE_DOOR_Y + 0.385, 1.03),
               (0.055, 0.17, 0.035), COL_DOORS, MAT_GALV, 0.008)

    for i, z in enumerate((0.45, 1.65)):
        create_box(f"DOOR_SIDE_HINGE_{i:02d}",
                   (side_x + 0.040, SIDE_DOOR_Y - SIDE_DOOR_WIDTH / 2.0 + 0.045, z),
                   (0.040, 0.060, 0.17), COL_DOORS, MAT_GALV, 0.005)


# ============================================================
# 11 STRUCTURAL
# ============================================================

if CREATE_BEAMS:
    for i, y in enumerate(BEAM_Y_POSITIONS):
        create_box(f"CEILING_BEAM_{i:02d}", (0.0, y, BEAM_Z),
                   (ROOM_WIDTH - 0.18, BEAM_WIDTH, BEAM_HEIGHT),
                   COL_CEILING, MAT_STRUCTURAL, 0.008)

        for side, x in (("L", -ROOM_WIDTH / 2.0 + 0.06),
                        ("R", ROOM_WIDTH / 2.0 - 0.06)):
            create_box(f"BEAM_PLATE_{side}_{i:02d}", (x, y, BEAM_Z),
                       (0.12, 0.24, 0.25), COL_STRUCT, MAT_GALV, 0.006)
            # Two readable large bolts on each bearing plate.
            bolt_x = x + (0.066 if side == "L" else -0.066)
            for b, zoff in enumerate((-0.065, 0.065)):
                create_hex_bolt(f"BEAM_BOLT_{side}_{i:02d}_{b:02d}",
                                (bolt_x, y, BEAM_Z + zoff), axis='X',
                                radius=0.022, depth=0.018,
                                collection=COL_STRUCT, material=MAT_DARK_METAL)

if CREATE_TECHNICAL_RAILS:
    for i, x in enumerate(TECH_RAIL_X_POSITIONS):
        create_box(f"TECH_RAIL_{i:02d}", (x, 0.0, TECH_RAIL_Z),
                   (TECH_RAIL_WIDTH, ROOM_LENGTH - 0.80, TECH_RAIL_HEIGHT),
                   COL_INFRA, MAT_STRUCTURAL, 0.005)
        for h, y in enumerate((-4.25, -2.15, 0.0, 2.15, 4.25)):
            create_box(f"TECH_RAIL_{i:02d}_HANGER_{h:02d}",
                       (x, y, TECH_RAIL_Z + 0.12),
                       (0.05, 0.10, 0.24), COL_INFRA, MAT_GALV, 0.003)


# ============================================================
# 12 ELECTRICAL
# ============================================================

JUNCTION_BOX_COUNT = 0
if CREATE_ELECTRICAL:
    panel_y = ROOM_LENGTH / 2.0 - MAIN_PANEL_DEPTH / 2.0 - 0.015
    create_panel_box(
        "MAIN_ELECTRICAL_PANEL",
        (MAIN_PANEL_X, panel_y, MAIN_PANEL_Z),
        (MAIN_PANEL_WIDTH, MAIN_PANEL_DEPTH, MAIN_PANEL_HEIGHT),
        COL_ELECTRICAL, MAT_ELECTRICAL, MAT_GALV,
        face_offset=0.024, bevel=0.018, normal_axis='Y'
    )

    # Selector
    create_box("MAIN_ELECTRICAL_PANEL_SWITCH_BASE",
               (MAIN_PANEL_X, panel_y - MAIN_PANEL_DEPTH / 2.0 - 0.026, MAIN_PANEL_Z),
               (0.17, 0.028, 0.23), COL_ELECTRICAL, MAT_DARK_METAL, 0.010)
    create_box("MAIN_ELECTRICAL_PANEL_SWITCH",
               (MAIN_PANEL_X, panel_y - MAIN_PANEL_DEPTH / 2.0 - 0.052, MAIN_PANEL_Z),
               (0.045, 0.050, 0.14), COL_ELECTRICAL, MAT_GALV, 0.008)

    # Four panel fasteners
    for idx, (dx, dz) in enumerate(((-0.25, -0.34), (0.25, -0.34),
                                    (-0.25, 0.34), (0.25, 0.34))):
        create_hex_bolt(f"MAIN_PANEL_BOLT_{idx:02d}",
                        (MAIN_PANEL_X + dx,
                         panel_y - MAIN_PANEL_DEPTH / 2.0 - 0.043,
                         MAIN_PANEL_Z + dz),
                        axis='Y', radius=0.018, depth=0.016,
                        collection=COL_ELECTRICAL, material=MAT_DARK_METAL)

    # Junction boxes: two left, two right.
    jboxes = (
        ("JBOX_LEFT_01", -ROOM_WIDTH / 2.0 + JUNCTION_BOX_DEPTH / 2.0 + 0.01, -1.10, 1.55, 'X_NEG'),
        ("JBOX_LEFT_02", -ROOM_WIDTH / 2.0 + JUNCTION_BOX_DEPTH / 2.0 + 0.01, 3.15, 2.15, 'X_NEG'),
        ("JBOX_RIGHT_01", ROOM_WIDTH / 2.0 - JUNCTION_BOX_DEPTH / 2.0 - 0.01, -3.30, 1.70, 'X_POS'),
        ("JBOX_RIGHT_02", ROOM_WIDTH / 2.0 - JUNCTION_BOX_DEPTH / 2.0 - 0.01, 2.30, 2.20, 'X_POS'),
    )
    for nm, x, y, z, axis in jboxes:
        create_panel_box(nm, (x, y, z),
                         (JUNCTION_BOX_DEPTH, JUNCTION_BOX_WIDTH, JUNCTION_BOX_HEIGHT),
                         COL_ELECTRICAL, MAT_ELECTRICAL, MAT_GALV,
                         face_offset=0.020, bevel=0.012, normal_axis=axis)
        JUNCTION_BOX_COUNT += 1


# ============================================================
# 13 CONDUITS
# ============================================================

CONDUIT_NETWORK_COUNT = 0
if CREATE_CONDUITS:
    back_y = ROOM_LENGTH / 2.0 - 0.075
    left_x = -ROOM_WIDTH / 2.0 + 0.075
    right_x = ROOM_WIDTH / 2.0 - 0.075

    networks = [
        ("CONDUIT_MAIN_A", [
            (-2.53, back_y, 2.21), (-2.53, back_y, HIGH_CONDUIT_Z),
            (-3.20, back_y, HIGH_CONDUIT_Z)
        ]),
        ("CONDUIT_MAIN_B", [
            (-2.34, back_y, 2.21), (-2.34, back_y, HIGH_CONDUIT_Z - 0.10),
            (-1.50, back_y, HIGH_CONDUIT_Z - 0.10)
        ]),
        ("CONDUIT_BACK_MAIN", [
            (-3.45, back_y, HIGH_CONDUIT_Z), (-1.0, back_y, HIGH_CONDUIT_Z),
            (1.0, back_y, HIGH_CONDUIT_Z), (3.45, back_y, HIGH_CONDUIT_Z)
        ]),
        ("CONDUIT_BACK_SECONDARY", [
            (-3.45, back_y, HIGH_CONDUIT_Z - 0.10),
            (-0.80, back_y, HIGH_CONDUIT_Z - 0.10),
            (1.40, back_y, HIGH_CONDUIT_Z - 0.10),
            (3.45, back_y, HIGH_CONDUIT_Z - 0.10)
        ]),
        ("CONDUIT_LEFT_HIGH", [
            (left_x, 5.35, SIDE_CONDUIT_Z), (left_x, 2.80, SIDE_CONDUIT_Z),
            (left_x, 0.25, SIDE_CONDUIT_Z), (left_x, -2.20, SIDE_CONDUIT_Z),
            (left_x, -5.15, SIDE_CONDUIT_Z)
        ]),
        ("CONDUIT_LEFT_DROP", [
            (left_x, -1.10, SIDE_CONDUIT_Z), (left_x, -1.10, 1.73)
        ]),
        ("CONDUIT_RIGHT_HIGH", [
            (right_x, 5.35, SIDE_CONDUIT_Z), (right_x, 2.75, SIDE_CONDUIT_Z),
            (right_x, 0.10, SIDE_CONDUIT_Z), (right_x, -2.55, SIDE_CONDUIT_Z),
            (right_x, -5.15, SIDE_CONDUIT_Z)
        ]),
        ("CONDUIT_RIGHT_DROP", [
            (right_x, -3.30, SIDE_CONDUIT_Z), (right_x, -3.30, 1.88)
        ]),
    ]

    for nm, pts in networks:
        create_poly_curve(nm, pts, COL_ELECTRICAL, MAT_GALV,
                          radius=CONDUIT_RADIUS, bevel_resolution=2)
        CONDUIT_NETWORK_COUNT += 1

    # Sparse support clamps.
    for i, x in enumerate((-3.10, -1.60, 0.00, 1.60, 3.10)):
        create_box(f"CONDUIT_CLAMP_BACK_{i:02d}",
                   (x, ROOM_LENGTH / 2.0 - 0.045, HIGH_CONDUIT_Z),
                   (0.08, 0.035, 0.09), COL_ELECTRICAL, MAT_STRUCTURAL, 0.003)
    for i, y in enumerate((-4.50, -2.00, 0.50, 3.00, 5.00)):
        create_box(f"CONDUIT_CLAMP_LEFT_{i:02d}",
                   (-ROOM_WIDTH / 2.0 + 0.045, y, SIDE_CONDUIT_Z),
                   (0.035, 0.09, 0.09), COL_ELECTRICAL, MAT_STRUCTURAL, 0.003)
        create_box(f"CONDUIT_CLAMP_RIGHT_{i:02d}",
                   (ROOM_WIDTH / 2.0 - 0.045, y, SIDE_CONDUIT_Z),
                   (0.035, 0.09, 0.09), COL_ELECTRICAL, MAT_STRUCTURAL, 0.003)


# ============================================================
# 14 DUCTS / VENTILATION
# ============================================================

# Stage 2 connection collars / wall mounting points remain visible.
if CREATE_VENTILATION:
    for i, x in enumerate(VENT_PORT_X_POSITIONS):
        create_cylinder(f"VENT_PORT_BACK_{i:02d}_COLLAR",
                        (x, ROOM_LENGTH / 2.0 - VENT_PORT_DEPTH / 2.0 - 0.015, VENT_PORT_Z),
                        VENT_PORT_RADIUS, VENT_PORT_DEPTH,
                        COL_VENT, MAT_GALV,
                        vertices=MEDIUM_CYLINDER_SIDES,
                        rotation=(math.radians(90.0), 0.0, 0.0),
                        bevel=0.004)
        create_cylinder(f"VENT_PORT_BACK_{i:02d}_INNER",
                        (x, ROOM_LENGTH / 2.0 - VENT_PORT_DEPTH - 0.025, VENT_PORT_Z),
                        VENT_PORT_RADIUS * 0.79, 0.018,
                        COL_VENT, MAT_BLACK,
                        vertices=MEDIUM_CYLINDER_SIDES,
                        rotation=(math.radians(90.0), 0.0, 0.0))

    # Sparse side brackets for future duct routing.
    for i, y in enumerate((-1.75, 1.40, 4.35)):
        for side, x in (("L", -ROOM_WIDTH / 2.0 + 0.045),
                        ("R", ROOM_WIDTH / 2.0 - 0.045)):
            create_box(f"VENT_BRACKET_{side}_{i:02d}",
                       (x, y, 3.08), (0.04, 0.28, 0.16),
                       COL_VENT, MAT_STRUCTURAL, 0.005)


DUCT_SEGMENT_COUNT = 0
if CREATE_MAIN_DUCT:
    total = DUCT_MAIN_X_MAX - DUCT_MAIN_X_MIN
    DUCT_SEGMENT_COUNT = max(3, math.ceil(total / DUCT_SEGMENT_TARGET))
    seg_len = total / DUCT_SEGMENT_COUNT

    for i in range(DUCT_SEGMENT_COUNT):
        x1 = DUCT_MAIN_X_MIN + seg_len * i
        x2 = DUCT_MAIN_X_MIN + seg_len * (i + 1)
        create_cylinder_between(f"DUCT_MAIN_BACK_SEG_{i:02d}",
                                (x1, DUCT_CENTER_Y, DUCT_HEIGHT),
                                (x2, DUCT_CENTER_Y, DUCT_HEIGHT),
                                DUCT_RADIUS, COL_DUCTS, MAT_GALV,
                                vertices=LARGE_CYLINDER_SIDES,
                                bevel=0.004, parent=VENT_SYSTEM_ROOT)

        if i > 0:
            create_ring_collar(f"DUCT_MAIN_BACK_RING_{i:02d}",
                               (x1, DUCT_CENTER_Y, DUCT_HEIGHT), 'X',
                               DUCT_RADIUS + DUCT_RING_EXTRA_RADIUS,
                               DUCT_RING_LENGTH, COL_DUCTS, MAT_GALV, VENT_SYSTEM_ROOT)

    # End collars
    create_ring_collar("DUCT_MAIN_BACK_RING_START",
                       (DUCT_MAIN_X_MIN, DUCT_CENTER_Y, DUCT_HEIGHT), 'X',
                       DUCT_RADIUS + DUCT_RING_EXTRA_RADIUS,
                       DUCT_RING_LENGTH, COL_DUCTS, MAT_GALV, VENT_SYSTEM_ROOT)
    create_ring_collar("DUCT_MAIN_BACK_RING_END",
                       (DUCT_MAIN_X_MAX, DUCT_CENTER_Y, DUCT_HEIGHT), 'X',
                       DUCT_RADIUS + DUCT_RING_EXTRA_RADIUS,
                       DUCT_RING_LENGTH, COL_DUCTS, MAT_GALV, VENT_SYSTEM_ROOT)

    # Left segmented 90-degree elbow: horizontal -> descending vertical.
    elbow_points = []
    radius = 0.46
    center_x = DUCT_MAIN_X_MIN
    center_z = DUCT_HEIGHT - radius
    for j in range(DUCT_ELBOW_SEGMENTS + 1):
        t = j / DUCT_ELBOW_SEGMENTS
        theta = math.radians(90.0 * t)
        # Starts at main horizontal end, sweeps left/down.
        x = center_x - radius * math.sin(theta)
        z = center_z + radius * math.cos(theta)
        elbow_points.append((x, DUCT_CENTER_Y, z))

    for j in range(len(elbow_points) - 1):
        create_cylinder_between(f"DUCT_ELBOW_LEFT_SEG_{j:02d}",
                                elbow_points[j], elbow_points[j + 1],
                                DUCT_RADIUS, COL_DUCTS, MAT_GALV,
                                vertices=LARGE_CYLINDER_SIDES,
                                bevel=0.003, parent=VENT_SYSTEM_ROOT)

    # Vertical down leg.
    left_down_x = elbow_points[-1][0]
    left_down_top_z = elbow_points[-1][2]
    left_down_bottom_z = 2.20
    create_cylinder_between("DUCT_LEFT_VERTICAL",
                            (left_down_x, DUCT_CENTER_Y, left_down_top_z),
                            (left_down_x, DUCT_CENTER_Y, left_down_bottom_z),
                            DUCT_RADIUS, COL_DUCTS, MAT_GALV,
                            vertices=LARGE_CYLINDER_SIDES, bevel=0.004,
                            parent=VENT_SYSTEM_ROOT)
    create_ring_collar("DUCT_LEFT_VERTICAL_COLLAR",
                       (left_down_x, DUCT_CENTER_Y, 2.40), 'Z',
                       DUCT_RADIUS + DUCT_RING_EXTRA_RADIUS,
                       DUCT_RING_LENGTH, COL_DUCTS, MAT_GALV, VENT_SYSTEM_ROOT)

    # Short right transition toward right fan/port.
    create_cylinder_between("DUCT_RIGHT_CONNECTOR",
                            (DUCT_MAIN_X_MAX, DUCT_CENTER_Y, DUCT_HEIGHT),
                            (FAN_RIGHT_X - FAN_DIAMETER * 0.56, DUCT_CENTER_Y, FAN_Z),
                            DUCT_RADIUS * 0.92, COL_DUCTS, MAT_GALV,
                            vertices=LARGE_CYLINDER_SIDES, bevel=0.004,
                            parent=VENT_SYSTEM_ROOT)

    # Wall supports / hangers for the main duct.
    for i, x in enumerate(DUCT_SUPPORT_X):
        create_box(f"DUCT_SUPPORT_PLATE_{i:02d}",
                   (x, ROOM_LENGTH / 2.0 - 0.045, DUCT_HEIGHT),
                   (0.20, 0.05, 0.26), COL_DUCTS, MAT_STRUCTURAL, 0.005,
                   parent=VENT_SYSTEM_ROOT)
        create_box(f"DUCT_SUPPORT_ARM_{i:02d}",
                   (x, (ROOM_LENGTH / 2.0 - 0.045 + DUCT_CENTER_Y) / 2.0,
                    DUCT_HEIGHT - DUCT_RADIUS - 0.035),
                   (0.07, abs((ROOM_LENGTH / 2.0 - 0.045) - DUCT_CENTER_Y), 0.07),
                   COL_DUCTS, MAT_STRUCTURAL, 0.004, parent=VENT_SYSTEM_ROOT)
        create_ring_collar(f"DUCT_SUPPORT_CLAMP_{i:02d}",
                           (x, DUCT_CENTER_Y, DUCT_HEIGHT), 'X',
                           DUCT_RADIUS + 0.010, 0.028,
                           COL_DUCTS, MAT_STRUCTURAL, VENT_SYSTEM_ROOT)


# ============================================================
# 15 FANS
# ============================================================

def create_fan(name, x, y, z, diameter, depth, face_normal='Y', parent=None):
    radius = diameter / 2.0

    # Housing axis along Y for back-wall fans.
    if face_normal == 'Y':
        rot = (math.radians(90.0), 0.0, 0.0)
        blade_y = y - depth / 2.0 - 0.018
        hub_loc = (x, blade_y, z)
    else:
        rot = (0.0, math.radians(90.0), 0.0)
        blade_y = y
        hub_loc = (x, y, z)

    create_cylinder(name + "_HOUSING", (x, y, z), radius, depth,
                    COL_FANS, MAT_STRUCTURAL,
                    vertices=LARGE_CYLINDER_SIDES, rotation=rot,
                    bevel=0.008, parent=parent)
    create_cylinder(name + "_INNER", (x, y - depth / 2.0 - 0.012, z),
                    radius * 0.84, 0.030,
                    COL_FANS, MAT_BLACK,
                    vertices=LARGE_CYLINDER_SIDES, rotation=rot,
                    parent=parent)

    hub_radius = radius * 0.22
    create_cylinder(name + "_HUB", hub_loc, hub_radius, 0.07,
                    COL_FANS, MAT_DARK_METAL,
                    vertices=MEDIUM_CYLINDER_SIDES, rotation=rot,
                    bevel=0.004, parent=parent)

    # Blades as efficient beveled boxes, radial in X/Z plane.
    blade_len = radius * 0.58
    blade_w = radius * 0.20
    radial = hub_radius + blade_len * 0.46
    for i in range(FAN_BLADE_COUNT):
        angle = (2.0 * math.pi * i / FAN_BLADE_COUNT) + math.radians(10.0)
        bx = x + math.cos(angle) * radial
        bz = z + math.sin(angle) * radial
        blade = create_box(f"{name}_BLADE_{i:02d}",
                           (bx, blade_y - 0.018, bz),
                           (blade_len, 0.045, blade_w),
                           COL_FANS, MAT_DARK_METAL, 0.015, parent)
        if blade:
            blade.rotation_euler[1] = -angle
            blade.rotation_euler[2] = math.radians(18.0)

    # Front grille: several concentric hoops + radial bars.
    grille_y = y - depth / 2.0 - 0.055
    for r_i in range(1, FAN_GRILLE_RINGS + 1):
        rr = radius * (0.25 + 0.15 * r_i)
        # Create ring as a Bezier circle with bevel for reliability.
        curve_name = f"{name}_GRILLE_RING_{r_i:02d}"
        if not object_exists(curve_name):
            curve_data = bpy.data.curves.new(curve_name + "_DATA", 'CURVE')
            curve_data.dimensions = '3D'
            curve_data.bevel_depth = 0.008
            curve_data.bevel_resolution = 1
            spline = curve_data.splines.new('POLY')
            segs = 32
            spline.points.add(segs)
            for s in range(segs + 1):
                a = 2.0 * math.pi * s / segs
                spline.points[s].co = (x + math.cos(a) * rr, grille_y, z + math.sin(a) * rr, 1.0)
            obj = bpy.data.objects.new(curve_name, curve_data)
            COL_FANS.objects.link(obj)
            curve_data.materials.append(MAT_GALV)
            obj.parent = parent

    for i in range(8):
        a = 2.0 * math.pi * i / 8.0
        p1 = (x + math.cos(a) * hub_radius * 0.95, grille_y, z + math.sin(a) * hub_radius * 0.95)
        p2 = (x + math.cos(a) * radius * 0.90, grille_y, z + math.sin(a) * radius * 0.90)
        create_cylinder_between(f"{name}_GRILLE_BAR_{i:02d}", p1, p2,
                                0.0075, COL_FANS, MAT_GALV,
                                vertices=8, parent=parent)

    # Four bracket tabs and bolts around the housing.
    for i, a in enumerate((45.0, 135.0, 225.0, 315.0)):
        ar = math.radians(a)
        tx = x + math.cos(ar) * radius * 1.06
        tz = z + math.sin(ar) * radius * 1.06
        create_box(f"{name}_TAB_{i:02d}", (tx, y, tz),
                   (0.10, depth * 0.90, 0.10), COL_FANS, MAT_STRUCTURAL, 0.004, parent)
        create_hex_bolt(f"{name}_TAB_BOLT_{i:02d}",
                        (tx, grille_y - 0.008, tz), axis='Y',
                        radius=0.018, depth=0.018,
                        collection=COL_FANS, material=MAT_GALV, parent=parent)


FAN_COUNT = 0
if CREATE_EXHAUST_FANS:
    create_fan("EXHAUST_FAN_LEFT", FAN_LEFT_X, FAN_CENTER_Y, FAN_Z,
               FAN_DIAMETER, FAN_DEPTH, 'Y', VENT_SYSTEM_ROOT)
    create_fan("EXHAUST_FAN_RIGHT", FAN_RIGHT_X, FAN_CENTER_Y, FAN_Z,
               FAN_DIAMETER, FAN_DEPTH, 'Y', VENT_SYSTEM_ROOT)
    FAN_COUNT = 2


# ============================================================
# 16 LIGHTING
# ============================================================

# Two connected frames rather than four independent small racks.
def create_reference_rack(name, center_x):
    xmin = center_x - RACK_DEPTH / 2.0 + RACK_POST_WIDTH / 2.0
    xmax = center_x + RACK_DEPTH / 2.0 - RACK_POST_WIDTH / 2.0
    boundaries = [RACK_Y_MIN + i * RACK_BAY_LENGTH
                  for i in range(RACK_MODULE_COUNT + 1)]
    boundaries[0] += RACK_POST_WIDTH / 2.0
    boundaries[-1] -= RACK_POST_WIDTH / 2.0

    # Four stations share the posts of adjacent bays: one continuous structure.
    for station, yy in enumerate(boundaries):
        for side, xx in (("OUTER", xmin), ("INNER", xmax)):
            create_box(f"{name}_POST_{station:02d}_{side}",
                       (xx, yy, RACK_HEIGHT / 2.0),
                       (RACK_POST_WIDTH, RACK_POST_WIDTH, RACK_HEIGHT),
                       COL_RACKS, MAT_STRUCTURAL, 0.004)
            create_box(f"{name}_FOOT_{station:02d}_{side}",
                       (xx, yy, 0.015), (0.12, 0.12, 0.03),
                       COL_RACKS, MAT_DARK_METAL, 0.003)
        for level, zz in (("BASE", RACK_BASE_Z), ("TOP", RACK_HEIGHT - 0.035)):
            create_box(f"{name}_CROSS_{station:02d}_{level}",
                       (center_x, yy, zz),
                       (RACK_DEPTH, RACK_POST_WIDTH, 0.055),
                       COL_RACKS, MAT_STRUCTURAL, 0.004)

    # Unbroken longitudinal rails along both sides.
    for side, xx in (("A", xmin), ("B", xmax)):
        for level, zz in (("BASE", RACK_BASE_Z), ("TOP", RACK_HEIGHT - 0.035)):
            create_box(f"{name}_LONG_{side}_{level}",
                       (xx, RACK_CENTER_Y, zz),
                       (RACK_POST_WIDTH, RACK_LENGTH, 0.055),
                       COL_RACKS, MAT_STRUCTURAL, 0.004)

    # Open lower platform with individual module trays and support bars.
    for bay, yy in enumerate(LIGHT_Y_POSITIONS):
        create_box(f"{name}_TRAY_{bay:02d}",
                   (center_x, yy, RACK_BASE_Z + 0.035),
                   (RACK_DEPTH - 0.14, RACK_BAY_LENGTH - 0.12, 0.025),
                   COL_RACKS, MAT_DARK_METAL, 0.006)
        for support, offset in enumerate((-0.65, 0.0, 0.65)):
            create_box(f"{name}_SUPPORT_{bay:02d}_{support:02d}",
                       (center_x + offset, yy, RACK_BASE_Z - 0.045),
                       (0.04, RACK_BAY_LENGTH, 0.06),
                       COL_RACKS, MAT_STRUCTURAL, 0.003)
        # Transverse top rail carrying the light at the bay center.
        create_box(f"{name}_LIGHT_RAIL_{bay:02d}",
                   (center_x, yy, LIGHT_HANGER_TOP_Z + 0.025),
                   (RACK_DEPTH - 0.055, 0.045, 0.045),
                   COL_RACKS, MAT_STRUCTURAL, 0.003)


if CREATE_RACKS:
    for side, xx in zip(("LEFT", "RIGHT"), RACK_X_POSITIONS):
        create_reference_rack(f"RACK_{side}", xx)


def create_light_fixture(name, x, y, z, parent=None):
    # Two LED strips in a transverse metal housing, centered on this rack bay.
    length = LIGHT_FIXTURE_LENGTH
    create_box(name + "_BODY", (x, y, z),
               (length, LIGHT_FIXTURE_WIDTH, LIGHT_FIXTURE_HEIGHT),
               COL_LIGHTS, MAT_GALV, 0.007, parent)
    for strip, dy in enumerate((-0.075, 0.075)):
        create_box(f"{name}_CHANNEL_{strip}", (x, y + dy, z - 0.034),
                   (length - 0.14, 0.065, 0.024), COL_LIGHTS, MAT_STRUCTURAL, 0.003, parent)
        create_box(f"{name}_LED_{strip}", (x, y + dy, z - 0.051),
                   (length - 0.20, 0.040, 0.013), COL_LIGHTS, MAT_EMISSION, 0.003, parent)
    for side, dx in (("A", -length / 2.0 + 0.025), ("B", length / 2.0 - 0.025)):
        create_box(f"{name}_END_{side}", (x + dx, y, z - 0.008),
                   (0.055, LIGHT_FIXTURE_WIDTH + 0.018, 0.080),
                   COL_LIGHTS, MAT_STRUCTURAL, 0.005, parent)
    create_box(name + "_DRIVER", (x, y, z + 0.052),
               (0.34, 0.14, 0.048), COL_LIGHTS, MAT_ELECTRICAL, 0.006, parent)
    for idx, dx in enumerate((-length * 0.34, length * 0.34)):
        low = z + LIGHT_FIXTURE_HEIGHT / 2.0
        create_cylinder_between(f"{name}_HANGER_{idx}",
                                (x + dx, y, low), (x + dx, y, LIGHT_HANGER_TOP_Z),
                                0.010, COL_LIGHTS, MAT_GALV, vertices=8, parent=parent)
        create_box(f"{name}_MOUNT_{idx}", (x + dx, y, LIGHT_HANGER_TOP_Z),
                   (0.10, 0.085, 0.018), COL_LIGHTS, MAT_STRUCTURAL, 0.003, parent)
        create_hex_bolt(f"{name}_BOLT_{idx}",
                        (x + dx, y, LIGHT_HANGER_TOP_Z + 0.014), axis='Z',
                        radius=0.012, depth=0.014, collection=COL_LIGHTS,
                        material=MAT_GALV, parent=parent)
    create_bezier_curve(name + "_DRIVER_CABLE",
                        [(x + 0.17, y, z + 0.05), (x + 0.28, y + 0.06, z + 0.072),
                         (x + 0.38, y + 0.065, LIGHT_HANGER_TOP_Z)],
                        COL_LIGHTS, MAT_RUBBER, 0.007, bevel_resolution=1, parent=parent)
    create_bezier_curve(name + "_FEED_CABLE",
                        [(x + 0.38, y + 0.065, LIGHT_HANGER_TOP_Z),
                         (x + 0.62, y + 0.075, LIGHT_HANGER_TOP_Z + 0.025),
                         (x + RACK_DEPTH / 2.0 - 0.06, y + 0.06, LIGHT_HANGER_TOP_Z)],
                        COL_LIGHTS, MAT_RUBBER, 0.009, bevel_resolution=1, parent=parent)
    if CREATE_REAL_LIGHTS:
        create_area_light(name + "_AREA", (x, y, z - 0.09),
                          AREA_LIGHT_ENERGY, AREA_LIGHT_SIZE, AREA_LIGHT_SIZE_Y,
                          COL_LIGHTS)


LIGHT_COUNT = 0
if CREATE_LIGHT_FIXTURES:
    for sx, x in enumerate(LIGHT_X_POSITIONS):
        for sy, y in enumerate(LIGHT_Y_POSITIONS):
            create_light_fixture(f"LIGHT_FIXTURE_{sx:02d}_{sy:02d}",
                                 x, y, LIGHT_FIXTURE_Z, LIGHT_SYSTEM_ROOT)
            LIGHT_COUNT += 1



# ============================================================
# STAGE 5 — GENERIC COMPOSITION PROPS
# ============================================================

def create_hoop(name, center, radius, tube, collection, material, parent=None):
    # Ring lies in local XY; can be parented to a rotated fan assembly.
    cx, cy, cz = center
    points = [(cx + radius * math.cos(i * 2.0 * math.pi / 32),
               cy + radius * math.sin(i * 2.0 * math.pi / 32), cz)
              for i in range(33)]
    return create_poly_curve(name, points, collection, material, tube,
                             bevel_resolution=1, parent=parent)


def create_tapered(name, location, bottom_radius, top_radius, depth, collection, material):
    existing = bpy.data.objects.get(name)
    if existing:
        return existing
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=bottom_radius,
                                    radius2=top_radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    link_object_to_collection(obj, collection)
    assign_material(obj, material)
    add_bevel(obj, 0.008, 2, apply=False)
    return obj


def module_placeholder_offsets(count):
    if count == 3:
        return ((-0.76, 0.0), (0.0, 0.0), (0.76, 0.0))
    if count == 4:
        return ((-0.55, -0.55), (0.55, -0.55), (-0.55, 0.55), (0.55, 0.55))
    raise ValueError("Use three or four placeholders per bay")


def create_plant_placeholder(name, x, y, variant):
    bottom = PLATFORM_TOP_Z
    top = bottom + POT_HEIGHT
    create_tapered(name + "_POT", (x, y, bottom + POT_HEIGHT / 2.0),
                   POT_BOTTOM_RADIUS, POT_TOP_RADIUS, POT_HEIGHT,
                   COL_PLACEHOLDERS, MAT_POT)
    create_hoop(name + "_RIM", (x, y, top), POT_TOP_RADIUS, 0.015,
                COL_PLACEHOLDERS, MAT_POT)
    create_cylinder(name + "_FILL", (x, y, top + 0.001), POT_TOP_RADIUS - 0.018,
                    0.008, COL_PLACEHOLDERS, MAT_POT_FILL, vertices=20)
    create_cylinder(name + "_STEM", (x, y, (top + CANOPY_CENTER_Z) / 2.0),
                    0.022, CANOPY_CENTER_Z - top, COL_PLACEHOLDERS,
                    MAT_PLACEHOLDER_A, vertices=8)
    canopy = bpy.data.objects.get(name + "_CANOPY")
    if canopy is None:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0,
                                             location=(x, y, CANOPY_CENTER_Z))
        canopy = bpy.context.object
        canopy.name = name + "_CANOPY"
        canopy.dimensions = CANOPY_DIMENSIONS
        apply_scale(canopy)
        link_object_to_collection(canopy, COL_PLACEHOLDERS)
        assign_material(canopy, MAT_PLACEHOLDER_A if variant % 2 == 0 else MAT_PLACEHOLDER_B)
    canopy["purpose"] = "Generic canopy volume for visual composition only"


PLACEHOLDER_COUNT = 0
if CREATE_RACKS and CREATE_PLANT_PLACEHOLDERS:
    for side, xx in zip(("LEFT", "RIGHT"), RACK_X_POSITIONS):
        for bay, yy in enumerate(LIGHT_Y_POSITIONS):
            for index, (dx, dy) in enumerate(module_placeholder_offsets(PLACEHOLDERS_PER_MODULE)):
                create_plant_placeholder(f"PLACEHOLDER_{side}_{bay:02d}_{index:02d}",
                                          xx + dx, yy + dy, bay + index)
                PLACEHOLDER_COUNT += 1


def create_closed_container(name, x, y, bottom, width=0.36, depth=0.30, height=0.36):
    create_box(name + "_BODY", (x, y, bottom + height / 2.0),
               (width, depth, height), COL_TECH_PROPS, MAT_CONTAINER, 0.024)
    create_box(name + "_LID", (x, y, bottom + height + 0.015),
               (width + 0.015, depth + 0.015, 0.035), COL_TECH_PROPS, MAT_CRATE, 0.008)
    create_box(name + "_HANDLE", (x, y, bottom + height + 0.045),
               (width * 0.40, 0.065, 0.035), COL_TECH_PROPS, MAT_DARK_METAL, 0.01)


if CREATE_TECHNICAL_PROPS:
    # Back zone begins beyond the rack ends; the rear door approach remains open.
    tx, ty = -3.08, 5.08
    create_cylinder("TECH_BLUE_TANK_BODY", (tx, ty, 0.87), 0.55, 1.62,
                    COL_TECH_PROPS, MAT_BLUE_TANK, vertices=32, bevel=0.07)
    for index, zz in enumerate((0.17, 0.53, 1.15, 1.56)):
        create_hoop(f"TECH_BLUE_TANK_RIB_{index}", (tx, ty, zz), 0.555, 0.017,
                    COL_TECH_PROPS, MAT_BLUE_TANK)
    create_cylinder("TECH_BLUE_TANK_LID", (tx, ty, 1.70), 0.48, 0.07,
                    COL_TECH_PROPS, MAT_BLUE_TANK, vertices=32, bevel=0.025)
    create_cylinder("TECH_BLUE_TANK_CAP", (tx, ty, 1.77), 0.12, 0.08,
                    COL_TECH_PROPS, MAT_DARK_METAL, vertices=20, bevel=0.01)
    # Cabinet under the existing electrical panel.
    create_box("TECH_CABINET_BODY", (-1.55, 5.42, 0.49), (0.84, 0.67, 0.92),
               COL_TECH_PROPS, MAT_ELECTRICAL, 0.02)
    for index, xx in enumerate((-1.765, -1.335)):
        create_box(f"TECH_CABINET_DOOR_{index}", (xx, 5.073, 0.51), (0.405, 0.025, 0.84),
                   COL_TECH_PROPS, MAT_GALV, 0.008)
        create_box(f"TECH_CABINET_HANDLE_{index}", (xx + (0.12 if index == 0 else -0.12), 5.04, 0.56),
                   (0.025, 0.035, 0.16), COL_TECH_PROPS, MAT_DARK_METAL, 0.005)
    # Steel bench on the right of the door, with lower shelf and four legs.
    bx, by = 1.70, 5.27
    create_box("TECH_BENCH_TOP", (bx, by, 0.96), (1.72, 0.78, 0.065),
               COL_TECH_PROPS, MAT_GALV, 0.012)
    create_box("TECH_BENCH_LOWER", (bx, by, 0.24), (1.58, 0.64, 0.04),
               COL_TECH_PROPS, MAT_STRUCTURAL, 0.006)
    for a, dx in enumerate((-0.77, 0.77)):
        for b, dy in enumerate((-0.30, 0.30)):
            create_box(f"TECH_BENCH_LEG_{a}_{b}", (bx + dx, by + dy, 0.47),
                       (0.06, 0.06, 0.94), COL_TECH_PROPS, MAT_GALV, 0.004)
    create_closed_container("TECH_BENCH_CASE_A", 1.20, by, 0.9925, 0.35, 0.33, 0.27)
    create_closed_container("TECH_BENCH_CASE_B", 1.76, by + 0.06, 0.9925, 0.36, 0.28, 0.36)
    create_closed_container("TECH_BENCH_CASE_LOWER", 1.62, by, 0.26, 0.60, 0.45, 0.37)
    # Four-tier shelf at the rear-right corner.
    sx, sy = 3.24, 5.28
    for a, dx in enumerate((-0.48, 0.48)):
        for b, dy in enumerate((-0.32, 0.32)):
            create_box(f"TECH_SHELF_POST_{a}_{b}", (sx + dx, sy + dy, 0.98),
                       (0.045, 0.045, 1.96), COL_TECH_PROPS, MAT_STRUCTURAL, 0.003)
    for level, zz in enumerate((0.20, 0.76, 1.32, 1.88)):
        create_box(f"TECH_SHELF_BOARD_{level}", (sx, sy, zz), (1.04, 0.70, 0.04),
                   COL_TECH_PROPS, MAT_GALV, 0.006)
    for level, bottom in enumerate((0.22, 0.78, 1.34)):
        for index, xx in enumerate((3.00, 3.48)):
            create_closed_container(f"TECH_SHELF_CASE_{level}_{index}", xx, sy, bottom,
                                    0.35, 0.40, 0.31 + 0.035 * index)
    # Closed generic bucket, set beside the bench without blocking the door.
    create_tapered("TECH_BUCKET_BODY", (2.60, 4.48, 0.19), 0.14, 0.18, 0.38,
                   COL_TECH_PROPS, MAT_BUCKET)
    create_cylinder("TECH_BUCKET_LID", (2.60, 4.48, 0.39), 0.19, 0.025,
                    COL_TECH_PROPS, MAT_BUCKET, vertices=24, bevel=0.008)
    create_bezier_curve("TECH_BUCKET_HANDLE",
                        [(2.42, 4.48, 0.30), (2.43, 4.48, 0.56),
                         (2.77, 4.48, 0.56), (2.78, 4.48, 0.30)],
                        COL_TECH_PROPS, MAT_GALV, 0.008, bevel_resolution=1)


# Embedded in the standalone Stage 6 script by _build_stage6.py.
def create_hollow_transition(name, radius_back, radius_front, z_back, z_front,
                             collection, material, parent=None, wall=0.014):
    """Open sheet-metal sleeve/bell in local Z; no disk obscures the fan blades."""
    existing = bpy.data.objects.get(name)
    if existing:
        return existing
    segments = 40
    vertices = []
    for radius, zz in ((radius_back, z_back), (radius_front, z_front),
                       (radius_back - wall, z_back), (radius_front - wall, z_front)):
        vertices.extend((radius * math.cos(i * math.tau / segments),
                         radius * math.sin(i * math.tau / segments), zz)
                        for i in range(segments))
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.extend(((i, j, segments + j, segments + i),
                      (2 * segments + i, 3 * segments + i, 3 * segments + j, 2 * segments + j),
                      (i, 2 * segments + i, 2 * segments + j, j),
                      (segments + i, segments + j, 3 * segments + j, 3 * segments + i)))
    mesh = bpy.data.meshes.new(name + '_DATA')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    obj.parent = parent
    shade_smooth(obj)
    return obj


def create_axial_rotor(name, radius, collection, parent, face_z=0.0):
    # Local +Z is the visible/air-facing side of the assembly.
    for blade_index in range(7):
        angle = blade_index * math.tau / 7.0
        radial = radius * 0.53
        blade = create_box(f'{name}_BLADE_{blade_index:02d}',
                           (radial * math.cos(angle), radial * math.sin(angle), face_z - 0.065),
                           (radius * 0.73, radius * 0.24, 0.023),
                           collection, MAT_GALV, 0.022, parent)
        blade.rotation_euler = (0.0, math.radians(13.0), angle + 0.20)
    create_cylinder(name + '_HUB', (0.0, 0.0, face_z - 0.030), radius * 0.20, 0.095,
                    collection, MAT_STRUCTURAL, vertices=24, bevel=0.008, parent=parent)
    for ring, factor in enumerate((0.30, 0.47, 0.65, 0.82, 0.97)):
        create_hoop(f'{name}_GRILLE_RING_{ring:02d}', (0, 0, face_z + 0.018),
                    radius * factor, 0.006, collection, MAT_DARK_METAL, parent)
    for spoke in range(12):
        angle = spoke * math.tau / 12
        create_cylinder_between(f'{name}_GRILLE_SPOKE_{spoke:02d}',
                                (0, 0, face_z + 0.028),
                                (radius * math.cos(angle), radius * math.sin(angle), face_z + 0.008),
                                0.005, collection, MAT_GALV, vertices=6, parent=parent)
    create_cylinder(name + '_CENTER_BADGE', (0, 0, face_z + 0.039), radius * 0.115, 0.012,
                    collection, MAT_GALV, vertices=20, bevel=0.003, parent=parent)


def create_side_fan(name, side, yy):
    # The front-left fan stays clear of the side door opening and its trim.
    if side < 0 and abs(yy - SIDE_DOOR_Y) < 0.85:
        yy = SIDE_DOOR_Y + SIDE_DOOR_WIDTH / 2.0 + 0.65
    root = ensure_empty(name + '_ROOT', COL_SIDE_FANS,
                        (side * (ROOM_WIDTH / 2.0 - 0.17), yy, SIDE_FAN_Z), size=0.09)
    root.rotation_euler = (0, -side * math.pi / 2.0, 0)
    root['face_direction'] = 'inward toward racks'
    root['nominal_diameter_m'] = SIDE_FAN_DIAMETER
    radius = SIDE_FAN_DIAMETER / 2.0
    frame_width = SIDE_FAN_DIAMETER + 0.14
    half_frame = (frame_width - 0.065) / 2
    for index, offset in enumerate((-half_frame, half_frame)):
        create_box(f'{name}_FRAME_H_{index}', (0, offset, -0.035),
                   (frame_width, 0.065, 0.18), COL_SIDE_FANS, MAT_STRUCTURAL, 0.007, root)
        create_box(f'{name}_FRAME_V_{index}', (offset, 0, -0.035),
                   (0.065, frame_width, 0.18), COL_SIDE_FANS, MAT_STRUCTURAL, 0.007, root)
    create_hollow_transition(name + '_CASING', radius + 0.018, radius + 0.018,
                             -0.12, 0.070, COL_SIDE_FANS, MAT_GALV, root)
    create_hoop(name + '_FRONT_FLANGE', (0, 0, 0.070), radius + 0.019, 0.015,
                COL_SIDE_FANS, MAT_STRUCTURAL, root)
    create_axial_rotor(name, radius, COL_SIDE_FANS, root, face_z=0.074)
    for index, (xx, yy_local) in enumerate(((-half_frame, -half_frame), (-half_frame, half_frame),
                                           (half_frame, -half_frame), (half_frame, half_frame))):
        create_hex_bolt(f'{name}_BOLT_{index}', (xx, yy_local, 0.062), axis='Z',
                        radius=0.018, depth=0.020, collection=COL_SIDE_FANS,
                        material=MAT_GALV, parent=root)
    create_bezier_curve(name + '_POWER_CABLE',
                        [(0.15, half_frame, -0.09), (0.16, half_frame + 0.10, -0.07),
                         (0.37, half_frame + 0.14, -0.12)],
                        COL_SIDE_FANS, MAT_RUBBER, 0.009, bevel_resolution=1, parent=root)


SIDE_FAN_COUNT = 0
if CREATE_SIDE_FANS:
    for side, label in ((-1, "LEFT"), (1, "RIGHT")):
        for bay, yy in enumerate(LIGHT_Y_POSITIONS):
            create_side_fan(f"SIDE_FAN_{label}_{bay:02d}", side, yy)
            SIDE_FAN_COUNT += 1


# Embedded into the standalone Stage 6 script. Generic environment dressing.
def create_wall_services():
    # Three metal pipe runs, upper ladder trays, bundled cables and vertical drops.
    # All longitudinal runs clear the enlarged fan housings and door headers.
    for side, label in ((-1, 'LEFT'), (1, 'RIGHT')):
        wall_x = side * (ROOM_WIDTH / 2.0 - 0.085)
        for run, (zz, radius) in enumerate(((3.16, 0.038), (3.30, 0.028), (3.43, 0.020))):
            create_cylinder_between(f'SERVICE_{label}_MAIN_PIPE_{run}',
                                    (wall_x, -5.30, zz), (wall_x, 5.38, zz),
                                    radius, COL_WALL_SERVICES, MAT_GALV, vertices=16)
            for clamp, yy in enumerate((-5.15, -2.65, -0.15, 2.35, 4.85)):
                create_ring_collar(f'SERVICE_{label}_PIPE_CLAMP_{run}_{clamp}',
                                   (wall_x, yy, zz), 'Y', radius + 0.014, 0.038,
                                   COL_WALL_SERVICES, MAT_STRUCTURAL)
                create_box(f'SERVICE_{label}_PIPE_STANDOFF_{run}_{clamp}',
                           (side * 3.97, yy, zz), (0.05, 0.055, 0.08),
                           COL_WALL_SERVICES, MAT_GALV, 0.003)

        # Ladder tray above the fans, spaced inward from the pipe runs.
        tray_x = side * 3.62
        for rail, dx in enumerate((-0.10, 0.10)):
            create_box(f'SERVICE_{label}_TRAY_RAIL_{rail}', (tray_x + dx, 0, 3.37),
                       (0.018, 10.90, 0.06), COL_WALL_SERVICES, MAT_GALV, 0.003)
        for rung in range(28):
            yy = -5.35 + rung * 10.70 / 27
            create_box(f'SERVICE_{label}_TRAY_RUNG_{rung:02d}', (tray_x, yy, 3.35),
                       (0.20, 0.022, 0.018), COL_WALL_SERVICES, MAT_GALV, 0.002)
        for cable, dx in enumerate((-0.061, -0.030, 0.0, 0.030, 0.061)):
            points = [(tray_x + dx, yy, 3.37 + 0.006 * math.sin(index * 1.8 + cable))
                      for index, yy in enumerate((-5.35, -3.3, -1.25, 0.8, 2.9, 5.30))]
            create_bezier_curve(f'SERVICE_{label}_CABLE_BUNDLE_{cable}', points,
                                COL_WALL_SERVICES, MAT_CABLE_ACCENT if cable == 0 else MAT_RUBBER,
                                0.009, bevel_resolution=1)

        for drop, yy in enumerate((-4.82, -0.20, 3.85)):
            # Drops avoid the side door and are kept in the 25 cm wall clearance.
            for run, offset in enumerate((-0.07, 0.07)):
                create_poly_curve(f'SERVICE_{label}_VERTICAL_PIPE_{drop}_{run}',
                                  [(wall_x, yy + offset + 0.12, 3.16),
                                   (wall_x, yy + offset, 3.04),
                                   (wall_x, yy + offset, 0.52)],
                                  COL_WALL_SERVICES, MAT_GALV, 0.026, bevel_resolution=2)
                for clamp, zz in enumerate((0.70, 1.45, 2.20, 2.87)):
                    create_ring_collar(f'SERVICE_{label}_DROP_CLAMP_{drop}_{run}_{clamp}',
                                       (wall_x, yy + offset, zz), 'Z', 0.038, 0.036,
                                       COL_WALL_SERVICES, MAT_STRUCTURAL)
            create_box(f'SERVICE_{label}_JUNCTION_{drop}', (side * 3.92, yy + 0.28, 2.36),
                       (0.12, 0.22, 0.30), COL_WALL_SERVICES, MAT_ELECTRICAL, 0.014)
            create_box(f'SERVICE_{label}_JUNCTION_FACE_{drop}', (side * 3.852, yy + 0.28, 2.36),
                       (0.015, 0.19, 0.265), COL_WALL_SERVICES, MAT_GALV, 0.005)
            create_bezier_curve(f'SERVICE_{label}_CABLE_DROP_{drop}',
                                [(tray_x, yy + 0.30, 3.37), (side * 3.83, yy + 0.32, 3.12),
                                 (side * 3.84, yy + 0.32, 2.69), (side * 3.88, yy + 0.28, 2.51)],
                                COL_WALL_SERVICES, MAT_RUBBER, 0.014, bevel_resolution=2)

    # Rear services bridge above the door rather than across its opening.
    for run, zz in enumerate((2.55, 2.70)):
        create_poly_curve(f'SERVICE_BACK_PIPE_{run}',
                          [(-3.87, 5.45, zz), (-3.75, 5.85, zz),
                           (3.75, 5.85, zz), (3.87, 5.45, zz)],
                          COL_WALL_SERVICES, MAT_GALV, 0.028, bevel_resolution=2)
    for cable in range(3):
        zz = 2.38 + cable * 0.032
        create_bezier_curve(f'SERVICE_BACK_CABLE_{cable}',
                            [(-3.78, 5.91, zz), (-1.95, 5.89, zz - 0.018),
                             (0, 5.91, zz), (1.95, 5.89, zz - 0.018), (3.78, 5.91, zz)],
                            COL_WALL_SERVICES, MAT_RUBBER, 0.010, bevel_resolution=1)


def create_ceiling_ducts():
    radius = CEILING_DUCT_DIAMETER / 2.0
    y_start, y_end = -5.10, DUCT_CENTER_Y
    sections = 10
    for segment in range(sections):
        a = y_start + (y_end - y_start) * segment / sections
        b = y_start + (y_end - y_start) * (segment + 1) / sections
        create_cylinder_between(f'CEILING_DUCT_MAIN_{segment:02d}',
                                (0, a, CEILING_DUCT_Z), (0, b, CEILING_DUCT_Z),
                                radius, COL_CEILING_DUCTS, MAT_GALV, vertices=40, bevel=0.004)
        create_ring_collar(f'CEILING_DUCT_JOINT_{segment:02d}',
                           (0, a, CEILING_DUCT_Z), 'Y', radius + 0.023, 0.048,
                           COL_CEILING_DUCTS, MAT_GALV)
        # Fine seam around each segment, giving the sheet metal a readable scale.
        create_ring_collar(f'CEILING_DUCT_SEAM_{segment:02d}',
                           (0, (a + b) / 2.0, CEILING_DUCT_Z), 'Y', radius + 0.005, 0.014,
                           COL_CEILING_DUCTS, MAT_DARK_METAL)
    create_ring_collar('CEILING_DUCT_REAR_JOIN', (0, y_end, CEILING_DUCT_Z),
                       'Y', radius + 0.025, 0.075, COL_CEILING_DUCTS, MAT_GALV)
    # The transverse rear duct and this trunk meet at a short vertical adapter.
    create_cylinder_between('CEILING_DUCT_REAR_ADAPTER', (0, y_end, DUCT_HEIGHT),
                            (0, y_end, CEILING_DUCT_Z), radius * 0.80,
                            COL_CEILING_DUCTS, MAT_GALV, vertices=32)
    create_cylinder_between('CEILING_DUCT_FRONT_CAP', (0, y_start - 0.025, CEILING_DUCT_Z),
                            (0, y_start, CEILING_DUCT_Z), radius + 0.006,
                            COL_CEILING_DUCTS, MAT_GALV, vertices=40)

    for mount, yy in enumerate((-4.55, -1.90, 0.60, 3.15, 5.20)):
        # Slender transverse channels at slab level; a suspended cradle below.
        create_box(f'CEILING_DUCT_CROSS_RAIL_{mount}', (0, yy, 3.555),
                   (ROOM_WIDTH - 0.20, 0.065, 0.055), COL_CEILING_DUCTS, MAT_GALV, 0.003)
        create_box(f'CEILING_DUCT_CRADLE_{mount}', (0, yy, 2.79),
                   (1.16, 0.055, 0.050), COL_CEILING_DUCTS, MAT_STRUCTURAL, 0.004)
        for side, xx in enumerate((-0.54, 0.54)):
            create_cylinder_between(f'CEILING_DUCT_HANGER_{mount}_{side}',
                                    (xx, yy, 2.79), (xx, yy, 3.54),
                                    0.009, COL_CEILING_DUCTS, MAT_GALV, vertices=8)
            create_hex_bolt(f'CEILING_DUCT_HANGER_NUT_{mount}_{side}',
                            (xx, yy, 2.755), axis='Z', radius=0.018, depth=0.020,
                            collection=COL_CEILING_DUCTS, material=MAT_GALV)
        create_ring_collar(f'CEILING_DUCT_STRAP_{mount}', (0, yy, CEILING_DUCT_Z),
                           'Y', radius + 0.014, 0.055, COL_CEILING_DUCTS, MAT_STRUCTURAL)

    for vent, yy in enumerate(LIGHT_Y_POSITIONS):
        name = f'CEILING_VENT_{vent:02d}'
        root = ensure_empty(name + '_ROOT', COL_CEILING_DUCTS,
                            (0, yy, CEILING_VENT_FACE_Z), size=0.10)
        root.rotation_euler = (math.pi, 0, 0)
        root['face_direction'] = 'vertically downward'
        root['nominal_diameter_m'] = CEILING_VENT_DIAMETER
        r = CEILING_VENT_DIAMETER / 2.0
        create_hollow_transition(name + '_NECK', 0.27, 0.27, -0.64, -0.27,
                                 COL_CEILING_DUCTS, MAT_GALV, root)
        create_hollow_transition(name + '_BELL', 0.27, r, -0.27, 0.0,
                                 COL_CEILING_DUCTS, MAT_GALV, root)
        create_hoop(name + '_NECK_COLLAR', (0, 0, -0.29), 0.283, 0.017,
                    COL_CEILING_DUCTS, MAT_STRUCTURAL, root)
        create_hoop(name + '_FRONT_FLANGE', (0, 0, 0), r + 0.010, 0.019,
                    COL_CEILING_DUCTS, MAT_STRUCTURAL, root)
        create_axial_rotor(name, r - 0.025, COL_CEILING_DUCTS, root, face_z=0.008)
        for bolt in range(8):
            angle = bolt * math.tau / 8
            create_hex_bolt(f'{name}_FLANGE_BOLT_{bolt}',
                            ((r + 0.008) * math.cos(angle), (r + 0.008) * math.sin(angle), 0.024),
                            axis='Z', radius=0.012, depth=0.018,
                            collection=COL_CEILING_DUCTS, material=MAT_GALV, parent=root)


if CREATE_WALL_SERVICES:
    create_wall_services()
if CREATE_CEILING_DUCTS:
    create_ceiling_ducts()

# The roof stays renderable from inside and can be shown in the viewport when needed.
if CREATE_CEILING:
    roof = bpy.data.objects.get('CEILING_SLAB')
    if roof:
        roof.hide_set(True)
        roof['viewport_note'] = 'Hidden for interior editing; enable the eye icon to show the roof.'



# ============================================================
# 17 MATERIAL REFINEMENT / WORLD
# ============================================================

world = scene.world
if world is None:
    world = bpy.data.worlds.new("ENV_World")
    scene.world = world
world.use_nodes = True
background = world.node_tree.nodes.get("Background")
if background:
    background.inputs["Color"].default_value = (0.025, 0.027, 0.030, 1.0)
    background.inputs["Strength"].default_value = WORLD_STRENGTH

# Improve viewport render defaults without forcing a final look.
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue


# ============================================================
# 18 ORGANIZATION / OPTIONAL PREVIEW CAMERA
# ============================================================

if CREATE_PREVIEW_CAMERA:
    cam = bpy.data.objects.get("PREVIEW_CAMERA")
    if cam is None:
        cam_data = bpy.data.cameras.new("PREVIEW_CAMERA_DATA")
        cam = bpy.data.objects.new("PREVIEW_CAMERA", cam_data)
        ROOT.objects.link(cam)
    cam.location = PREVIEW_CAMERA_LOCATION
    look_at(cam, PREVIEW_CAMERA_TARGET)
    cam.data.lens = 38.0
    scene.camera = cam

# Dashed relationship lines connect fixture parts to their root, not light rays.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.overlay.show_relationship_lines = False

# Keep root reference objects easy to identify.
WAREHOUSE_ORIGIN.hide_render = True
VENT_SYSTEM_ROOT.hide_render = True
LIGHT_SYSTEM_ROOT.hide_render = True


# ============================================================
# 19 VALIDATION
# ============================================================

def validate_object(name):
    return bpy.data.objects.get(name) is not None


validation = {
    "architecture": validate_object("WALL_RIGHT") and validate_object("WALL_BACK_LEFT"),
    "back_door": validate_object("DOOR_BACK_LEAF") if CREATE_DOORS else True,
    "side_door": validate_object("DOOR_SIDE_LEAF") if CREATE_DOORS else True,
    "drain": validate_object("DRAIN_CHANNEL") if CREATE_DRAIN else True,
    "main_panel": validate_object("MAIN_ELECTRICAL_PANEL_BODY") if CREATE_ELECTRICAL else True,
    "main_duct": validate_object("DUCT_MAIN_BACK_SEG_00") if CREATE_MAIN_DUCT else True,
    "fans": (validate_object("EXHAUST_FAN_LEFT_HOUSING") and
             validate_object("EXHAUST_FAN_RIGHT_HOUSING")) if CREATE_EXHAUST_FANS else True,
    "racks": (validate_object("RACK_LEFT_POST_00_OUTER") and
              validate_object("RACK_RIGHT_POST_00_OUTER")) if CREATE_RACKS else True,
    "lights": validate_object("LIGHT_FIXTURE_00_00_BODY") if CREATE_LIGHT_FIXTURES else True,
}

# Count generated objects that are members of any Stage 3 collection.
generated_names = set()
for col in (COL_SHELL, COL_DOORS, COL_TRIMS, COL_FLOOR, COL_INFRA,
            COL_CEILING, COL_ELECTRICAL, COL_VENT, COL_LIGHT_POINTS,
            COL_DUCTS, COL_FANS, COL_LIGHTS, COL_STRUCT, COL_RACKS,
            COL_PLACEHOLDERS, COL_TECH_PROPS, COL_SIDE_FANS, COL_WALL_SERVICES, COL_CEILING_DUCTS):
    for obj in col.all_objects:
        generated_names.add(obj.name)
TOTAL_GENERATED_OBJECTS = len(generated_names)


# ============================================================
# 20 SUMMARY
# ============================================================

print("")
print("=" * 72)
print("WAREHOUSE ENVIRONMENT — STAGE 6 INFRASTRUCTURE COMPLETED")
print("=" * 72)
print(f"Room:                     {ROOM_WIDTH:.2f}m x {ROOM_LENGTH:.2f}m x {WALL_HEIGHT:.2f}m")
print(f"Architecture:             {'OK' if validation['architecture'] else 'CHECK'}")
print(f"Doors:                    {2 if CREATE_DOORS else 0}")
print(f"Front Gate Opening:       {FRONT_GATE_WIDTH:.2f}m x {FRONT_GATE_HEIGHT:.2f}m")
print(f"Central Drain:            {'OK' if validation['drain'] else 'CHECK'}")
print(f"Drain Modules:            {DRAIN_MODULE_COUNT}")
print(f"Structural Beams:         {len(BEAM_Y_POSITIONS) if CREATE_BEAMS else 0}")
print(f"Technical Rails:          {len(TECH_RAIL_X_POSITIONS) if CREATE_TECHNICAL_RAILS else 0}")
print(f"Electrical Main Panel:    {1 if CREATE_ELECTRICAL else 0}")
print(f"Junction Boxes:           {JUNCTION_BOX_COUNT}")
print(f"Conduit Networks:         {CONDUIT_NETWORK_COUNT}")
print(f"Main HVAC Duct:           {'OK' if validation['main_duct'] else 'CHECK'}")
print(f"Duct Diameter:            {DUCT_DIAMETER:.2f}m")
print(f"Duct Main Segments:       {DUCT_SEGMENT_COUNT}")
print(f"Industrial Fans:          {FAN_COUNT}")
print(f"Industrial Lights:        {LIGHT_COUNT}")
print(f"Real Area Lights:         {'Enabled' if CREATE_REAL_LIGHTS else 'Disabled'}")
print(f"Ceiling:                  {'Enabled' if CREATE_CEILING else 'Disabled'}")
print("Materials:")
print("  - Concrete Wall XZ / YZ")
print("  - Concrete Floor")
print("  - Structural Dark Steel")
print("  - Galvanized Steel")
print("  - Door Metal")
print("  - Electrical Metal")
print("  - Emissive Light Diffuser")
print(f"Total Generated Objects:  {TOTAL_GENERATED_OBJECTS}")
print("Validation:")
for key, ok in validation.items():
    print(f"  - {key:<18} {'OK' if ok else 'CHECK'}")
print("")
print(f"Continuous Side Racks:    {2 if CREATE_RACKS else 0}")
print(f"Bays Per Rack:            {RACK_MODULE_COUNT}")
print(f"Rack Size:                {RACK_DEPTH:.2f} x {RACK_LENGTH:.2f} x {RACK_HEIGHT:.2f}m")
print(f"Wall Clearance:           {RACK_WALL_CLEARANCE:.2f}m")
print(f"Central Corridor:         {CENTRAL_CORRIDOR_WIDTH:.2f}m")
print(f"Rack/Light X Centers:     {RACK_X_POSITIONS}")
print(f"Generic Plant Volumes:    {PLACEHOLDER_COUNT}")
print(f"Volumes Per Module:      {PLACEHOLDERS_PER_MODULE}")
print(f"Side Fans:               {SIDE_FAN_COUNT}")
print(f"Wall Fan Diameter:       {SIDE_FAN_DIAMETER:.2f}m")
print(f"Ceiling Main Duct:       {CEILING_DUCT_DIAMETER:.2f}m")
print(f"Ceiling Vents:           {len(LIGHT_Y_POSITIONS) if CREATE_CEILING_DUCTS else 0}")
print(f"Vent Diameter:           {CEILING_VENT_DIAMETER:.2f}m")
print("Stage 6 infrastructure ready. Pink LEDs preserved.")
print("=" * 72)
print("")


# Pink LED bloom and visible diffuser edges.
LED_AREA_ENERGY = AREA_LIGHT_ENERGY
LED_EMISSION_STRENGTH = LIGHT_EMISSION_STRENGTH
def configure_led_glow(scene):
    """Add a subtle Fog Glow after the current compositor, Blender 4.x/5.x."""
    if hasattr(scene, 'compositing_node_group'):
        tree = scene.compositing_node_group
        if tree is None:
            tree = bpy.data.node_groups.new('WAREHOUSE_LED_COMPOSITOR', 'CompositorNodeTree')
            tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
            scene.compositing_node_group = tree
        output = next((n for n in tree.nodes if n.type == 'GROUP_OUTPUT' and n.is_active_output), None)
        if output is None:
            output = tree.nodes.new('NodeGroupOutput')
        destination = output.inputs.get('Image')
        if destination is None:
            print('LED glow skipped: existing compositor has no Image output.')
            return
    else:
        scene.use_nodes = True
        tree = scene.node_tree
        output = next((n for n in tree.nodes if n.type == 'COMPOSITE'), None)
        if output is None:
            output = tree.nodes.new('CompositorNodeComposite')
        destination = output.inputs['Image']

    glow = tree.nodes.get('WAREHOUSE_LED_PINK_GLOW')
    if glow is None:
        # Preserve any existing compositing by inserting the glow at the output.
        if destination.is_linked:
            source = destination.links[0].from_socket
        else:
            layers = next((n for n in tree.nodes if n.type == 'R_LAYERS'), None)
            if layers is None:
                layers = tree.nodes.new('CompositorNodeRLayers')
            source = layers.outputs['Image']
        glow = tree.nodes.new('CompositorNodeGlare')
        glow.name = 'WAREHOUSE_LED_PINK_GLOW'
        glow.label = 'LED rosa - brilho suave'
        glow.location = (output.location.x - 240, output.location.y)
        tree.links.new(source, glow.inputs['Image'])
        tree.links.new(glow.outputs['Image'], destination)

    # Blender 5 exposes settings as sockets; older versions use node attributes.
    if glow.inputs.get('Type') is not None:
        glow.inputs['Type'].default_value = 'Fog Glow'
    elif hasattr(glow, 'glare_type'):
        glow.glare_type = 'FOG_GLOW'
    if glow.inputs.get('Quality') is not None:
        glow.inputs['Quality'].default_value = 'High'
    elif hasattr(glow, 'quality'):
        glow.quality = 'HIGH'
    if glow.inputs.get('Threshold') is not None:
        glow.inputs['Threshold'].default_value = 1.2
    elif hasattr(glow, 'threshold'):
        glow.threshold = 1.2
    if glow.inputs.get('Strength') is not None:
        glow.inputs['Strength'].default_value = 0.25
    elif hasattr(glow, 'mix'):
        glow.mix = -0.75
    if glow.inputs.get('Size') is not None:
        glow.inputs['Size'].default_value = 0.22
    elif hasattr(glow, 'size'):
        glow.size = 7
    scene.render.use_compositing = True


def add_led_diffuser_edges(material):
    """Thin emitting diffuser edges make the LEDs readable from above."""
    added = 0
    for body in list(bpy.data.objects):
        if not (body.name.startswith('LIGHT_FIXTURE_') and body.name.endswith('_BODY')
                and body.type == 'MESH'):
            continue
        for side, sign in enumerate((-1, 1)):
            name = body.name[:-5] + f'_PINK_EDGE_{side}'
            if bpy.data.objects.get(name) is not None:
                continue
            hx, hy, hz = (body.dimensions.x - 0.18) / 2, 0.006, 0.010
            vertices = [(-hx,-hy,-hz), (hx,-hy,-hz), (hx,hy,-hz), (-hx,hy,-hz),
                        (-hx,-hy,hz), (hx,-hy,hz), (hx,hy,hz), (-hx,hy,hz)]
            faces = [(0,3,2,1), (4,5,6,7), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7)]
            mesh = bpy.data.meshes.new(name + '_DATA')
            mesh.from_pydata(vertices, [], faces)
            mesh.update()
            edge = bpy.data.objects.new(name, mesh)
            body.users_collection[0].objects.link(edge)
            edge.parent = body
            edge.location = (0.0, sign * (body.dimensions.y / 2 + 0.006),
                             -body.dimensions.z / 2 - 0.010)
            edge.data.materials.append(material)
            added += 1
    return added


def apply_pink_leds():
    material = bpy.data.materials.get('MAT_Light_Diffuser_Emission')
    if material is None:
        raise RuntimeError('Execute o Stage 5 antes deste ajuste: material das LEDs não encontrado.')
    material.diffuse_color = LED_EMISSION_COLOR
    material.use_nodes = True
    emission = next((n for n in material.node_tree.nodes if n.type == 'EMISSION'), None)
    if emission is None:
        raise RuntimeError('O material das LEDs não possui o nó de emissão esperado.')
    emission.inputs['Color'].default_value = LED_EMISSION_COLOR
    emission.inputs['Strength'].default_value = LED_EMISSION_STRENGTH

    count = 0
    for obj in bpy.data.objects:
        if (obj.name.startswith('LIGHT_FIXTURE_') and obj.name.endswith('_AREA')
                and obj.type == 'LIGHT' and obj.data.type == 'AREA'):
            obj.data.color = LED_LIGHT_COLOR
            obj.data.energy = LED_AREA_ENERGY
            count += 1
    added = add_led_diffuser_edges(material)
    configure_led_glow(bpy.context.scene)
    bpy.context.view_layer.update()
    print(f'LEDs rosa aplicadas: {count} luzes AREA; {added} bordas de difusor criadas; brilho suave.')


apply_pink_leds()
