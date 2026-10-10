import bpy
import math
import random
from mathutils import Vector

# ============================================================
# INDUSTRIAL WAREHOUSE ENVIRONMENT — STAGE 4 / REFERENCE STRUCTURES
# Blender 4.x / pure bpy / no external add-ons
# ============================================================
# This script consolidates Stages 1, 2 and 3 of the environment:
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
ROOT_COLLECTION_NAME = "ENV_WAREHOUSE_STAGE4"
LEGACY_ROOT_COLLECTIONS = (
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
CREATE_CEILING = False
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
MAIN_PANEL_X = -2.40
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
DUCT_DIAMETER = 0.45
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
FAN_DIAMETER = 0.54
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
LIGHT_FIXTURE_WIDTH = 0.16
LIGHT_FIXTURE_HEIGHT = 0.075
LIGHT_FIXTURE_Z = RACK_HEIGHT - 0.16
LIGHT_HANGER_TOP_Z = RACK_HEIGHT - 0.045
LIGHT_EMISSION_STRENGTH = 4.0
AREA_LIGHT_ENERGY = 260.0
AREA_LIGHT_SIZE = LIGHT_FIXTURE_LENGTH * 0.88
AREA_LIGHT_SIZE_Y = LIGHT_FIXTURE_WIDTH * 0.76

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
    emission.inputs["Color"].default_value = (1.0, 0.94, 0.84, 1.0)
    emission.inputs["Strength"].default_value = LIGHT_EMISSION_STRENGTH
    links.new(emission.outputs["Emission"], out.inputs["Surface"])
    mat.diffuse_color = (1.0, 0.94, 0.84, 1.0)
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
    data.color = (1.0, 0.94, 0.86)
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


# Preserve the Stage 2 lighting mounting points even though Stage 3
# now places finished industrial fixtures below them.
if CREATE_LIGHT_FIXTURES:
    for sx, x in enumerate(LIGHT_X_POSITIONS):
        for sy, y in enumerate(LIGHT_Y_POSITIONS):
            create_box(f"LIGHT_MOUNT_POINT_{sx:02d}_{sy:02d}",
                       (x, y, LIGHT_HANGER_TOP_Z),
                       (0.11, 0.18, 0.030),
                       COL_LIGHT_POINTS, MAT_STRUCTURAL, 0.004, LIGHT_SYSTEM_ROOT)
            create_box(f"LIGHT_POWER_POINT_{sx:02d}_{sy:02d}",
                       (x, y + 0.18, LIGHT_HANGER_TOP_Z - 0.045),
                       (0.15, 0.15, 0.09),
                       COL_LIGHT_POINTS, MAT_ELECTRICAL, 0.008, LIGHT_SYSTEM_ROOT)

def create_light_fixture(name, x, y, z, parent=None):
    # Horizontal across the rack (X), with the diffuser beneath the body.
    create_box(name + "_BODY", (x, y, z),
               (LIGHT_FIXTURE_LENGTH, LIGHT_FIXTURE_WIDTH, LIGHT_FIXTURE_HEIGHT),
               COL_LIGHTS, MAT_STRUCTURAL, 0.008, parent)
    create_box(name + "_DIFFUSER", (x, y, z - LIGHT_FIXTURE_HEIGHT / 2.0 - 0.014),
               (LIGHT_FIXTURE_LENGTH * 0.88, LIGHT_FIXTURE_WIDTH * 0.76, 0.022),
               COL_LIGHTS, MAT_EMISSION, 0.006, parent)
    for side, dx in (("A", -LIGHT_FIXTURE_LENGTH / 2.0 + 0.05),
                     ("B", LIGHT_FIXTURE_LENGTH / 2.0 - 0.05)):
        create_box(f"{name}_END_{side}", (x + dx, y, z),
                   (0.075, LIGHT_FIXTURE_WIDTH + 0.025, LIGHT_FIXTURE_HEIGHT + 0.025),
                   COL_LIGHTS, MAT_GALV, 0.005, parent)
    hanger_len = LIGHT_HANGER_TOP_Z - z
    for idx, dx in enumerate((-LIGHT_FIXTURE_LENGTH * 0.32,
                              LIGHT_FIXTURE_LENGTH * 0.32)):
        create_box(f"{name}_HANGER_{idx:02d}",
                   (x + dx, y, z + hanger_len / 2.0),
                   (0.025, 0.045, hanger_len),
                   COL_LIGHTS, MAT_GALV, 0.003, parent)
        create_box(f"{name}_MOUNT_{idx:02d}",
                   (x + dx, y, LIGHT_HANGER_TOP_Z),
                   (0.11, 0.16, 0.030),
                   COL_LIGHTS, MAT_STRUCTURAL, 0.004, parent)
    box_x = x + LIGHT_FIXTURE_LENGTH * 0.34
    create_box(name + "_JBOX", (box_x, y + 0.13, z + 0.04),
               (0.16, 0.12, 0.08), COL_LIGHTS, MAT_ELECTRICAL, 0.010, parent)
    create_cylinder_between(name + "_FEED",
                            (box_x, y + 0.13, z + 0.08),
                            (box_x, y + 0.13, LIGHT_HANGER_TOP_Z),
                            0.012, COL_LIGHTS, MAT_GALV,
                            vertices=SMALL_CYLINDER_SIDES, parent=parent)
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
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    pass


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
            COL_DUCTS, COL_FANS, COL_LIGHTS, COL_STRUCT, COL_RACKS):
    for obj in col.all_objects:
        generated_names.add(obj.name)
TOTAL_GENERATED_OBJECTS = len(generated_names)


# ============================================================
# 20 SUMMARY
# ============================================================

print("")
print("=" * 72)
print("WAREHOUSE ENVIRONMENT — STAGE 4 STRUCTURES COMPLETED")
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
print("Reference structure layout ready; props and final art are separate.")
print("=" * 72)
print("")
