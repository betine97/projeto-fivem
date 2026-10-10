"""Locate stock and DLC map placements that survive the custom base level."""
from pathlib import Path
import sys,json,math,xml.etree.ElementTree as E
P=Path(__file__).resolve().parents[1];R=P.parent;A=P/'amostra_natural'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset
from szio.vfs import VPath
G=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
grid=np.load(P/'dados/terreno.npz')['terrain']
def height(x,y):
 u=(x-grid[0,0,0])/(grid[0,1,0]-grid[0,0,0]);v=(y-grid[0,0,1])/(grid[1,0,1]-grid[0,0,1]);i,j=int(u),int(v);u-=i;v-=j
 a,b,c,d=grid[j,i,2],grid[j,i+1,2],grid[j+1,i,2],grid[j+1,i+1,2]
 return float(a+(b-a)*u+(d-b)*v if u>=v else a+(d-c)*u+(c-a)*v)
print('EXPECTED_TERRAIN',[(x,y,height(x,y)) for x,y in [(-717.5778,-170),(-709.79,-407.49)]],flush=True)
report=[];blocked=set();errors=[]
def inspect(path):
 try:
  mp=try_load_asset(path)
  if mp is None:return
  found=[]
  for e in mp.entities:
   x,y,z=e.position
   if -1450<x<1450 and -1700<y<1700:found.append({'archetype':str(e.archetype_name),'position':list(e.position)})
  if found:
   blocked.add(path.stem);report.append({'source':str(path),'name':path.stem,'entities_on_island':len(found),'near_sample':[e for e in found if -950<e['position'][0]<-600 and -500<e['position'][1]<0]})
 except Exception as e:errors.append({'path':str(path),'error':str(e)[:140]})
# Stock metadata provides a reference for identifying the rooftop object.
for line in (R/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines():
 if line.endswith('.ymap') and '/_city' in line:inspect(VPath(G, line.replace('|','/')))
print('STOCK_MAPS_IN_ISLAND_REGION',len(blocked),flush=True)
# DLC placement archives are mounted separately from gta5.meta. Enumerate
# placements only; leave their weapons, vehicles and props available.
def walk(path,depth=0):
 try:
  for p in path.iterdir():
   if p.is_dir():walk(p,depth)
   elif p.suffix.lower()=='.rpf' and depth<4:walk(p,depth+1)
   elif p.suffix.lower()=='.ymap':inspect(p)
 except Exception as e:errors.append({'path':str(path),'error':str(e)[:140]})
for pack in sorted((G/'update/x64/dlcpacks').iterdir()):
 for archive in pack.glob('*.rpf'):walk(VPath(archive))
 print('DLC_SCANNED',pack.name,len(blocked),flush=True)
(A/'auditoria_mundo.json').write_text(json.dumps({'maps':report,'errors':errors},indent=2))
(P/'fivem/data/mapas_originais.json').write_text(json.dumps(sorted(blocked)))
print('ORIGINAL_MAP_AUDIT_READY',len(blocked),'errors',len(errors),flush=True)
