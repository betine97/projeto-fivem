"""Prepare a bounded coastal pilot using assets from the installed GTA files."""
from pathlib import Path
import sys,json,hashlib,shutil,math
P=Path(__file__).resolve().parents[1];R=P.parent;A=P/'amostra_natural';F=A/'fontes';T=A/'texturas'
for p in [F,T,A/'backup',A/'exportados']:p.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset,AssetTarget,AssetFormat,AssetVersion,AssetMapData,MapContentFlags
from szio.gta5.entities import Entity,EntityFlags,EntityLodLevel,EntityPriorityLevel
from szio.types import Vector,Quaternion
G=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V');archive_cache={};provenance=[]
def archive(root,sub):
 key=root+'|'+sub
 if key not in archive_cache:archive_cache[key]=open_rpf(G/root).open_nested(sub)
 return archive_cache[key]
def extract(root,sub,name):
 b=archive(root,sub).read_bytes(name);p=F/name;p.write_bytes(b)
 provenance.append({'file':name,'archive':root+'|'+sub,'sha256':hashlib.sha256(b).hexdigest()});return p
root='update/x64/dlcpacks/mpheist4/dlc1.rpf';sub='x64/levels/gta5/generic/mph4_gtxd.rpf';textures={}
for dic in ['gdislxterrain','gdislxtertracks']:
 # Highest installed mip levels take precedence; don't upscale source textures.
 for suffix in ['', '+hi']:
  d=try_load_asset(extract(root,sub,dic+suffix+'.ytd'))
  for name,tex in d.textures.items():textures[str(name).lower()]=tex
layers=[('grass','cs_rsn_sl_agrgrass_02','cs_rsn_sl_agrgrass_02_n'),('dirt','cs_rsn_sl_agrdirttrack2','cs_rsn_sl_agrdirttrack2_n'),('mud','hp_islandbank_redmud_02','hp_islandbank_redmud_02_n'),('rock','cs_islx_canyonrock_rough_01','cs_islx_canyonrockrough_01_nrm'),('sand','ap_rls_sand_scrabl_warm','ap_rls_sand_scrabl_n')]
layer_report=[]
for family,diffuse,normal in layers:
 for name in [diffuse,normal]:
  tex=textures[name.lower()];(T/(name+'.dds')).write_bytes(tex.data.read_bytes())
 layer_report.append({'family':family,'diffuse':diffuse,'normal':normal,'size':[textures[diffuse].width,textures[diffuse].height]})
models={'palm':['prop_palm_med_01a','prop_palm_sm_01a','prop_palm_sm_01d'], 'tree':['prop_tree_eucalip_01'], 'rock':['prop_rock_1_a','prop_rock_2_a','prop_rock_4_c'], 'bush':['prop_bush_med_01','prop_bush_med_03'], 'grass':['prop_veg_grass_01_a','prop_veg_grass_01_b','prop_veg_grass_01_c']}
index=(R/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines();model_info={};dictionaries={}
for family,names in models.items():
 for name in names:
  source=next(s.strip() for s in index if s.strip().endswith('|'+name+'.ydr'));parts=source.split('|');root,sub=parts[:2]
  a=try_load_asset(extract(root,sub,name+'.ydr'));arc=archive(root,sub)
  typename=next(n for n in arc.list_dir('') if n.endswith('.ytyp'))
  if typename not in dictionaries:dictionaries[typename]=try_load_asset(extract(root,sub,typename))
  archetype=next(v for v in dictionaries[typename].archetypes if str(v.name)==name)
  model_info[name]={'family':family,'bb_min':list(archetype.bb_min),'bb_max':list(archetype.bb_max),'txd':str(archetype.texture_dictionary),'physics':str(archetype.physics_dictionary),'archive':root+'|'+sub,'has_embedded_collision':a.bounds is not None}
  # Native assets remain in their already loaded prop archives. Copies here are
  # for authoring and verification, never a second copy streamed to the game.
  for suffix in ['', '+hi']:
   ytd=str(archetype.texture_dictionary)+suffix+'.ytd'
   if ytd in arc.list_dir(''):
    td=try_load_asset(extract(root,sub,ytd))
    for key,tex in td.textures.items():(T/(str(key).lower()+'.dds')).write_bytes(tex.data.read_bytes())
  for key,tex in a.shader_group.embedded_textures.items():(T/(str(key).lower()+'.dds')).write_bytes(tex.data.read_bytes())
grid=np.load(P/'dados/terreno.npz')['terrain'];meta=json.loads((P/'dados/medidas.json').read_text());tile=next(t for t in meta['tiles'] if t['name']=='ti_terreno_03_01')
def ground(x,y):
 u=(x-grid[0,0,0])/(grid[0,1,0]-grid[0,0,0]);v=(y-grid[0,0,1])/(grid[1,0,1]-grid[0,0,1]);i,j=int(u),int(v);u-=i;v-=j
 h00,h10,h01,h11=grid[j,i,2],grid[j,i+1,2],grid[j+1,i,2],grid[j+1,i+1,2]
 z=h00+(h10-h00)*u+(h11-h10)*v if u>=v else h00+(h11-h01)*u+(h01-h00)*v
 dx=(h10-h00 if u>=v else h11-h01)/(grid[0,1,0]-grid[0,0,0]);dy=(h11-h10 if u>=v else h01-h00)/(grid[1,0,1]-grid[0,0,1]);return float(z),float(math.hypot(dx,dy))
def path_x(y):return -715+14*math.sin((y+160)/54)
rng=np.random.default_rng(20261009);placed=[];obstacles=[]
for family,target,min_z,max_slope,spacing,lod in [('palm',55,3,.48,8,500),('tree',12,16,.42,10,500),('rock',65,1,.66,3,220),('bush',95,6,.55,2,150),('grass',460,8,.50,.8,85)]:
 attempts=0;count=0
 while count<target and attempts<30000:
  attempts+=1;x=float(rng.uniform(-819,-651));y=float(rng.uniform(-408,-132));z,slope=ground(x,y)
  if z<min_z or slope>max_slope or abs(x-path_x(y))<5:continue
  if any((x-q[0])**2+(y-q[1])**2<spacing**2 for q in obstacles):continue
  name=str(rng.choice(models[family]));scale=float(rng.uniform(.85,1.14));heading=float(rng.uniform(0,360));info=model_info[name]
  # Root bases overlap terrain slightly; rocks follow their true mesh bounds.
  embed=.12 if family in ['palm','tree'] else .035
  origin_z=z-embed-(info['bb_min'][2]*scale if family=='rock' else 0)
  placed.append({'name':name,'family':family,'position':[x,y,origin_z],'ground_z':z,'scale':scale,'heading':heading,'lod':lod,'slope':slope});count+=1
  if family in ['palm','tree','rock']:obstacles.append((x,y))
 assert count==target,(family,count)
visit={'x':path_x(-170),'y':-170,'z':ground(path_x(-170),-170)[0]+1.15,'heading':180,'model':meta.get('spawn_model','a_m_y_business_01')}
counts={k:sum(q['family']==k for q in placed) for k in models}
config={'tile':tile,'bounds':[-819,-408,-651,-132],'visit':visit,'layers':layer_report,'placements':placed,'models':model_info,'counts':counts,'seed':20261009,'native_game_assets':True,'in_game_verified':False}
(A/'config.json').write_text(json.dumps(config,indent=2));(A/'proveniencia.json').write_text(json.dumps(provenance,indent=2))
for file in [P/'fivem/stream'/f"{tile['name']}.ydr",P/'fivem/stream'/f"{tile['name']}.ybn",P/'fivem/client.lua',P/'fivem/data/config.json']:
 dest=A/'backup'/file.name
 if not dest.exists():shutil.copy2(file,dest)
print('NATURAL_PILOT_PREPARED',counts,'visit',visit,flush=True)
