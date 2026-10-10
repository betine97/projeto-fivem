"""Package one pilot sector without touching the other island sectors."""
from pathlib import Path
import sys,json,copy,struct,math,re,shutil
P=Path(__file__).resolve().parents[1];R=P.parent;A=P/'amostra_natural';O=P/'fivem/stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import CollisionMaterial
from szio.gta5.maps import *
from szio.gta5.entities import *
from szio.types import Vector,Quaternion,DataSource
cfg=json.loads((A/'config.json').read_text());name=cfg['tile']['name'];targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
a=try_load_asset(A/'exportados'/f'{name}.ydr');report={'lod_triangles':{}}
for lod,suffix in [(LodLevel.HIGH,''),(LodLevel.MEDIUM,'_MED'),(LodLevel.LOW,'_LOW'),(LodLevel.VERYLOW,'_VLOW')]:
 src=try_load_asset(A/'exportados'/f'{name}{suffix}.ydr')
 assert [s.preset_filename for s in a.shader_group.shaders]==[s.preset_filename for s in src.shader_group.shaders]
 a.models[lod]=copy.deepcopy(src.models[LodLevel.HIGH])
 report['lod_triangles'][lod.name]=sum(len(g.index_buffer)//3 for m in a.models[lod] for g in m.geometries)
 for m in a.models[lod]:
  for g in m.geometries:
   if 'Tangent' in g.vertex_buffer.dtype.names:
    v=g.vertex_buffer.copy();bad=np.linalg.norm(v['Tangent'][:,:3],axis=1)<.5;n=v['Normal'][bad];axis=np.eye(3)[np.argmin(abs(n),axis=1)];t=np.cross(axis,n);t/=np.maximum(np.linalg.norm(t,axis=1,keepdims=True),1e-9);v['Tangent'][bad,:3]=t;v['Tangent'][bad,3]=1;g.vertex_buffer=v
for txname in list(a.shader_group.embedded_textures):
 path=A/'texturas'/f'{txname}.dds'
 if not path.exists():path=P/'nativo/texturas'/f'{txname}.dds'
 b=path.read_bytes();h,w=struct.unpack_from('<II',b,12);a.shader_group.embedded_textures[txname]=EmbeddedTexture(txname,w,h,DataSource.create(b,name=txname+'.dds'))
for shader in a.shader_group.shaders:shader.name=Path(shader.preset_filename).stem
a.lod_thresholds={LodLevel.HIGH:420.,LodLevel.MEDIUM:850.,LodLevel.LOW:1800.,LodLevel.VERYLOW:6500.};a.bounds=None
save_asset(a,targets,O,name)
# Keep the exact original collision mesh; only change its surface response.
names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
col=try_load_asset(A/'backup'/f'{name}.ybn');b=col.children[0];v=np.array([list(p.co) for p in b.geometry_vertices]);counts={}
for tri in b.geometry_primitives:
 p=v[list(tri.vertices)];x,y,z=p.mean(0);n=np.cross(p[1]-p[0],p[2]-p[0]);slope=np.linalg.norm(n[:2])/max(abs(n[2]),1e-8)
 path=-715+14*math.sin((y+160)/54);mud=((x+750)/12)**2+((y+230)/22)**2<.65
 mat='SAND_LOOSE' if z<8 else 'ROCK' if slope>.55 else 'MUD_SOFT' if mud else 'DIRT_TRACK' if abs(x-path)<4.5 else 'GRASS'
 tri.material=CollisionMaterial.from_packed(names.index(mat));counts[mat]=counts.get(mat,0)+1
save_asset(col,targets,O,name);report['collision_surfaces']=counts
# Register a self-contained subset, not optional stock archetypes. The original
# native drawables keep their shaders, palettes, LODs and embedded collisions.
aliases={model:'ti_n_'+model.removeprefix('prop_') for model in cfg['models']}
source_types=[try_load_asset(p) for p in (A/'fontes').glob('*.ytyp')]
archetypes=[];copied_txd=set()
for model,alias in aliases.items():
 archetype=copy.deepcopy(next(t for typ in source_types for t in typ.archetypes if str(t.name)==model))
 shutil.copy2(A/'fontes'/f'{model}.ydr',O/f'{alias}.ydr')
 archetype.name=alias;archetype.asset_name=alias
 archetype.drawable_dictionary='';archetype.physics_dictionary=''
 original_txd=str(archetype.texture_dictionary)
 if (A/'fontes'/f'{original_txd}.ytd').exists():
  target_txd='ti_n_'+original_txd
  if original_txd not in copied_txd:
   for suffix in ['', '+hi']:
    path=A/'fontes'/f'{original_txd}{suffix}.ytd'
    if path.exists():shutil.copy2(path,O/f'{target_txd}{suffix}.ytd')
   copied_txd.add(original_txd)
  archetype.texture_dictionary=target_txd
 else:
  # These original drawables have their full texture dictionary embedded.
  drawable=try_load_asset(A/'fontes'/f'{model}.ydr')
  assert drawable.shader_group.embedded_textures,model
  archetype.texture_dictionary=''
 archetype.lod_dist=cfg['models'][model]['family'] in ['tree','palm'] and 500.0 or 220.0
 archetype.hd_texture_dist=archetype.lod_dist
 archetypes.append(archetype)
save_asset(AssetMapTypes(name='ti_nature',archetypes=archetypes),targets,O,'ti_nature')
entities=[];mins=[];maxs=[];streammins=[];streammaxs=[];physics=set()
for i,row in enumerate(cfg['placements']):
 info=cfg['models'][row['name']];theta=math.radians(row['heading']);s=row['scale'];p=np.array(row['position']);c,t=math.cos(theta),math.sin(theta)
 rot=np.array([[c,-t,0],[t,c,0],[0,0,1]])
 corners=np.array([[x,y,z] for x in [info['bb_min'][0],info['bb_max'][0]] for y in [info['bb_min'][1],info['bb_max'][1]] for z in [info['bb_min'][2],info['bb_max'][2]]])*s
 corners=corners@rot.T+p;lo=corners.min(0);hi=corners.max(0);mins.append(lo);maxs.append(hi);streammins.append(lo-row['lod']);streammaxs.append(hi+row['lod'])
 priority=EntityPriorityLevel.OPTIONAL_HIGH if row['family'] in ['palm','tree','rock'] else EntityPriorityLevel.OPTIONAL_LOW
 # GTA map quaternions store the inverse of Blender's object rotation.
 entities.append(Entity(aliases[row['name']],Vector(p),Quaternion((math.cos(theta/2),0,0,-math.sin(theta/2))),s,s,EntityFlags.IS_STATIC,i+1,-1,row['lod'],0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]))
save_asset(AssetMapData(name='ti_amostra_natural',content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,physics_dictionaries=sorted(physics),entities_extents=(Vector(np.min(mins,0)),Vector(np.max(maxs,0))),streaming_extents=(Vector(np.min(streammins,0)),Vector(np.max(streammaxs,0)))),targets,O,'ti_amostra_natural')
configpath=P/'fivem/data/config.json';gamecfg=json.loads(configpath.read_text());gamecfg['natural_sample']={'spawn':cfg['visit'],'bounds':cfg['bounds'],'counts':cfg['counts'],'models':list(aliases.values()),'source_models':aliases};gamecfg['revision']='ilha-20261009-amostra-natural-3';configpath.write_text(json.dumps(gamecfg,indent=2))
report.update({'sector':name,'entities':len(entities),'counts':cfg['counts'],'native_assets_reused':list(cfg['models']),'in_game_verified':False});(A/'pacote.json').write_text(json.dumps(report,indent=2));print('NATURAL_PILOT_PACKAGED',report,flush=True)
