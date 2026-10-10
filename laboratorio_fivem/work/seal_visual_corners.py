import sys,copy,numpy as np
from pathlib import Path
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.gta5 import *
from szio.gta5.drawables import LodLevel
W=Path(__file__).resolve().parents[1];a=try_load_asset(W.parent/'server-data/resources/cidade_laboratorio/stream/lab_estrutura.ydr')
model=a.models[LodLevel.HIGH][0];ref=model.geometries[0]
faces=[((0,3,2,1),(0,0,-1)),((4,5,6,7),(0,0,1)),((0,1,5,4),(0,-1,0)),((1,2,6,5),(1,0,0)),((2,3,7,6),(0,1,0)),((3,0,4,7),(-1,0,0))]
for x in (-3.98,3.98):
 for y in (-5.98,5.98):
  # Overlap both wall edges so small modelling/quantization gaps cannot show daylight.
  corners=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])*np.array([.14,.14,1.86])+np.array([x,y,1.86])
  g=copy.deepcopy(ref);vb=np.zeros(24,dtype=ref.vertex_buffer.dtype);ind=[]
  for fi,(ids,n) in enumerate(faces):
   for j,vi in enumerate(ids):
    k=fi*4+j;vb['Position'][k]=corners[vi];vb['Normal'][k]=n
    if 'TexCoord0' in vb.dtype.names:vb['TexCoord0'][k]=[(j==1 or j==2)*.025,(j>=2)*.8]
    if 'Tangent' in vb.dtype.names:vb['Tangent'][k]=[1,0,0,1] if abs(n[0])<.5 else [0,1,0,1]
    for field in ('Colour0','Colour1'):
     if field in vb.dtype.names:vb[field][k]=[114,114,114,255]
   b=fi*4;ind.extend([b,b+1,b+2,b,b+2,b+3])
  g.vertex_buffer=vb;g.index_buffer=np.array(ind,dtype=ref.index_buffer.dtype);model.geometries.append(g)
save_asset(a,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),W/'polido','lab_estrutura')
assert try_load_asset(W/'polido/lab_estrutura.ydr') is not None
print('CORNER_TRIMS_OK')
