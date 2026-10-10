import sys,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;N=W/'work/native';D=R/'server-data/resources/cidade_mansao/stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
origin=np.array(json.loads((W/'medidas_estudo.json').read_text())['native_origin'])
rows=json.loads((W/'work/near_house_entities.json').read_text());out={'origin':origin.tolist(),'entities':[],'geometry':[],'collision':[]}
for e in rows:
    f=D/(e['name']+'.ydr');f=f if f.exists() else N/f.name
    if not f.exists() or 'lod' in e['name']:continue
    a=try_load_asset(f)
    if a is None:continue
    off=np.array(e['pos'])-origin
    for m in a.models.get(LodLevel.HIGH,[]):
        for g in m.geometries:
            v=g.vertex_buffer['Position']+off;lo=v.min(0);hi=v.max(0)
            if hi[0]<-12 or lo[0]>16 or hi[1]<5 or lo[1]>28:continue
            tex=next((p.value for p in a.shader_group.shaders[g.shader_index].parameters if p.name.lower()=='diffusesampler'),'')
            out['geometry'].append({'file':f.name,'offset':off.tolist(),'material':str(tex),'lo':lo.tolist(),'hi':hi.tolist(),'tris':len(g.index_buffer)//3})
    out['entities'].append({'name':e['name'],'map':e['map'],'offset':off.tolist(),'rot':e['rot']})
triangles=[]
for original in sorted(N.glob('*ch2_09b_[0-3].ybn')):
    f=D/original.name;f=f if f.exists() else original
    a=try_load_asset(f);count=[0];verts_in=[]
    def visit(b,parent=np.eye(4)):
        tx=np.asarray(b.composite_transform)@parent
        for c in getattr(b,'children',[]):visit(c,tx)
        if not hasattr(b,'geometry_primitives'):return
        vs=np.array([v.co for v in b.geometry_vertices]);v=(np.c_[vs,np.ones(len(vs))]@tx)[:,:3]-origin
        for t in b.geometry_primitives:
            if t.primitive_type!=BoundPrimitiveType.TRIANGLE:continue
            q=v[list(t.vertices)];lo=q.min(0);hi=q.max(0)
            if hi[0]<-12 or lo[0]>16 or hi[1]<5 or lo[1]>30 or lo[2]>1 or hi[2]<-10:continue
            count[0]+=1;verts_in.extend(q)
            if original.name in ['ch2_09b_'+str(i)+'.ybn' for i in range(4)]:triangles.append(q)
    visit(a)
    if count[0]:out['collision'].append({'file':original.name,'triangles':count[0],'lo':np.min(verts_in,0).tolist(),'hi':np.max(verts_in,0).tolist()})
ts=np.array(triangles);heights=[]
for y in [7,9,11,13,15,17,19,21,23,25,27]:
    line=[]
    for x in [-8,-5,-2,1,4,7,10,13]:
        a=ts[:,0];u=ts[:,1]-a;v=ts[:,2]-a;den=u[:,0]*v[:,1]-u[:,1]*v[:,0];safe=abs(den)>1e-6
        s=((x-a[:,0])*v[:,1]-(y-a[:,1])*v[:,0])/np.where(safe,den,1)
        t=(u[:,0]*(y-a[:,1])-u[:,1]*(x-a[:,0]))/np.where(safe,den,1)
        zs=a[:,2]+s*u[:,2]+t*v[:,2];keep=safe&(s>=-1e-4)&(t>=-1e-4)&(s+t<=1.0001)
        line.append([x,sorted(set(np.round(zs[keep],3).tolist()),reverse=True)])
    heights.append({'y':y,'x_z':line})
out['terrain_samples']=heights
(P/'site_measurements.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
for g in out['geometry']:print('GEOMETRY',g)
for h in heights:print('GROUND',h)
print('SITE_MEASURED',len(out['entities']),len(ts),flush=True)
