import sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];W=P.parent;N=P/'native';N.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
from szio.gta5 import *
import numpy as np
G=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
index=(R/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines();cache={}
for source in index:
    name=source.split('|')[-1]
    if name!='ch2_roads_rd_26.ydr':continue
    parts=source.split('|');a=open_rpf(G/parts[0])
    for sub in parts[1:-1]:a=a.open_nested(sub)
    (N/name).write_bytes(a.read_bytes(name));print('EXTRACTED',name)
origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin'])
e=next(e for e in json.loads((W/'work/entities.json').read_text()) if e['name']=='ch2_roads_rd_26');off=np.array(e['pos'])-origin
a=try_load_asset(N/'ch2_roads_rd_26.ydr');ts=np.concatenate([g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)]+off for m in a.models[LodLevel.HIGH] for g in m.geometries]);v=ts[:,0];u=ts[:,1]-v;t=ts[:,2]-v;den=u[:,0]*t[:,1]-u[:,1]*t[:,0];safe=abs(den)>1e-6
data=[]
for y in [17.8,18.5,19,19.5,20,21]:
    line=[]
    for x in [3.8,4.5,5.4,6.2,8,10,12.5,13]:
        b=((x-v[:,0])*t[:,1]-(y-v[:,1])*t[:,0])/np.where(safe,den,1);c=(u[:,0]*(y-v[:,1])-u[:,1]*(x-v[:,0]))/np.where(safe,den,1);z=v[:,2]+b*u[:,2]+c*t[:,2];keep=safe&(b>=-1e-4)&(c>=-1e-4)&(b+c<=1.0001)
        line.append([x,sorted(set(np.round(z[keep],4).tolist()))])
    data.append({'y':y,'x_z':line});print(data[-1])
(P/'road_samples.json').write_text(json.dumps({'entity':e,'samples':data},indent=2))
