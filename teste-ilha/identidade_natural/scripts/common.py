from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[3];P=R/'teste-ilha';O=P/'identidade_natural'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
G=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
for name in ['dados','fontes','texturas','stream','previews']:(O/name).mkdir(exist_ok=True)
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,data):Path(path).write_text(json.dumps(data,indent=2,default=lambda v:v.tolist() if isinstance(v,np.ndarray) else v.item()),encoding='utf8')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
grid=np.load(P/'porto_construido/dados/terreno.npz')['terrain']
x,y,z=np.moveaxis(grid,-1,0);dx=float(x[0,1]-x[0,0]);dy=float(y[1,0]-y[0,0])
def sample(field,xx,yy):
    u=np.clip((np.asarray(xx)-x[0,0])/dx,0,grid.shape[1]-1.0001);v=np.clip((np.asarray(yy)-y[0,0])/dy,0,grid.shape[0]-1.0001)
    i=u.astype(int);j=v.astype(int);u=u-i;v=v-j
    a,b,c,d=(np.asarray(q,dtype=float) for q in (field[j,i],field[j,i+1],field[j+1,i],field[j+1,i+1]))
    return np.where(u>=v,a+(b-a)*u+(d-b)*v,a+(d-c)*u+(c-a)*v)
def smooth(a,b,v):t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
def route_distance(xx,yy,points):
    result=np.full(np.broadcast_arrays(xx,yy)[0].shape,np.inf)
    for a,b in zip(points[:-1],points[1:]):
        vx,vy=np.asarray(b[:2])-a[:2];t=np.clip(((xx-a[0])*vx+(yy-a[1])*vy)/(vx*vx+vy*vy),0,1)
        result=np.minimum(result,np.hypot(xx-a[0]-t*vx,yy-a[1]-t*vy))
    return result
