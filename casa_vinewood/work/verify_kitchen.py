import sys,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';KITCHENOUT=W/'cozinha_fivem';SERVER=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),str(W/'work'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset
kitchen=json.loads((W/'cozinha_completa.json').read_text());drawable=try_load_asset(KITCHENOUT/(kitchen['model']+'.ydr'));assert drawable and drawable.bounds;geos=[g for lod in drawable.models.values() for m in lod for g in m.geometries];count=0
for g in geos:
 vb=g.vertex_buffer
 for field in ('Position','Normal','TexCoord0'):assert np.isfinite(vb[field]).all(),field
 assert np.min(np.linalg.norm(vb['Normal'],axis=1))>.8
 if 'Tangent' in vb.dtype.names:assert np.isfinite(vb['Tangent']).all() and np.min(np.linalg.norm(vb['Tangent'][:,:3],axis=1))>.5
 else:assert drawable.shader_group.shaders[g.shader_index].preset_filename=='emissive.sps'
 ts=vb['Position'][g.index_buffer.reshape(-1,3)];area=np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1)/2
 assert np.min(area)>1e-11,(g.shader_index,np.min(area));count+=len(ts)
assert count==kitchen['triangles'];assert len(drawable.shader_group.embedded_textures)==28
for name,tex in drawable.shader_group.embedded_textures.items():
 data=tex.data.read_bytes();assert data[:4]==b'DDS ';height,width=struct.unpack_from('<II',data,12);mips=struct.unpack_from('<I',data,28)[0];assert width&(width-1)==0 and height&(height-1)==0;assert mips>=int(np.log2(min(width,height)))-1,(name,width,height,mips)
origin=np.array(kitchen['origin']);mp=try_load_asset(KITCHENOUT/'mansao_cozinha_completa.ymap');typ=try_load_asset(KITCHENOUT/'mansao_cozinha_completa.ytyp');assert len(mp.entities)==2 and len(typ.archetypes)==1;assert np.max(abs(np.array(mp.entities[0].position)-origin))<.0001
assert kitchen['hi'][0]<14.186 and kitchen['hi'][2]<2.358 and kitchen['hi'][1]<-6.5;assert kitchen['real_sink_cutout'];assert kitchen['counter_height_m']==.91
# Test the currently installed architecture and furniture, then add all decor and the kitchen.
source=(W/'work/verify_fit.py').read_text();base=source.split('routes={}')[0];base=base.replace("OUT=W/('backup_antes_limpeza/fivem' if BASELINE else 'fivem')","OUT=SERVER/'stream'");exec(base)
cfg=json.loads((KITCHENOUT/'decoracao_iluminacao.json').read_text())
for row in cfg['plants']:
 a=try_load_asset(W/'work/decor_native'/(row['model']+'.ydr'));tx=np.eye(4);tx[:3,:3]*=row['scale'];visit(a.bounds,parent=tx,offset=np.array(row['position']),label='decor_plant_'+row['name'])
custom=json.loads((W/'vaso_planta_autoral.json').read_text());plant=try_load_asset(SERVER/'stream'/(custom['model']+'.ydr'))
for row in custom['instances']:
 h=row['heading'];c=np.cos(h);s=np.sin(h);tx=np.eye(4);tx[:3,:3]=np.array([[c,s,0],[-s,c,0],[0,0,1]]);visit(plant.bounds,parent=tx,offset=np.array(row['position']),label='custom_pot_'+row['name'])
visit(drawable.bounds,label='mansao_cozinha_parede')
T=np.array(faces);low=T.min(1);high=T.max(1);norm=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);SL=np.array([ps.min(0)-pad for kind,ps,pad,label in smooth]);SH=np.array([ps.max(0)+pad for kind,ps,pad,label in smooth])
exec('routes={}\n'+source.split('routes={}')[1].split('fit=json.loads')[0])
route('Passagem entre sofa e jantar',[(-.5,-10.85,-.8),(.8,-10.85,-.8),(4.5,-10.85,-.8)])
route('Passagem cozinha',[(8.85,-11.05,-.8),(11.35,-11.05,-.8),(11.35,-6.95,-.8)])
route('Volta completa da mesa',[(.8,-10.85,-.8),(4.5,-10.85,-.8),(4.5,-5.8,-.8),(.8,-5.8,-.8),(.8,-10.85,-.8)])
route('Entre jantar e cozinha',[(4.5,-8.3,-.8),(8.85,-8.3,-.8)])
route('Circulacao sala ao lado do vaso',[(-8.4,-3.55,-.8),(-6.8,-3.55,-.8),(-3.5,-3.55,-.8)])
route('Circulacao hall escada ao lado do vaso',[(3.5,1.65,-.8),(5.1,1.65,-.8),(6.1,1.65,-.8)])
route('Corredor entre ilha e bancada',[(12.40,-6.45,-.8),(12.40,-12.25,-.8)])
route('Acesso frente do forno',[(12.40,-6.95,-.8),(13.00,-6.95,-.8)])
assert all(q['passed'] for q in routes.values()),{k:v for k,v in routes.items() if not v['passed']}
assert any(x.startswith('mansao_cozinha_parede') for x in blockers(np.array([13.51,-9.0,-.8]))),'Kitchen collision missing'
light=json.loads((KITCHENOUT/'iluminacao_ambiente.json').read_text());oldlight=json.loads((SERVER/'iluminacao_ambiente.json').read_text())
for key in ('max_lights','budgets','day_multiplier','night_multiplier'):assert light[key]==oldlight[key]
assert all(q in light['lights'] for q in oldlight['lights']);assert len([q for q in light['lights'] if q['id'].startswith('kitchen_led_')])==5
decor=try_load_asset(KITCHENOUT/'mansao_decoracao.ymap');olddecor=try_load_asset(SERVER/'stream/mansao_decoracao.ymap');assert len(decor.entities)==len(olddecor.entities)
changed=[]
for i,(a,b) in enumerate(zip(decor.entities,olddecor.entities)):
 assert str(a.archetype_name)==str(b.archetype_name);assert a.scale_xy==b.scale_xy and a.scale_z==b.scale_z;assert np.max(abs(np.array(a.rotation)-np.array(b.rotation)))<1e-6
 if np.linalg.norm(np.array(a.position)-np.array(b.position))>.001:changed.append(i)
assert changed==[kitchen['plant_relocation']['map_entity_index']],changed
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in KITCHENOUT.iterdir() if p.suffix in ('.ydr','.ymap','.ytyp','.json')}
report={'passed':True,'triangles':count,'editable_parts':kitchen['parts'],'walking_routes':routes,'wall_fit':True,'sink_cutout':True,'materials':len(drawable.shader_group.shaders),'texture_mipmaps':True,'original_lighting_budget_preserved':True,'only_one_existing_plant_moved':True,'files':files,'in_game_verified':False}
(W/'verificacao_cozinha_completa.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('KITCHEN_VERIFIED',count,'triangles;',len(routes),'walking routes;',len(drawable.shader_group.embedded_textures),'mipmapped textures',flush=True)
