"""Native skinned pocket overlays; original trouser geometry stays intact."""
import copy
import numpy as np

def sample(g, uv):
    v=g.vertex_buffer; ids=g.index_buffer.reshape(-1,3)
    t=v['TexCoord0'][ids]; a=t[:,0]; e=t[:,1]-a; f=t[:,2]-a
    det=e[:,0]*f[:,1]-e[:,1]*f[:,0]; safe=np.abs(det)>1e-9
    q=np.asarray(uv)-a
    b=np.divide(q[:,0]*f[:,1]-q[:,1]*f[:,0],det,out=np.zeros_like(det),where=safe)
    c=np.divide(e[:,0]*q[:,1]-e[:,1]*q[:,0],det,out=np.zeros_like(det),where=safe)
    w=np.column_stack((1-b-c,b,c))
    valid=safe & (w.min(1)>-1e-4)
    if not valid.any(): raise ValueError('Pocket point outside native UV: '+str(uv))
    k=np.flatnonzero(valid)[0]; ws=np.clip(w[k],0,1);ws/=ws.sum()
    tri=v[ids[k]]; out=tri[np.argmax(ws)].copy()
    for key in ('Position','Normal','Tangent','TexCoord1'):
        if key in v.dtype.names: out[key]=(tri[key]*ws[:,None]).sum(0)
    out['Normal']/=max(np.linalg.norm(out['Normal']),1e-8)
    out['TexCoord0']=uv
    weights={}
    for row,factor in zip(tri,ws):
        for bone,weight in zip(row['BlendIndices'],row['BlendWeights']):
            weights[int(bone)]=weights.get(int(bone),0)+float(weight)*factor
    selected=sorted(weights.items(),key=lambda x:x[1],reverse=True)[:4]
    scaled=np.array([x[1] for x in selected]);scaled=np.rint(scaled/scaled.sum()*255).astype(int)
    scaled[0]+=255-scaled.sum()
    out['BlendWeights']=0;out['BlendIndices']=0
    for i,((bone,_),weight) in enumerate(zip(selected,scaled)):
        out['BlendIndices'][i]=bone;out['BlendWeights'][i]=weight
    return out

def add_pockets(drawable):
    anchors=[]
    for lod,models in drawable.models.items():
        if not models:continue
        g=models[0].geometries[0]; steps=8 if lod==0 else 4
        for center in (.255,.745):
            u0,u1=center-.066,center+.066;v0,v1=.158,.315
            points=[];triangles=[]
            for j in range(steps+1):
                for i in range(steps+1):
                    u,v=i/steps,j/steps
                    row=sample(g,(u0+(u1-u0)*u,v0+(v1-v0)*v))
                    # 9 mm raised face with a sewn 1 mm perimeter.
                    lift=.001+.008*np.sin(np.pi*u)**.45*np.sin(np.pi*v)**.45
                    row['Position']+=row['Normal']*lift
                    points.append(row)
            for j in range(steps):
                for i in range(steps):
                    a=j*(steps+1)+i;b=a+1;c=a+steps+1;d=c+1
                    for tri in ((a,b,d),(a,d,c)):
                        p=np.array([points[k]['Position'] for k in tri])
                        n=sum((points[k]['Normal'] for k in tri))
                        if np.dot(np.cross(p[1]-p[0],p[2]-p[0]),n)<0:tri=tri[::-1]
                        triangles.append(tri)
            patch=copy.deepcopy(g);patch.vertex_buffer=np.array(points,dtype=g.vertex_buffer.dtype)
            patch.index_buffer=np.asarray(triangles,dtype=g.index_buffer.dtype).ravel()
            models[0].geometries.append(patch)
            if lod==0:
                anchor=sample(g,(center,.218))
                anchor['Position']+=anchor['Normal']*.013
                anchors.append(anchor['Position'].tolist())
    return anchors
