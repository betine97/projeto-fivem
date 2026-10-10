from pathlib import Path

base = Path(__file__).resolve().parent
source = (base / 'warehouse_stage5_luz_rosa.py').read_text(encoding='utf-8')
source = source.replace('STAGE 5 / VISUAL COMPOSITION', 'STAGE 6 / INDUSTRIAL SERVICES AND CEILING VENTS')
source = source.replace('ROOT_COLLECTION_NAME = "ENV_WAREHOUSE_STAGE5"', 'ROOT_COLLECTION_NAME = "ENV_WAREHOUSE_STAGE6"')
source = source.replace('LEGACY_ROOT_COLLECTIONS = (', 'LEGACY_ROOT_COLLECTIONS = (\n    "ENV_WAREHOUSE_STAGE5",')
source = source.replace('CREATE_CEILING = False', 'CREATE_CEILING = True')
source = source.replace('SIDE_FAN_DIAMETER = 0.44', 'SIDE_FAN_DIAMETER = 0.82')
source = source.replace('SIDE_FAN_Z = 1.57', 'SIDE_FAN_Z = 2.60')
source = source.replace('FAN_DIAMETER = 0.54', 'FAN_DIAMETER = 0.84')
source = source.replace('DUCT_DIAMETER = 0.45', 'DUCT_DIAMETER = 0.56')
source = source.replace('# Vent placeholders', '''# Stage 6 overhead infrastructure; all dimensions in meters.
CREATE_WALL_SERVICES = True
CREATE_CEILING_DUCTS = True
CEILING_DUCT_DIAMETER = 0.68
CEILING_DUCT_Z = 3.16
CEILING_VENT_DIAMETER = 0.90
CEILING_VENT_FACE_Z = 2.52

# Vent placeholders''')
source = source.replace('COL_SIDE_FANS = ensure_collection("ENV_SIDE_FANS", ROOT)', '''COL_SIDE_FANS = ensure_collection("ENV_SIDE_FANS", ROOT)
COL_WALL_SERVICES = ensure_collection("ENV_WALL_SERVICES", ROOT)
COL_CEILING_DUCTS = ensure_collection("ENV_CEILING_DUCTS", ROOT)''')
source = source.replace('MAT_BUCKET = make_simple_material(',
                        'MAT_CABLE_ACCENT = make_simple_material("MAT_Cable_Accent", (0.16, 0.075, 0.045), 0.7)\nMAT_BUCKET = make_simple_material(')
start = source.index('def create_side_fan(')
end = source.index('\n\nSIDE_FAN_COUNT = 0', start)
source = source[:start] + (base / '_stage6_fan_helpers.py').read_text(encoding='utf-8') + source[end:]
marker = '# ============================================================\n# 17 MATERIAL REFINEMENT / WORLD'
source = source.replace(marker, (base / '_stage6_infrastructure.py').read_text(encoding='utf-8') + '\n\n' + marker)
source = source.replace('COL_PLACEHOLDERS, COL_TECH_PROPS, COL_SIDE_FANS):',
                        'COL_PLACEHOLDERS, COL_TECH_PROPS, COL_SIDE_FANS, COL_WALL_SERVICES, COL_CEILING_DUCTS):')
source = source.replace('WAREHOUSE ENVIRONMENT — STAGE 5 COMPOSITION COMPLETED',
                        'WAREHOUSE ENVIRONMENT — STAGE 6 INFRASTRUCTURE COMPLETED')
source = source.replace('print("Stage 5 visual composition ready. Generic props only.")', '''print(f"Wall Fan Diameter:       {SIDE_FAN_DIAMETER:.2f}m")
print(f"Ceiling Main Duct:       {CEILING_DUCT_DIAMETER:.2f}m")
print(f"Ceiling Vents:           {len(LIGHT_Y_POSITIONS) if CREATE_CEILING_DUCTS else 0}")
print(f"Vent Diameter:           {CEILING_VENT_DIAMETER:.2f}m")
print("Stage 6 infrastructure ready. Pink LEDs preserved.")''')
compile(source, 'warehouse_stage6_completo.py', 'exec')
for directory in (base, Path(r'C:\Users\erons\Downloads')):
    (directory / 'warehouse_stage6_completo.py').write_text(source, encoding='utf-8')
print('Stage 6 standalone script saved.')
