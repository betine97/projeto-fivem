import json,shutil,hashlib,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';B=W/'backup_antes_jantar_cozinha';B.mkdir(exist_ok=True)
for name in ('mansao_encaixada.blend','mansao_fivem_preparada.blend'):
 if not (B/name).exists():shutil.copy2(W/name,B/name)
for p in W.glob('*.json'):
 if not (B/p.name).exists():shutil.copy2(p,B/p.name)
for folder in ('fivem','work/materiais'):
 if not (B/folder).exists():shutil.copytree(W/folder,B/folder)
if not (B/'resource').exists():shutil.copytree(R/'server-data/resources/cidade_mansao',B/'resource')
if not (B/'scripts').exists():
 (B/'scripts').mkdir()
 for p in (W/'work').glob('*.py'):shutil.copy2(p,B/'scripts'/p.name)
files={
 'dining':'Meshy_AI_luxury_dining_set_3d_1008013321_image-to-3d-texture.glb',
 'cylinder':'Meshy_AI_modern_cylinder_penda_1008013301_image-to-3d-texture.glb',
 'island':'Meshy_AI_kitchen_island_stools_1008012933_image-to-3d-texture.glb',
 'linear':'Meshy_AI_linear_led_pendant_li_1008013240_image-to-3d-texture.glb'}
rows={}
for k,name in files.items():
 src=Path('C:/Users/erons/Downloads')/name;dst=W/'source_assets'/(k+'_original.glb');shutil.copy2(src,dst)
 raw=dst.read_bytes();n=struct.unpack_from('<I',raw,12)[0];data=json.loads(raw[20:20+n])
 rows[k]=dict(source=str(src),local_source=str(dst),sha256=hashlib.sha256(raw).hexdigest(),materials=data.get('materials',[]),meshes=len(data.get('meshes',[])))
(W/'componentes_jantar_cozinha.json').write_text(json.dumps(dict(revision='jantar-cozinha-2026-10-07',assets=rows),indent=2),encoding='utf-8')
print('INPUTS_BACKED_UP',[(k,v['meshes'],len(v['materials'])) for k,v in rows.items()])
