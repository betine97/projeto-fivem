from pathlib import Path

BASE = Path(__file__).resolve().parent
s = (BASE / 'warehouse_stage4_completo.py').read_text(encoding='utf-8')
s = s.replace('STAGE 4 / REFERENCE STRUCTURES', 'STAGE 5 / VISUAL COMPOSITION')
s = s.replace('# This script consolidates Stages 1, 2 and 3 of the environment:',
              '# Standalone environment: architecture, racks and Stage 5 visual props:')
s = s.replace('ROOT_COLLECTION_NAME = "ENV_WAREHOUSE_STAGE4"',
              'ROOT_COLLECTION_NAME = "ENV_WAREHOUSE_STAGE5"')
s = s.replace('LEGACY_ROOT_COLLECTIONS = (',
              'LEGACY_ROOT_COLLECTIONS = (\n    "ENV_WAREHOUSE_STAGE4",')
s = s.replace('MAIN_PANEL_X = -2.40', 'MAIN_PANEL_X = -1.55')
s = s.replace('LIGHT_FIXTURE_WIDTH = 0.16', 'LIGHT_FIXTURE_WIDTH = 0.28')
s = s.replace('LIGHT_FIXTURE_HEIGHT = 0.075', 'LIGHT_FIXTURE_HEIGHT = 0.055')
s = s.replace('AREA_LIGHT_SIZE_Y = LIGHT_FIXTURE_WIDTH * 0.76',
              'AREA_LIGHT_SIZE_Y = LIGHT_FIXTURE_WIDTH * 0.85')
config = '''# Stage 5: generic visual placeholders only.
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
SIDE_FAN_DIAMETER = 0.44
SIDE_FAN_Z = 1.57

'''
s = s.replace('# Vent placeholders', config + '# Vent placeholders')
s = s.replace('COL_RACKS = ensure_collection("ENV_RACKS", ROOT)', '''COL_RACKS = ensure_collection("ENV_RACKS", ROOT)
COL_PLACEHOLDERS = ensure_collection("ENV_PLANT_PLACEHOLDERS", ROOT)
COL_TECH_PROPS = ensure_collection("ENV_TECHNICAL_PROPS", ROOT)
COL_SIDE_FANS = ensure_collection("ENV_SIDE_FANS", ROOT)''')
s = s.replace('MAT_EMISSION = make_emission_material()', '''MAT_EMISSION = make_emission_material()
MAT_POT = make_simple_material("MAT_Generic_Pot", (0.08, 0.085, 0.08), 0.78)
MAT_POT_FILL = make_simple_material("MAT_Pot_Fill", (0.065, 0.047, 0.031), 0.95)
MAT_PLACEHOLDER_A = make_simple_material("MAT_Canopy_Placeholder_A", (0.16, 0.28, 0.10), 0.9)
MAT_PLACEHOLDER_B = make_simple_material("MAT_Canopy_Placeholder_B", (0.23, 0.34, 0.13), 0.9)
MAT_BLUE_TANK = make_simple_material("MAT_Blue_Tank", (0.015, 0.10, 0.42), 0.4)
MAT_CONTAINER = make_simple_material("MAT_Closed_Container", (0.40, 0.43, 0.38), 0.7)
MAT_CRATE = make_simple_material("MAT_Generic_Crate", (0.21, 0.23, 0.24), 0.7)
MAT_BUCKET = make_simple_material("MAT_Generic_Bucket", (0.62, 0.63, 0.56), 0.6)''')

start = s.index('# Preserve the Stage 2 lighting mounting points')
end = s.index('\n\nLIGHT_COUNT = 0', start)
s = s[:start] + '''def create_light_fixture(name, x, y, z, parent=None):
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
''' + s[end:]

stage5 = r'''
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


def create_side_fan(name, side, yy):
    # Local +Z is the visible face: rotate it to +X on left, -X on right.
    root = ensure_empty(name + "_ROOT", COL_SIDE_FANS,
                        (side * (ROOM_WIDTH / 2.0 - 0.12), yy, SIDE_FAN_Z), size=0.07)
    root.rotation_euler = (0.0, -side * math.pi / 2.0, 0.0)
    root["face_direction"] = "inward toward rack"
    radius = SIDE_FAN_DIAMETER / 2.0
    create_box(name + "_WALL_PLATE", (0.0, 0.0, -0.09), (0.16, 0.25, 0.025),
               COL_SIDE_FANS, MAT_STRUCTURAL, 0.005, root)
    create_cylinder(name + "_MOTOR", (0.0, 0.0, -0.045), 0.055, 0.13,
                    COL_SIDE_FANS, MAT_DARK_METAL, vertices=16, parent=root)
    for index, zz in enumerate((-0.045, 0.065)):
        create_hoop(f"{name}_RIM_{index}", (0, 0, zz), radius, 0.012,
                    COL_SIDE_FANS, MAT_STRUCTURAL, root)
    for index in range(3):
        angle = 2.0 * math.pi * index / 3.0
        blade = create_box(f"{name}_BLADE_{index}",
                            (0.10 * math.cos(angle), 0.10 * math.sin(angle), 0.015),
                            (0.18, 0.070, 0.014), COL_SIDE_FANS, MAT_GALV, 0.018, root)
        blade.rotation_euler[2] = angle + 0.22
    create_cylinder(name + "_HUB", (0, 0, 0.04), 0.049, 0.07,
                    COL_SIDE_FANS, MAT_DARK_METAL, vertices=16, parent=root)
    for index, rr in enumerate((radius * 0.38, radius * 0.67, radius * 0.92)):
        create_hoop(f"{name}_GRILLE_{index}", (0, 0, 0.082), rr, 0.0045,
                    COL_SIDE_FANS, MAT_GALV, root)
    for index in range(8):
        angle = index * math.pi / 4.0
        create_cylinder_between(f"{name}_SPOKE_{index}", (0, 0, 0.082),
                                (radius * math.cos(angle), radius * math.sin(angle), 0.065),
                                0.004, COL_SIDE_FANS, MAT_GALV, vertices=6, parent=root)
    create_bezier_curve(name + "_CABLE",
                        [(0, -0.045, -0.07), (0, -0.21, -0.08), (0, -0.37, -0.105)],
                        COL_SIDE_FANS, MAT_RUBBER, 0.006, bevel_resolution=1, parent=root)


SIDE_FAN_COUNT = 0
if CREATE_SIDE_FANS:
    for side, label in ((-1, "LEFT"), (1, "RIGHT")):
        for bay, yy in enumerate(LIGHT_Y_POSITIONS):
            create_side_fan(f"SIDE_FAN_{label}_{bay:02d}", side, yy)
            SIDE_FAN_COUNT += 1

'''
s = s.replace('# 17 MATERIAL REFINEMENT / WORLD', '# 17 MATERIAL REFINEMENT / WORLD')
marker = '# ============================================================\n# 17 MATERIAL REFINEMENT / WORLD'
s = s.replace(marker, stage5 + '\n' + marker)
s = s.replace('COL_LIGHTS, COL_STRUCT, COL_RACKS):',
              'COL_LIGHTS, COL_STRUCT, COL_RACKS,\n            COL_PLACEHOLDERS, COL_TECH_PROPS, COL_SIDE_FANS):')
s = s.replace('WAREHOUSE ENVIRONMENT — STAGE 4 STRUCTURES COMPLETED',
              'WAREHOUSE ENVIRONMENT — STAGE 5 COMPOSITION COMPLETED')
s = s.replace('print("Reference structure layout ready; props and final art are separate.")', '''print(f"Generic Plant Volumes:    {PLACEHOLDER_COUNT}")
print(f"Volumes Per Module:      {PLACEHOLDERS_PER_MODULE}")
print(f"Side Fans:               {SIDE_FAN_COUNT}")
print("Stage 5 visual composition ready. Generic props only.")''')
s = s.replace("try:\n    scene.render.engine = 'BLENDER_EEVEE_NEXT'\nexcept Exception:\n    pass", """for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue""")
compile(s, 'warehouse_stage5_completo.py', 'exec')
(BASE / 'warehouse_stage5_completo.py').write_text(s, encoding='utf-8')
Path(r'C:\Users\erons\Downloads\warehouse_stage5_completo.py').write_text(s, encoding='utf-8')
print('Stage 5 standalone script created.')
