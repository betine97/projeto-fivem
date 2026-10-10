from pathlib import Path
import sys,json,xml.etree.ElementTree as E,hashlib
P=Path(__file__).resolve().parents[1];R=P.parent
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(R/'casa_vinewood/work/lua_syntax_deps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from lupa import LuaRuntime
from szio.gta5 import try_load_asset,LodLevel
checks=[]
def check(name,condition,detail=None):
 checks.append({'name':name,'passed':bool(condition),'detail':detail})
 if not condition:raise AssertionError((name,detail))
cfg=json.loads((P/'fivem/data/config.json').read_text());src=(R/'server-data/resources/cidade_core/client.lua').read_text()
for mode,available,col in [('cidade',True,True),('ilha',True,True),('ilha',False,True),('ilha',True,False)]:
 l=LuaRuntime(unpack_returned_tuples=True);g=l.globals();g.mode=mode;g.available=available;g.collision=col
 g.islandSpawn=l.table_from(cfg['spawn'])
 l.execute('''threads={};commands={};logs={};clock=0;frozen=nil;prepared=false
 function print(t)logs[#logs+1]=t end
 function RegisterCommand(n,f)commands[n]=f end
 function AddEventHandler()end
 function CreateThread(f)threads[#threads+1]=f end
 function GetConvar(n,d)return mode end
 function GetResourceState(n)return available and 'started' or 'missing' end
 function NetworkIsSessionStarted()return true end
 function GetGameTimer()return clock end
 function Wait(ms)clock=clock+ms end
 function PlayerPedId()return 1 end
 function FreezeEntityPosition(p,v)frozen=v end
 function HasCollisionLoadedAroundEntity()return collision end
 function RequestCollisionAtCoord()end
 function SetEntityMaxHealth()end;function SetEntityHealth()end;function SetMaxWantedLevel()end;function ShutdownLoadingScreenNui()end
 function BeginTextCommandThefeedPost()end;function AddTextComponentSubstringPlayerName()end;function EndTextCommandThefeedPostTicker()end
 exports={spawnmanager={},teste_ilha={}}
 function exports.spawnmanager:setAutoSpawn(v)auto=v end
 function exports.spawnmanager:spawnPlayer(p,cb)spawned=p;cb()end
 function exports.teste_ilha:getSpawn()return islandSpawn end
 function exports.teste_ilha:prepareSpawn()prepared=true end
 ''')
 l.execute(src);g.threads[1]()
 label=f'{mode},resource={available},collision={col}'
 check('manual_spawn_'+label,g.auto is False)
 if mode=='cidade':check('city_mode_retains_city_spawn',abs(g.spawned.x-195.17)<1e-4 and not g.prepared)
 elif not available:check('missing_island_never_falls_back_to_city',g.spawned is None and len(g.logs)>0)
 else:
  check('island_spawn_'+label,g.prepared and abs(g.spawned.x-cfg['spawn']['x'])<1e-4 and g.spawned.z==cfg['spawn']['z'])
  check('spawn_collision_protection_'+label,g.frozen is (not col))
# Parse every active Lua file using the actual Lua runtime, including manifests.
parser=LuaRuntime();load=parser.eval('function(s,n) local f,e=load(s,n);return f~=nil,e end')
for path in list((P/'fivem').glob('*.lua'))+[R/'server-data/resources/cidade_core/client.lua']:
 ok,error=load(path.read_text(),path.name);check('lua_syntax_'+path.name,ok,error)
level=E.parse(P/'fivem/ilha.meta').getroot();images=E.parse(P/'fivem/data/images.meta').getroot()
allfiles=[i.findtext('filename','').lower() for i in images]+[i.findtext('filename','').lower() for i in level.find('dataFiles')]
check('original_city_archives_excluded',not any('/_city' in f or '/_country' in f or 'minimap.rpf' in f or 'navmeshes' in f for f in allfiles))
check('original_city_placement_excluded',not any(i.findtext('fileType') in ['IPL_FILE','WORLD_HEIGHTMAP_FILE','WORLD_WATERHEIGHT_FILE','SCENARIO_POINTS_PSO_FILE','DISTANT_LIGHTS_FILE'] for i in level.find('dataFiles')))
manifest=(P/'fivem/fxmanifest.lua').read_text()
includes=[n.get('href') for n in level.find('includedXmlFiles').iter() if n.tag.endswith('include')]
check('images_include_uses_mounted_resource_uri','resources:/teste_ilha/data/images.meta' in includes and not any('cfx_resource_' in n for n in includes))
waters=[n.findtext('filename') for n in level.find('dataFiles') if n.findtext('fileType')=='WATER_FILE']
check('ocean_loaded_with_custom_level',waters==['resources:/teste_ilha/data/water.xml'])
check('water_resource_mount_declared',"data_file 'WATER_FILE' 'data/water.xml'" in manifest)
check('water_grid_clip_never_expanded','SetWaterAreaClipRect(' not in (P/'fivem/client.lua').read_text())
check('water_native_xml_header',(P/'fivem/data/water.xml').read_bytes().startswith(b'<?xml version="1.0" encoding="UTF-8"?>'))
blocked=json.loads((P/'fivem/data/mapas_originais.json').read_text())
check('rooftop_map_blacklisted','bh1_09_strm_0' in blocked and 'ti_amostra_natural' not in blocked)
check('original_map_blacklist_excludes_authored_map',not any(s.startswith('ti_') or s=='teste_ilha' for s in blocked))
for uri in includes+waters:
 if uri.startswith('resources:'):
  name=uri.removeprefix('resources:/teste_ilha/')
  check('resource_uri_resolves_'+name,(P/'fivem'/name).is_file() and "'"+name+"'" in manifest)
# Exercise actual client exports, including stale-world detection and native
# failures. Loading a terrain alone must not count as a verified empty world.
for city,result,count,delayed in [(False,True,690,False),(True,True,690,False),(False,False,0,False),(False,True,0,False),(False,True,690,True)]:
 l=LuaRuntime(unpack_returned_tuples=True);g=l.globals()
 g.config=l.table_from(cfg,recursive=True);g.city=city;g.waterResult=result;g.count=count;g.waterDelayed=delayed
 l.execute((P/'scripts/mock_cliente_ilha.lua').read_text())
 l.execute((P/'fivem/client.lua').read_text());g.exports.prepareSpawn()
 logs='\n'.join(g.logs.values());label=f'city={city},water={result},count={count}'
 check('stale_world_warning_'+label,('Mapa antigo ainda carregado' in logs)==city,logs)
 check('water_failure_warning_'+label,('Agua personalizada ainda nao carregou' in logs)==(not result or count!=cfg['water_quads']),logs)
 if delayed:check('water_waits_for_streaming_update',g.clock>=200 and 'Agua nativa: true' in logs)
active=(R/'server-data/server-ilha.cfg').read_text();check('island_resource_before_spawn',active.index('ensure teste_ilha')<active.index('ensure cidade_core'))
check('city_maps_inactive_in_island_mode',not any('ensure '+v+'\n' in active for v in ['cidade_mansao','cidade_laboratorio','cidade_castelo_livre','cidade_castelo_previa','cidade_hospital_carcer']))
check('default_launcher_island',(R/'server-data/server.cfg').read_text().strip().endswith('exec server-ilha.cfg') and "$Modo='ilha'" in (R/'iniciar-cidade.ps1').read_text(encoding='utf-8-sig'))
check('city_mode_retained','ensure cidade_mansao' in (R/'server-data/server-cidade.cfg').read_text() and (R/'iniciar-cidade-original.cmd').exists())
water=E.parse(P/'fivem/data/water.xml').getroot().find('WaterQuads');check('native_water_bounds',all(float(q.find('minX').get('value'))<float(q.find('maxX').get('value')) and float(q.find('minY').get('value'))<float(q.find('maxY').get('value')) for q in water),len(water))
rows=json.loads((P/'nativo/pacote.json').read_text());vertex_errors=[];collisions=0
for row in rows:
 a=try_load_asset(P/'fivem/stream'/f"{row['name']}.ydr")
 counts=[sum(len(g.index_buffer)//3 for m in a.models[lod] for g in m.geometries) for lod in [LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW]]
 check('native_lods_'+row['name'],all(counts[i]>=counts[i+1]>0 for i in range(3)),counts)
 for m in a.models[LodLevel.HIGH]:
  for g in m.geometries:
   if not np.isfinite(g.vertex_buffer['Position']).all() or int(g.index_buffer.max())>=len(g.vertex_buffer):vertex_errors.append(row['name'])
 mp=try_load_asset(P/'fivem/stream'/f"{row['name']}_map.ymap")
 check('ymap_position_'+row['name'],np.max(np.abs(np.array(mp.entities[0].position)-row['center']))<.001)
 if row['collision_triangles']:
  b=try_load_asset(P/'fivem/stream'/f"{row['name']}.ybn");check('world_collision_dictionary_'+row['name'],str(mp.physics_dictionaries[0])==row['name'] and len(b.children[0].geometry_primitives)==row['collision_triangles']);collisions+=1
check('all_native_positions_and_indices',not vertex_errors,vertex_errors);check('42_world_collision_sectors',collisions==42)
installed=R/'server-data/resources/teste_ilha';mismatch=[str(f.relative_to(P/'fivem')) for f in (P/'fivem').rglob('*') if f.is_file() and (not(installed/f.relative_to(P/'fivem')).exists() or hashlib.sha256(f.read_bytes()).digest()!=hashlib.sha256((installed/f.relative_to(P/'fivem')).read_bytes()).digest())]
check('installed_resource_matches_package',not mismatch,mismatch)
report={'passed':True,'checks':checks,'in_game_verified':False}
(P/'nativo/verificacao_integracao.json').write_text(json.dumps(report,indent=2));print('ISLAND_INTEGRATION_PASSED',len(checks),flush=True)
