"""Check the shipped pilot geometry, native dependencies and visit command."""
from pathlib import Path
import sys,json,hashlib,math,io,xml.etree.ElementTree as E
P=Path(__file__).resolve().parents[1];R=P.parent;A=P/'amostra_natural';F=P/'fivem';O=F/'stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/lua_syntax_deps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from lupa import LuaRuntime
from PIL import Image
from szio.gta5 import try_load_asset,LodLevel
from szio.gta5.entities import EntityFlags
cfg=json.loads((A/'config.json').read_text());game=json.loads((F/'data/config.json').read_text());checks=[]
def check(name,ok,detail=None):
 checks.append({'name':name,'passed':bool(ok),'detail':detail})
 if not ok:raise AssertionError((name,detail))
mp=try_load_asset(O/'ti_amostra_natural.ymap')
check('all_687_native_objects',len(mp.entities)==687)
check('unique_object_guids',len({e.guid for e in mp.entities})==687)
aliases=game['natural_sample']['source_models']
check('all_native_alias_archetypes',all(str(e.archetype_name) in aliases.values() for e in mp.entities))
for row in cfg['placements']:
 x,y,z=row['position'];x0,y0,x1,y1=cfg['bounds']
 assert x0<=x<=x1 and y0<=y<=y1 and row['ground_z']>0
 assert abs(x-(-715+14*math.sin((y+160)/54)))>=5
check('objects_on_dry_land_and_path_clear',True)
check('collision_enabled_on_static_objects',all(e.flags & EntityFlags.IS_STATIC and not e.flags.value&4 for e in mp.entities))
images=E.parse(F/'data/images.meta').getroot();mounted=[i.findtext('filename','').lower() for i in images]
for archive in ['v_palm','v_trees','v_ext_veg','v_bush','v_rocks']:
 check('native_archive_mounted_'+archive,any('/'+archive+'.rpf' in s for s in mounted))
check('no_duplicated_native_models_streamed',not any((O/(name+'.ydr')).exists() for name in cfg['models']))
native_types=try_load_asset(O/'ti_nature.ytyp')
check('12_self_contained_archetypes',len(native_types.archetypes)==12 and {str(t.name) for t in native_types.archetypes}==set(aliases.values()))
check('no_global_collision_dictionaries',not mp.physics_dictionaries and all(not str(t.physics_dictionary) for t in native_types.archetypes))
for model,alias in aliases.items():
 check('original_drawable_bytes_'+model,(O/(alias+'.ydr')).read_bytes()==(A/'fontes'/(model+'.ydr')).read_bytes())
for typ in native_types.archetypes:
 txd=str(typ.texture_dictionary)
 check('texture_dependency_'+str(typ.name),(O/(txd+'.ytd')).is_file() if txd else bool(try_load_asset(O/(str(typ.name)+'.ydr')).shader_group.embedded_textures))
types=[try_load_asset(p) for p in (A/'fontes').glob('*.ytyp')]
known={str(t.name) for typ in types for t in typ.archetypes}
check('archetypes_resolve_in_original_metadata',set(cfg['models'])<=known)
check('native_embedded_object_collisions',all(info['has_embedded_collision'] for info in cfg['models'].values()))
orig=try_load_asset(A/'backup'/f"{cfg['tile']['name']}.ybn");now=try_load_asset(O/f"{cfg['tile']['name']}.ybn")
b0,b1=orig.children[0],now.children[0]
v0=np.array([list(v.co) for v in b0.geometry_vertices]);v1=np.array([list(v.co) for v in b1.geometry_vertices]);delta=float(np.max(abs(v0-v1)))
check('collision_geometry_unchanged',np.allclose(v0,v1,atol=.005,rtol=0) and sorted(t.vertices for t in b0.geometry_primitives)==sorted(t.vertices for t in b1.geometry_primitives),{'max_resave_quantization_m':delta})
check('five_physical_ground_surfaces',len({t.material.material_index for t in b1.geometry_primitives})==5)
old=try_load_asset(A/'backup'/f"{cfg['tile']['name']}.ydr");new=try_load_asset(O/f"{cfg['tile']['name']}.ydr")
def triangles(asset,lod):
 out=[]
 for m in asset.models[lod]:
  for g in m.geometries:
   for tri in g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)]:out.append(tuple(sorted(tuple(float(round(x,4)) for x in v) for v in tri)))
 return sorted(out)
for lod in [LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW]:
 check('same_terrain_triangles_'+lod.name,triangles(old,lod)==triangles(new,lod))
 masks=np.concatenate([g.vertex_buffer['Colour1'] for m in new.models[lod] for g in m.geometries if new.shader_group.shaders[g.shader_index].preset_filename=='terrain_cb_4lyr.sps'])
 check('grass_and_dirt_masks_'+lod.name,int(masks[:,0].max())==0 and len(np.unique(masks[:,1:3],axis=0))>4)
check('native_ground_shader_with_normal_maps',new.shader_group.shaders[0].preset_filename=='terrain_cb_4lyr.sps')
for name,t in new.shader_group.embedded_textures.items():
 path=A/'texturas'/f'{name}.dds'
 if not path.exists():path=P/'nativo/texturas'/f'{name}.dds'
 shipped=t.data.read_bytes();source=path.read_bytes()
 def pixels(dds):return dds[148 if dds[84:88]==b'DX10' else 128:]
 if name==cfg['tile']['name']:
  check('preserved_border_albedo',np.array_equal(np.array(Image.open(io.BytesIO(shipped)).convert('RGBA')),np.array(Image.open(io.BytesIO(source)).convert('RGBA'))))
 else:check('original_dds_mips_'+name,pixels(shipped)==pixels(source))
baseline=R/'server-data/resources/teste_ilha/stream'
changed=[p.name for p in O.glob('*') if (baseline/p.name).exists() and p.read_bytes()!=(baseline/p.name).read_bytes()]
if not (A/'mudancas_stream.json').exists():
 check('only_one_sector_changed',sorted(changed)==sorted([cfg['tile']['name']+'.ydr',cfg['tile']['name']+'.ybn']),changed)
 (A/'mudancas_stream.json').write_text(json.dumps(changed))
else:check('only_one_sector_changed',len(json.loads((A/'mudancas_stream.json').read_text()))==2)
# Exercise destination streaming, incorrect stock ground, timeout and native exceptions.
cases=[('success',True,False,False,False,False),('no_collision',False,False,False,False,False),('vehicle',True,True,False,False,False),('stock_ground',True,False,True,False,True),('native_exception',True,False,False,True,False)]
for label,collision,vehicle,bad,broken,runway in cases:
 l=LuaRuntime(unpack_returned_tuples=True);g=l.globals();g.config=l.table_from(game,recursive=True)
 g.collision=collision;g.vehicle=vehicle;g.badGround=bad;g.brokenNative=broken;g.runwayGround=runway;g.waterResult=True;g.count=game['water_quads']
 l.execute((P/'scripts/mock_cliente_ilha.lua').read_text())
 l.execute((F/'client.lua').read_text());g.commands.amostrailha()
 check('never_permanently_frozen_'+label,not g.frozen)
 if vehicle:check('vehicle_visit_does_not_move_player',g.moved is None)
 else:
  check('restored_controls_and_camera_'+label,g.controlled and g.visible and g.entityCollision and g.gravity and g.cameraReleased and not g.focus and not g.scene and g.fadedIn and not g.nuiFocus)
  if label=='success':check('verified_visit_coordinates',abs(g.moved.x-cfg['visit']['x'])<1e-5 and abs(g.moved.z-cfg['visit']['z'])<1e-5)
  elif label=='stock_ground':check('incorrect_ground_returns_to_runway',abs(g.moved.x-game['spawn']['x'])<1e-5)
  else:check('failed_visit_returns_to_origin_'+label,g.moved.x==0 and g.moved.y==0 and g.moved.z==18)
  check('original_maps_removed_'+label,g.removedMaps is not None and g.removedMaps['bh1_09_strm_0'])
l=LuaRuntime(unpack_returned_tuples=True);g=l.globals();g.config=l.table_from(game,recursive=True)
g.collision=True;g.vehicle=False;g.missingModels=True;g.waterResult=True;g.count=game['water_quads']
l.execute((P/'scripts/mock_cliente_ilha.lua').read_text());l.execute((F/'client.lua').read_text());g.commands.amostrailha()
check('missing_models_does_not_teleport',g.moved is None and not g.frozen and g.controlled and g.cameraReleased and g.clock>=8000)
check('missing_models_never_reports_sample_ready',not any('Amostra natural:' in s for s in g.logs.values()))
report={'passed':True,'checks':checks,'in_game_verified':False};(A/'verificacao.json').write_text(json.dumps(report,indent=2));print('NATURAL_PILOT_VERIFIED',len(checks),flush=True)
