"""Prove closure and 4K filtered textures in serialized game geometry."""
from pathlib import Path
import sys,json,io,struct,hashlib
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset
a=try_load_asset(W/'fivem/mansao_mobiliario.ydr');checks=[]
for family in ('sofa','tv'):
 triangles=[];zero_tangents=0;screen_uv=[]
 for lod in a.models.values():
  for model in lod:
   for g in model.geometries:
    shader=a.shader_group.shaders[g.shader_index];params={p.name.lower():p.value for p in shader.parameters}
    if str(params['diffusesampler'])!=family+'_albedo':continue
    tri=g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)]
    triangles.extend(tri)
    if family=='tv':
     centers=tri.mean(axis=1)
     hit=np.linalg.norm(centers-np.array([-8.784946,-9.580075,1.240979]),axis=1)<.0001
     screen_uv.extend(g.vertex_buffer['TexCoord0'][g.index_buffer.reshape(-1,3)][hit])
    N=g.vertex_buffer['Normal'];T=g.vertex_buffer['Tangent'];assert np.isfinite(N).all() and np.isfinite(T).all()
    assert abs(np.linalg.norm(N,axis=1)-1).max()<1e-4
    zero_tangents+=int(sum(np.linalg.norm(T[:,:3],axis=1)<.5))
    assert float(params['specularintensitymult'][0])<=.23
    assert float(params['wetnessmultiplier'][0])==0
 assert zero_tangents==0,(family,zero_tangents)
 triangles=np.array(triangles);verts,ids=np.unique(triangles.reshape(-1,3),axis=0,return_inverse=True);ids=ids.reshape(-1,3)
 edges=np.sort(np.concatenate((ids[:,[0,1]],ids[:,[1,2]],ids[:,[2,0]])),axis=1)
 unique,counts=np.unique(edges,axis=0,return_counts=True)
 boundary=int(sum(counts==1));nonmanifold=int(sum(counts!=2));assert boundary==0 and nonmanifold==0,(family,boundary,nonmanifold)
 area=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)*.5
 assert area.min()>1e-12
 maps=[]
 for suffix in ('albedo','normal','spec'):
  raw=a.shader_group.embedded_textures[family+'_'+suffix].data.read_bytes();im=Image.open(io.BytesIO(raw));mips=struct.unpack_from('<I',raw,28)[0]
  assert mips==int(np.log2(max(im.size)))-1
  if suffix in ('albedo','normal'):assert im.size==(4096,4096)
  maps.append(dict(name=family+'_'+suffix,size=list(im.size),mip_count=mips))
 screen_check=None
 if family=='tv':
  assert len(screen_uv)==1
  raw=a.shader_group.embedded_textures['tv_albedo'].data.read_bytes();pixels=np.array(Image.open(io.BytesIO(raw)).convert('RGB'))
  samples=[];u=screen_uv[0]
  for i in range(11):
   for j in range(11-i):
    co=(u[0]*i+u[1]*j+u[2]*(10-i-j))/10
    samples.append(pixels[int(co[1]*4095),int(co[0]*4095)])
  peak=int(np.max(samples));assert peak<35,peak
  screen_check=dict(repaired_triangle_samples=len(samples),maximum_rgb_channel=peak,no_wood_atlas_bleed=True)
 checks.append(dict(family=family,triangles=len(triangles),welded_vertices=len(verts),boundary_edges=boundary,nonmanifold_edges=nonmanifold,degenerate_triangles=0,zero_tangents=zero_tangents,embedded_maps=maps,screen_uv_check=screen_check))
report=dict(passed=True,mesh_checks=checks,sha256=hashlib.sha256((W/'fivem/mansao_mobiliario.ydr').read_bytes()).hexdigest(),in_game_verified=False)
(W/'verificacao_malha_mobiliario.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('FURNITURE_NATIVE_MESH_QUALITY',checks,flush=True)
