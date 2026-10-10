import sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import try_load_asset
from szio.gta5.bounds import BoundPrimitiveType
w=Path(__file__).resolve().parents[2];lab=w/'laboratorio_fivem'
p=json.loads((lab/'placement.json').read_text());origin=np.array(p['origin']);basis=np.array(p['basis'])
files=[
 lab/'work/base_assets/ch3_08_36.ybn',
 lab/'work/base_assets/patch_hei_ch3_08_36.ybn',
 lab/'work/base_assets/dlc_hei_ch3_08_36.ybn',
 lab/'collision_fix/hei_ch3_08_36.ybn',
 w/'server-data/resources/cidade_laboratorio/stream/ch3_08_36.ybn',
 w/'server-data/resources/cidade_laboratorio/stream/hi@ch3_08_20.ybn',
 w/'server-data/resources/cidade_laboratorio/stream/lab_estrutura.ydr',
 w/'server-data/resources/cidade_laboratorio/stream/lab_porta.ydr',
]
paths=[('entry',-2.695,-8.55,-7.4,1),('vestibule',0,-6.65,-5.35,1),('rear',0,4.65,5.65,1),('side',-3.3,-2.3,-1.2,1)]
def tri_intersection(q,x,z):
 n=np.cross(q[1]-q[0],q[2]-q[0]);
 if abs(n[1])<1e-9:return None
 y=q[0,1]-(n[0]*(x-q[0,0])+n[2]*(z-q[0,2]))/n[1]
 a=q[2]-q[0];b=q[1]-q[0];c=np.array([x,y,z])-q[0]
 aa=a@a;ab=a@b;bb=b@b;ca=c@a;cb=c@b;den=aa*bb-ab*ab
 if abs(den)<1e-9:return None
 u=(bb*ca-ab*cb)/den;v=(aa*cb-ab*ca)/den
 return y if u>=-1e-4 and v>=-1e-4 and u+v<=1+1e-4 else None
for path in files:
 a=try_load_asset(path);hits={n:[] for n,*_ in paths}
 def scan(b):
  for child in getattr(b,'children',[]):scan(child)
  if not hasattr(b,'geometry_primitives'):return
  tx=np.array(b.composite_transform)
  for i,t in enumerate(b.geometry_primitives):
   q=np.array([list(b.geometry_vertices[j].co)+[1] for j in t.vertices])@tx
   q=q[:,:3] if path.suffix=='.ydr' else (q[:,:3]-origin)@basis
   for name,x,ylo,yhi,z in paths:
    if t.primitive_type==BoundPrimitiveType.TRIANGLE:
     y=tri_intersection(q,x,z)
     if y is not None and ylo-.02<=y<=yhi+.02:hits[name].append((i,'triangle',round(float(y),3)))
    elif t.primitive_type==BoundPrimitiveType.BOX:
     lo=q.min(0);hi=q.max(0)
     if lo[0]<=x<=hi[0] and lo[2]<=z<=hi[2] and lo[1]<=yhi and hi[1]>=ylo:hits[name].append((i,'box',round(float(max(lo[1],ylo)),3)))
 scan(a.bounds if hasattr(a,'bounds') else a)
 print(path.parent.name,path.name,{n:sorted(v,key=lambda x:x[2])[:12] for n,v in hits.items() if v},flush=True)
