import json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
backup=W/'backup_antes_limpeza'
if not backup.exists():
 backup.mkdir();shutil.copytree(R/'server-data/resources/cidade_mansao',backup/'cidade_mansao');shutil.copytree(W/'fivem',backup/'fivem')
 for p in W.glob('*'):
  if p.suffix in ('.json','.blend','.md'):shutil.copy2(p,backup/p.name)
exec(Path(__file__).with_name('locate.py').read_text().split('for s in index:')[0])
origin=json.loads((W/'medidas_estudo.json').read_text())['native_origin'];selected=[]
for e in json.loads((out/'entities.json').read_text()):
 q=[v-o for v,o in zip(e['pos'],origin)]
 if -13<q[0]<17 and -18<q[1]<12 and -12<q[2]<8:selected.append(e)
names={e['name'] for e in selected}
for s in index:
 parts=s.split('|');name=Path(parts[-1]).stem
 if s.endswith('.ydr') and name in names:
  f=assets/(name+'.ydr')
  if not f.exists():f.write_bytes(archive(parts).read_bytes(parts[-1]))
(out/'near_house_entities.json').write_text(json.dumps(selected,indent=2))
print('EXTRACTED',len(selected),'nearby entities',len(names),'drawables; backup',backup)
