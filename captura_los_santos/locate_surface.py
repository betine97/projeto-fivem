"""Identify the actual HD map geometry touching a saved mouse hit."""
from pathlib import Path
import json,sqlite3,sys,subprocess,os
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
def candidates(point,origin):
    db=sqlite3.connect(ROOT/'captura_los_santos/data/world_index.sqlite3');db.row_factory=sqlite3.Row
    p=np.array([point[k] for k in ('x','y','z')],dtype=float)
    if origin=='Cayo Perico':p-=np.array([-1300,5200,0])
    rows=db.execute('SELECT e.* FROM bounds b JOIN entities e ON e.id=b.id WHERE b.minX<=? AND b.maxX>=? AND b.minY<=? AND b.maxY>=? AND b.minZ<=? AND b.maxZ>=? LIMIT 120',(p[0]+.5,p[0]-.5,p[1]+.5,p[1]-.5,p[2]+.5,p[2]-.5)).fetchall();db.close()
    return p,rows
def distances(p,tri):
    a,b,c=tri[:,0],tri[:,1],tri[:,2];ab=b-a;ac=c-a;ap=p-a
    n=np.cross(ab,ac);nn=np.sum(n*n,axis=1);valid=nn>1e-12
    projection=p-n*(np.sum(ap*n,axis=1)/np.maximum(nn,1e-12))[:,None]
    v=projection-a;aa=np.sum(ab*ab,axis=1);bb=np.sum(ab*ac,axis=1);cc=np.sum(ac*ac,axis=1);den=aa*cc-bb*bb
    u=(cc*np.sum(v*ab,axis=1)-bb*np.sum(v*ac,axis=1))/np.maximum(den,1e-12)
    t=(aa*np.sum(v*ac,axis=1)-bb*np.sum(v*ab,axis=1))/np.maximum(den,1e-12)
    d=np.where(valid&(u>=0)&(t>=0)&(u+t<=1),np.linalg.norm(p-projection,axis=1),np.inf)
    for start,end in ((a,b),(b,c),(c,a)):
        edge=end-start;factor=np.clip(np.sum((p-start)*edge,axis=1)/np.maximum(np.sum(edge*edge,axis=1),1e-12),0,1)
        d=np.minimum(d,np.linalg.norm(p-(start+edge*factor[:,None]),axis=1))
    return float(d.min())
def locate(body):
    index=json.loads((ROOT/'captura_los_santos/data/model_index.json').read_text(encoding='utf8'))
    p,rows=candidates(body['position'],body.get('origin','Los Santos'));results=[]
    for row in rows:
        meta=index['models'].get(str(row['hash']))
        if not meta or not meta.get('file') or meta.get('mlo'):continue
        # Large terrain, occlusion and LOD groups are never substituted for a prop.
        if max(b-a for a,b in zip(meta['bbMin'],meta['bbMax']))>180:continue
        folder=ROOT/'captura_los_santos/cache'/meta['model'];folder.mkdir(parents=True,exist_ok=True)
        if not (folder/'geometry.npz').exists():
            (folder/'source.json').write_text(json.dumps(meta),encoding='utf8')
            with (folder/'extraction.log').open('wb')as log:
                proc=subprocess.run([sys.executable,str(ROOT/'captura_los_santos/assets.py'),str(folder)],stdout=log,stderr=subprocess.STDOUT,timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if proc.returncode:continue
        if not (folder/'geometry.npz').exists():continue
        arrays=np.load(folder/'geometry.npz');tri=[]
        for i in range(len(arrays.files)//2):
            vertices=arrays['v'+str(i)]['Position'].astype(float)
            tri.append(vertices[arrays['i'+str(i)].reshape(-1,3)])
        if not tri:continue
        tri=np.concatenate(tri);w,x,y,z=json.loads(row['rotation'])
        rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
        local=tri*np.array([row['sxy'],row['sxy'],row['sz']]);pos=np.array(json.loads(row['pos']))
        distance=min(distances(p,(local@rot.T)+pos),distances(p,(local@rot)+pos))
        results.append({'hash':row['hash'],'model':meta['model'],'distance':distance,'position':json.loads(row['pos']),'map':row['map']})
    results.sort(key=lambda r:r['distance'])
    # Match actual triangles, not merely another object's overlapping bounds.
    good=[r for r in results if r['distance']<=.35]
    return {'found':bool(good),'best':good[0] if good else None,'candidates':results[:5]}
if __name__=='__main__':
    path=Path(sys.argv[1]);result=locate(json.loads(path.read_text(encoding='utf8')))
    path.with_suffix('.resolved.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf8')
