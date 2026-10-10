"""Verify exported geometry, hydrology and the independent city snapshot."""
from pathlib import Path
import sys,json,struct,hashlib,sqlite3
P=Path(__file__).resolve().parents[1];R=P.parent
sys.path.insert(0,str(R/'laboratorio_fivem/work/pydeps'))
import numpy as np
from PIL import Image
d=np.load(P/'dados/terreno.npz');g=d['terrain'].astype(np.float64);meta=json.loads((P/'dados/medidas.json').read_text());checks={}
def check(name,condition,details=None):
 checks[name]={'passed':bool(condition),'details':details}
 if not condition:print('FAIL',name,details)
check('finite_heightfield',np.isfinite(g).all(),list(g.shape))
# Compute clipped triangle footprint independently from the saved, rounded mesh.
def fraction(z):
 k=(z>0).sum(-1);f=(k==3).astype(float)
 for i in range(3):
  a,b,c=z[...,i],z[...,(i+1)%3],z[...,(i+2)%3]
  t=np.divide(a,a-b,out=np.zeros_like(a),where=np.abs(a-b)>1e-12)*np.divide(a,a-c,out=np.zeros_like(a),where=np.abs(a-c)>1e-12)
  f=np.where((k==1)&(a>0),t,f);f=np.where((k==2)&(a<=0),1-t,f)
 return f
z=g[:,:,2];dx=g[0,1,0]-g[0,0,0];dy=g[1,0,1]-g[0,0,1]
area=sum(fraction(q).sum() for q in [np.stack([z[:-1,:-1],z[:-1,1:],z[1:,1:]],-1),np.stack([z[:-1,:-1],z[1:,1:],z[1:,:-1]],-1)])*dx*dy/2
ratio=area/(meta['reference_land_area_km2_estimate']*1e6)
check('three_times_reference_area',abs(ratio-3)<.001,{'saved_mesh_area_m2':float(area),'ratio':float(ratio),'tolerance_ratio':.001})
check('river_descends_to_sea',np.max(np.diff(d['river_z']))<=1e-4 and abs(float(d['river_z'][-1]))<1e-4,{'source_z':float(d['river_z'][0]),'mouth_z':float(d['river_z'][-1])})
check('lake_and_river_source_match',np.linalg.norm(d['lakecenter']-d['river_points'][0])<.001,{'distance_m':float(np.linalg.norm(d['lakecenter']-d['river_points'][0]))})
def sample(xy):
 ix=(xy[:,0]-g[0,0,0])/(g[0,-1,0]-g[0,0,0])*(len(g)-1);iy=(xy[:,1]-g[0,0,1])/(g[-1,0,1]-g[0,0,1])*(len(g)-1)
 a=np.minimum(np.maximum(ix.astype(int),0),len(g)-2);b=np.minimum(np.maximum(iy.astype(int),0),len(g)-2);tx=ix-a;ty=iy-b
 return (z[b,a]*(1-tx)+z[b,a+1]*tx)*(1-ty)+(z[b+1,a]*(1-tx)+z[b+1,a+1]*tx)*ty
bed=sample(d['river_points']);depth=d['river_z']-bed
check('river_center_below_water',float(depth.min())>0,{'min_depth_m':float(depth.min()),'max_depth_m':float(depth.max())})
check('lake_bed_below_water',float(sample(d['lakecenter'][None])[0])<float(d['lakeheight']))
run=meta['runway'];cx,cy=run['center_m'];q=np.array([[x,y] for x in np.linspace(cx-run['length_m']/2,cx+run['length_m']/2,50) for y in [cy-run['width_m']/2,cy,cy+run['width_m']/2]])
error=np.max(np.abs(sample(q)-run['level_m']))
check('runway_graded',error<.10,{'max_height_error_m':float(error)})
check('authoral_undeveloped_island',meta['native_city_geometry_in_asset'] is False and meta['trees']==0 and meta['buildings']==0)
im=Image.open(P/'texturas/albedo_terreno.png');check('terrain_texture_4k',im.size==(4096,4096))
hm=Image.open(P/'dados/altura_16bits.png');check('heightmap_16bit',hm.mode in ['I;16','I;16B','I'],{'mode':hm.mode,'size':list(hm.size)})
# Validate GLB structural integrity and all buffer bounds without loading a viewer.
blob=(P/'exportacoes/ilha_terreno.glb').read_bytes();magic,version,size=struct.unpack_from('<4sII',blob)
check('glb_header',magic==b'glTF' and version==2 and size==len(blob))
jl,jt=struct.unpack_from('<II',blob,12);doc=json.loads(blob[20:20+jl]);off=20+jl;bl,bt=struct.unpack_from('<II',blob,off);binary=blob[off+8:off+8+bl]
check('glb_binary_chunk',bt==0x004e4942 and len(binary)==bl)
sizes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16};types={5120:np.int8,5121:np.uint8,5122:np.int16,5123:np.uint16,5125:np.uint32,5126:np.float32}
accessors=[];valid=True
for a in doc['accessors']:
 bv=doc['bufferViews'][a['bufferView']];dtype=np.dtype(types[a['componentType']]);n=sizes[a['type']];offset=bv.get('byteOffset',0)+a.get('byteOffset',0);stride=bv.get('byteStride',dtype.itemsize*n)
 end=offset+(a['count']-1)*stride+dtype.itemsize*n
 valid &= end<=bv.get('byteOffset',0)+bv['byteLength'] and end<=len(binary)
 ar=np.ndarray((a['count'],n),dtype=dtype,buffer=binary,offset=offset,strides=(stride,dtype.itemsize));accessors.append(ar);valid &= bool(np.isfinite(ar).all())
check('glb_accessors_finite_and_in_bounds',valid,{'accessors':len(accessors)})
index_ok=True;triangles=0
for m in doc['meshes']:
 for pr in m['primitives']:
  pos=accessors[pr['attributes']['POSITION']];idx=accessors[pr['indices']].ravel();index_ok &= int(idx.max())<len(pos) and len(idx)%3==0;triangles+=len(idx)//3
check('glb_triangle_indices',index_ok,{'triangles':triangles,'meshes':len(doc['meshes'])})
check('glb_water_meshes',any('RIO' in n.get('name','') for n in doc['nodes']) and any('LAGO' in n.get('name','') for n in doc['nodes']))
check('glb_embedded_texture',any('bufferView' in im for im in doc.get('images',[])))
inventory=json.loads((P/'cidade-original-preservada/inventario.json').read_text());bad=[]
for f in inventory['files']:
 p=P/f['backup']
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=f['sha256']:bad.append(f['backup'])
check('city_snapshot_hashes',not bad,{'files':len(inventory['files']),'mismatches':bad})
configs=[f for f in inventory['files'] if f['original'].endswith('.cfg')];different=[f['original'] for f in configs if hashlib.sha256((R/f['original']).read_bytes()).hexdigest()!=f['sha256']]
check('live_server_configs_unchanged',not different,{'checked':len(configs),'changed':different})
with sqlite3.connect(f"file:{(P/'cidade-original-preservada/painel_acesso/data/usuarios.sqlite3').as_posix()}?mode=ro",uri=True) as db:integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
check('snapshot_database_integrity',integrity=='ok')
report={'passed':all(c['passed'] for c in checks.values()),'checks':checks,'in_game_verified':False,'native_world_isolation_activated':False,'native_water_physics_configured':False}
(P/'dados/verificacao.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('ISLAND_VERIFICATION',report['passed'],len(checks))
sys.exit(0 if report['passed'] else 1)
