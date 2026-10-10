import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parent;N=P/'referencia_tecnica';N.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
from szio.gta5 import *
game=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V/update/x64/dlcpacks/mpheist4');found=[]
def walk(a,folder='',prefix='',depth=0):
 for name in a.list_dir(folder):
  f=folder+'/'+name if folder else name
  if a.is_dir(f):walk(a,f,prefix,depth)
  elif f.endswith('.rpf') and depth<6:
   try:walk(a.open_nested(f),'',prefix+'|'+f,depth+1)
   except Exception as e:print('SCAN_NOTE',f,str(e)[:100],flush=True)
  elif f.endswith(('.ymap','.ydr','.ybn','.ytyp')):
   found.append({'file':f,'archive':prefix})
   if f.endswith('.ymap') and ('island' in f or 'terrain' in f):
    (N/Path(f).name).write_bytes(a.read_bytes(f))
for f in game.glob('*.rpf'):
 try:walk(open_rpf(f),prefix=str(f))
 except Exception as e:print('SCAN_ROOT_NOTE',f.name,str(e)[:100],flush=True)
(N/'indice_cayo.json').write_text(json.dumps(found,indent=2))
rows=[]
for f in N.glob('*.ymap'):
 try:a=try_load_asset(f)
 except Exception:continue
 for e in a.entities:
  name=str(e.archetype_name)
  if any(v in name for v in ['terrain','islandx','island_terrain','h4_island']):rows.append({'map':f.name,'name':name,'pos':list(e.position),'rot':list(e.rotation),'scale_xy':e.scale_xy,'scale_z':e.scale_z})
(N/'entidades_terreno.json').write_text(json.dumps(rows,indent=2));print('CAYO_ENTITIES',len(rows),rows[:18],flush=True)
print('TERRAIN_FILES',[f for f in found if any(v in f['file'] for v in ['terrain','islandx'])][:50],flush=True)
