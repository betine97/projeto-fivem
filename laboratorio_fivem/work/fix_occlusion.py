import sys,json,numpy as np,copy,hashlib,shutil
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.gta5 import *
from clip_geometry import subtract_box
w=Path(__file__).resolve().parent;pd=json.loads((w.parent/'placement.json').read_text());basis=np.array(pd['basis']);origin=np.array(pd['origin'])
out=w.parent/'occlusion_fix';out.mkdir(exist_ok=True)
# Clear only the occupied interior/vestibule, with a small wall/camera margin.
lo=np.array([-4.4,-8.5,-.5]);hi=np.array([4.4,6.6,4.1])
report={'local_cut_min':lo.tolist(),'local_cut_max':hi.tolist(),'maps':[],'in_game_verified':False}
for p in (w/'base_assets').glob('*occl*.ymap'):
 a=try_load_asset(p);changes=[]
 for i,b in enumerate(a.model_occluders):
  xyz=(b.vertices-origin)@basis;verts=[];inds=[];changed=[]
  for j,t in enumerate(b.indices):
   v=xyz[t];pieces,hit=subtract_box(list(v),lo,hi)
   if hit:changed.append(j)
   for poly in pieces:
    for k in range(1,len(poly)-1):
     tri=np.array([poly[0],poly[k],poly[k+1]])
     if np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))<1e-7:continue
     off=len(verts);verts.extend(tri@basis.T+origin);inds.append([off,off+1,off+2])
  if changed:
   old=len(b.indices);unique,inverse=np.unique(np.round(np.array(verts),5),axis=0,return_inverse=True);assert len(unique)<256; b.vertices=unique.astype(b.vertices.dtype);b.indices=inverse[np.array(inds)].astype(b.indices.dtype)
   changes.append({'model':i,'original_triangles':old,'cut_triangles':changed,'result_triangles':len(inds)})
 if not changes:continue
 save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),out,p.stem)
 check=try_load_asset(out/p.name)
 assert len(check.model_occluders)==len(a.model_occluders)
 for b in check.model_occluders:
  xyz=(b.vertices-origin)@basis
  for t in b.indices:
   _,hit=subtract_box(list(xyz[t]),lo+.005,hi-.005)
   assert not hit,(p.name,t)
 report['maps'].append({'file':p.name,'changes':changes,'sha256':hashlib.sha256((out/p.name).read_bytes()).hexdigest()})
assert report['maps'],'No intersecting occlusion found'
(w.parent/'validacao_oclusao.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

