"""Read native materials, geometry, furniture UVs and actual walking clearance."""
import sys,json,hashlib,io
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset
config=json.loads((W/'materiais_sala.json').read_text());spec=json.loads((W/'aplicacao_materiais_sofa.json').read_text());scene=json.loads((W/'inspecao_materiais_blender.json').read_text())
models=json.loads((W/'exportacao_fivem.json').read_text())['models']
assets={m['name']:try_load_asset(W/'fivem'/(m['name']+'.ydr')) for m in models}
family_texture={'marble':'piso_marmore','wall':'parede_reboco','brick':'parede_tijolo_tv','metal':'corrimao_preto','sofa':'sofa_albedo','tv':'tv_albedo'}
texture_checks=[];triangles={};triangle_textures={};furniture_vertices=[];furniture_uvs=[];architectural_uv_error=0.;architectural_uv_probes=0
expected={Path(config[k][p]).stem:Path(config[k][p]) for k in ('marble','wall','brick','metal') for p in ('diffuse','normal')}
expected.update({n:W/'work/materiais'/(n+'.dds') for n in ('sofa_albedo','sofa_normal','sofa_spec','tv_albedo','tv_normal','tv_spec')})
for name,a in assets.items():
 ts=[];textures=[]
 for texname,tex in a.shader_group.embedded_textures.items():
  if texname not in expected:continue
  actual=np.array(Image.open(io.BytesIO(tex.data.read_bytes())).convert('RGBA'))
  original=np.array(Image.open(expected[texname]).convert('RGBA'))
  assert actual.shape==original.shape and np.array_equal(actual,original),(name,texname)
  import struct
  mip_count=struct.unpack_from('<I',tex.data.read_bytes(),28)[0]
  # Native compressed textures stop at the final 4x4 block.
  assert mip_count==int(np.log2(max(actual.shape[:2])))-1,(name,texname,mip_count)
  texture_checks.append(dict(drawable=name,texture=texname,size=list(actual.shape[:2]),mip_count=mip_count,decoded_pixels_equal=True))
 for lod in a.models.values():
  for model in lod:
   for g in model.geometries:
    shader=a.shader_group.shaders[g.shader_index]
    texture=str(next(p.value for p in shader.parameters if p.name.lower()=='diffusesampler'))
    T=g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)].astype(float)
    ts.extend(T);textures.extend([texture]*len(T))
    family=next((k for k,v in family_texture.items() if v==texture),None)
    if family in ('marble','wall','brick','metal'):
     ids=g.index_buffer.reshape(-1,3);points=g.vertex_buffer['Position'][ids];UV=g.vertex_buffer['TexCoord0'][ids]
     normal=np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0]);axis=np.argmax(abs(normal),axis=1)
     expected_uv=np.zeros_like(UV)
     for dominant,axes in ((2,(0,1)),(1,(0,2)),(0,(1,2))):
      ix=np.flatnonzero(axis==dominant);expected_uv[ix]=points[ix][:,:,axes]/config[family]['tile_m']
     expected_uv[:,:,1]=1-expected_uv[:,:,1]
     error=float(abs(UV-expected_uv).max());assert error<.001,(name,family,error)
     architectural_uv_error=max(architectural_uv_error,error);architectural_uv_probes+=len(UV)*3
     params={p.name.lower():p.value for p in shader.parameters}
     assert np.max(abs(params['globalanimuv0']-np.array([1,0,0,0])))<1e-6
     assert np.max(abs(params['globalanimuv1']-np.array([0,1,0,0])))<1e-6
    if name=='mansao_mobiliario' and texture=='sofa_albedo':
     furniture_vertices.extend(g.vertex_buffer['Position']);furniture_uvs.extend(g.vertex_buffer['TexCoord0'])
 triangles[name]=np.array(ts);triangle_textures[name]=np.array(textures)
assert set(expected).issubset({q['texture'] for q in texture_checks})
for k in ('marble','wall','brick','metal'):
 assert hashlib.sha256(Path(config[k]['source']).read_bytes()).hexdigest()==config[k]['source_sha256']
assert hashlib.sha256(Path(config['sofa']['glb_source']).read_bytes()).hexdigest()==config['sofa']['glb_sha256']
groups={'01_':'mansao_paredes','02_':'mansao_paredes','03_':'mansao_paredes','04_':'mansao_pisos','05_':'mansao_escada'}
probe_count=0;counts={};failures=[]
for row in scene:
 if 'material_probes' not in row:continue
 if not any(row['collection'].startswith(k) for k in groups):continue
 name=next(v for k,v in groups.items() if row['collection'].startswith(k));T=triangles[name];low=T.min(1);high=T.max(1)
 for probe in row['material_probes']:
  family=probe['family']
  if family not in family_texture:continue
  q=np.array(probe['position']);ix=np.flatnonzero(np.all(low<=q+1e-4,1)&np.all(high>=q-1e-4,1))
  if len(ix):
   t=T[ix];a,b,c=t[:,0],t[:,1],t[:,2];n=np.cross(b-a,c-a);nn=np.einsum('ij,ij->i',n,n);ds=np.einsum('ij,ij->i',q-a,n);valid=(nn>1e-14)&(abs(ds)/np.sqrt(np.maximum(nn,1e-30))<1e-4)
   for u,v in ((a,b),(b,c),(c,a)):valid&=np.einsum('ij,ij->i',np.cross(v-u,q-u),n)>=-1e-7
   ix=ix[valid]
  if not len(ix) or family_texture[family] not in triangle_textures[name][ix]:failures.append(dict(source=row['name'],family=family,position=q.tolist()))
  probe_count+=1;counts[family]=counts.get(family,0)+1
assert not failures,failures[:8]
assert all(counts.get(k,0)>0 for k in ('marble','wall','brick','metal')),counts
T=triangles['mansao_paredes'][triangle_textures['mansao_paredes']=='parede_tijolo_tv'];assert len(T)>0
assert np.max(abs(T[:,:,0]+9.056))<1e-4 and T[:,:,1].min()>-11.601 and T[:,:,1].max()<-6.099
T=triangles['mansao_pisos'];n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);ground=(n[:,2]>1e-6)&(np.max(abs(T[:,:,2]+.8),1)<1e-4)
assert all(triangle_textures['mansao_pisos'][ground]=='piso_marmore')
upper=(n[:,2]>1e-6)&(np.max(abs(T[:,:,2]-2.808),1)<1e-4)
hall=spec['upper_wood_hall_bounds'];c=T.mean(1)
wood_area=(c[:,0]>hall[0]-1e-5)&(c[:,0]<hall[1]+1e-5)&(c[:,1]>hall[2]-1e-5)&(c[:,1]<hall[3]+1e-5)
assert all(triangle_textures['mansao_pisos'][upper&wood_area]=='im_wood_panels_05')
assert all(triangle_textures['mansao_pisos'][upper&~wood_area]=='piso_marmore')
sofa=next(r for r in scene if r['collection'].startswith('10_') and 'Sofa' in r['name']);P=np.array(furniture_vertices);UV=np.array(furniture_uvs)
assert sum(triangle_textures['mansao_mobiliario']=='sofa_albedo')==spec['sofa_game_triangles']==120000
assert sum(triangle_textures['mansao_mobiliario']=='tv_albedo')==spec['tv']['game_triangles']
assert np.max(abs(P.min(0)-spec['sofa_bounds']['lo']))<1e-4 and np.max(abs(P.max(0)-spec['sofa_bounds']['hi']))<1e-4
assert np.isfinite(UV).all() and UV.min()>-.001 and UV.max()<1.001
uv_error=0.
for probe in sofa['uv_probes']:
 q=np.array(probe['position']);ix=np.flatnonzero(np.linalg.norm(P-q,axis=1)<1e-4);assert len(ix)
 expected_uv=np.array([probe['uv'][0],1-probe['uv'][1]])
 err=float(np.linalg.norm(UV[ix]-expected_uv,axis=1).min());uv_error=max(uv_error,err);assert err<.001,err
# Use the same body and support tests as the whole-house native collision audit.
room_spec=spec
source=Path(__file__).with_name('verify_fit.py').read_text();exec(source.split('routes={}')[0])
spec=room_spec
route_code='routes={}\n'+source.split('routes={}')[1].split("route('entrada_original'")[0];exec(route_code)
ring=[(-6.3,-11.95,-.8),(-1.65,-11.95,-.8),(-1.65,-5.65,-.8),(-6.3,-5.65,-.8),(-6.3,-11.95,-.8)]
route('Ao redor do sofa e mesa',ring)
route('Entre sofa e mesa',[(-4.025,-5.6,-.8),(-4.025,-9.2,-.8)])
assert all(r['passed'] for r in routes.values()),routes
checks=dict(passed=True,revision=spec['revision'],source_hashes_match=True,embedded_texture_checks=texture_checks,architectural_material_surface_probes=probe_count,material_probe_counts=counts,material_assignment_failures=failures,whole_ground_floor_marble=True,tv_brick_panel_matches=True,sofa_native_triangles=len(triangles['mansao_mobiliario']),sofa_source_uv_probes=len(sofa['uv_probes']),sofa_max_uv_error=uv_error,sofa_width_m=spec['sofa_bounds']['dimensions'][1],sofa_floor_clearance_m=spec['sofa_bounds']['lo'][2]+.8,walking_routes=routes,drawable_sha256={n+'.ydr':hashlib.sha256((W/'fivem'/(n+'.ydr')).read_bytes()).hexdigest() for n in assets},in_game_verified=False)
checks.update(architectural_uv_corner_probes=architectural_uv_probes,architectural_max_uv_error=architectural_uv_error,upper_floor_marble_outside_marked_hall=True,sofa_closed_after_optimization=spec['sofa_quality']['boundary_edges_after_optimization']==0,tv_closed_after_optimization=spec['tv']['boundary_edges_after_optimization']==0,tv_native_triangles=spec['tv']['game_triangles'])
(W/'verificacao_materiais_sofa.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('ROOM_FINISHES_NATIVE_OK',probe_count,'surface probes;',len(texture_checks),'embedded textures;',len(sofa['uv_probes']),'sofa UV probes;',len(routes),'walking routes',flush=True)
