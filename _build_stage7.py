from pathlib import Path

base = Path(__file__).resolve().parent
source = (base / 'warehouse_stage6_completo.py').read_text(encoding='utf-8')
source = source.replace('STAGE 6 / INDUSTRIAL SERVICES AND CEILING VENTS', 'STAGE 7 / FLOOR HOSES AND STORAGE PROPS')
source = source.replace('ROOT_COLLECTION_NAME = "ENV_WAREHOUSE_STAGE6"', 'ROOT_COLLECTION_NAME = "ENV_WAREHOUSE_STAGE7"')
source = source.replace('LEGACY_ROOT_COLLECTIONS = (', 'LEGACY_ROOT_COLLECTIONS = (\n    "ENV_WAREHOUSE_STAGE6",')
fragment = (base / '_stage7_floor_hoses.py').read_text(encoding='utf-8')
marker = '# ============================================================\n# 17 MATERIAL REFINEMENT / WORLD'
source = source.replace(marker, fragment + '\n\n' + marker)
source = source.replace('COL_WALL_SERVICES, COL_CEILING_DUCTS):',
                        'COL_WALL_SERVICES, COL_CEILING_DUCTS, COL_FLOOR_HOSES, COL_STORAGE_DRUMS):')
source = source.replace('WAREHOUSE ENVIRONMENT — STAGE 6 INFRASTRUCTURE COMPLETED',
                        'WAREHOUSE ENVIRONMENT — STAGE 7 FLOOR HOSES COMPLETED')
source = source.replace('print("Stage 6 infrastructure ready. Pink LEDs preserved.")',
                        'print("Stage 7 ready: two closed drums, floor cables and a visual hose to each pot.")')
compile(source, 'warehouse_stage7_completo.py', 'exec')
for directory in (base, Path(r'C:\Users\erons\Downloads')):
    (directory / 'warehouse_stage7_completo.py').write_text(source, encoding='utf-8')
print('Stage 7 complete source saved.')
