"""Clean single-layer clear PVC strip curtains fitted to the Meshy frame."""
from pathlib import Path
import numpy as np

root=Path(__file__).resolve().parents[2]
out=root/'laboratorio_fivem/containment_source/containment_strips.npz'
positions=[];normals=[];uvs=[]

def triangle(points,texcoords):
    a,b,c=[np.asarray(p,dtype=np.float32) for p in points]
    normal=np.cross(b-a,c-a)
    normal/=max(float(np.linalg.norm(normal)),1e-8)
    for order in ((0,1,2),(2,1,0)):
        for index in order:
            positions.append(points[index])
            normals.append(normal if order==(0,1,2) else -normal)
            uvs.append(texcoords[index])

def grid(surface,u_count,v_count):
    for j in range(v_count):
        for i in range(u_count):
            u0,u1=i/u_count,(i+1)/u_count
            v0,v1=j/v_count,(j+1)/v_count
            p00,p10,p11,p01=(surface(u0,v0),surface(u1,v0),
                             surface(u1,v1),surface(u0,v1))
            triangle((p00,p10,p11),((u0,v0),(u1,v0),(u1,v1)))
            triangle((p00,p11,p01),((u0,v0),(u1,v1),(u0,v1)))

for side in (-1,1):
    for index in range(20):
        center=-3.70+(index+.5)*7.40/20
        def surface(u,v,side=side,center=center,index=index):
            y=center+(u-.5)*.395
            z=.27+v*2.57
            x=side*(1.07+.012*np.sin(np.pi*v*2+index*.7)+
                    .009*np.sin(np.pi*u*2)*np.sin(np.pi*v))
            return (x,y,z)
        grid(surface,3,10)

for index in range(6):
    center=-1.08+(index+.5)*2.16/6
    def front(u,v,center=center,index=index):
        x=center+(u-.5)*.385
        z=.27+v*2.57
        y=-3.70-.014*np.sin(np.pi*v*2+index*.8)
        return (x,y,z)
    grid(front,3,10)

# A nearly invisible clear canopy retains the original top coverage.
def roof(u,v):
    x=-1.075+2.15*u
    y=-3.70+7.40*v
    z=2.92-.025*np.sin(np.pi*u)*np.sin(np.pi*v)
    return (x,y,z)
grid(roof,8,20)

pos=np.asarray(positions,dtype=np.float32)
norm=np.asarray(normals,dtype=np.float32)
uv=np.asarray(uvs,dtype=np.float32)
np.savez_compressed(out,position=pos,normal=norm,uv=uv)
assert len(pos)%3==0
print('STRIPS_OK',len(pos)//3,'triangles','bounds',pos.min(0),pos.max(0),flush=True)
