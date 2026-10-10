import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
import numpy as np
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'CONJUNTO_COMPLETO.blend'))
rig=bpy.data.objects['MP_M_FREEMODE_01_RIG']
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
# Intersect original skin triangles with parallel planes. These contours
# let clothing grow around the actual limb without shrinking the limb.
def contours(objects,axis,levels):
 tris=[]
 for obj in objects:
  obj.data.calc_loop_triangles()
  for t in obj.data.loop_triangles:
   vs=np.array([obj.data.vertices[i].co[:] for i in t.vertices])
   if vs[:,0].mean()>0:tris.append(vs)
 tris=np.array(tris);axes=[i for i in range(3) if i!=axis];result=[]
 for level in levels:
  selected=tris[(tris[:,:,axis].min(1)<=level)&(tris[:,:,axis].max(1)>=level)];segments=[]
  for tri in selected:
   hits=[]
   for a,b in zip(tri,np.roll(tri,-1,axis=0)):
    if (a[axis]<=level<b[axis]) or (b[axis]<=level<a[axis]):hits.append((a+(b-a)*(level-a[axis])/(b[axis]-a[axis]))[axes])
   if len(hits)==2:segments.append(hits)
  if segments:
   segments=np.array(segments);center=(segments.reshape(-1,2).min(0)+segments.reshape(-1,2).max(0))/2;result.append((level,segments,center))
 return result,axes
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def fit(obj,axis,levels,objects,clearance,mask):
 sections,axes=contours(objects,axis,levels);values=np.array([s[0] for s in sections]);angles=120
 if axis==1:
  for _,_,center in sections:center[1]=-1.014
 # Use one smooth radial scale for both sides of the leather shell. Clamping
 # individual layers to one surface would make those layers overlap.
 a=np.array([v.co[:] for v in obj.data.vertices]);sign=np.sign(a[:,0]);a[:,0]=abs(a[:,0])
 indices=np.abs(a[:,axis,None]-values[None,:]).argmin(1)
 centers=np.array([s[2] for s in sections]);delta=a[:,axes]-centers[indices];radius=np.linalg.norm(delta,axis=1)
 theta=(np.arctan2(delta[:,1],delta[:,0])+2*np.pi)%(2*np.pi)
 angular=(theta*angles/(2*np.pi)).astype(int)%angles
 outer=np.zeros((len(sections),angles));np.maximum.at(outer,(indices,angular),radius)
 for row in outer:
  valid=np.flatnonzero(row>.005)
  if len(valid):row[:]=np.interp(np.arange(angles),np.concatenate([valid-angles,valid,valid+angles]),np.tile(row[valid],3))
 validrows=np.flatnonzero(outer.max(1)>.005)
 for j in range(angles):outer[:,j]=np.interp(np.arange(len(sections)),validrows,outer[validrows,j])
 for k in range(4):outer=np.maximum(outer,np.maximum(np.roll(outer,1,axis=1),np.roll(outer,-1,axis=1)))
 skin=np.zeros_like(outer)
 for idx,(_,segments,center) in enumerate(sections):
  for j in range(angles):
   direction=np.array([math.cos(j*2*math.pi/angles),math.sin(j*2*math.pi/angles)])
   for p,q in segments:
    e=q-p;den=cross(direction,e)
    if abs(den)<1e-10:continue
    d=p-center;t=cross(d,e)/den;u=cross(d,direction)/den
    if t>=0 and -.00001<=u<=1.00001:skin[idx,j]=max(skin[idx,j],t)
 skin=np.maximum(skin,np.maximum(np.roll(skin,1,axis=1),np.roll(skin,-1,axis=1)))
 factors=np.clip((skin+clearance)/np.maximum(outer,.005),1,1.65)
 factors=np.maximum(factors,np.maximum(np.roll(factors,1,axis=1),np.roll(factors,-1,axis=1)))
 factors=(np.roll(factors,1,axis=1)+2*factors+np.roll(factors,-1,axis=1))/4
 factors=np.maximum(factors,np.maximum(np.concatenate([factors[:1],factors[:-1]]),np.concatenate([factors[1:],factors[-1:]])))
 changed=0
 for v in obj.data.vertices:
  if not mask(v.co):continue
  idx=v.index;scale=factors[indices[idx],angular[idx]]
  if scale<=1:continue
  p=centers[indices[idx]]+delta[idx]*scale
  for ax,value in zip(axes,p):v.co[ax]=sign[idx]*value if ax==0 else value
  changed+=1
 obj.data.update();return changed
feet=bpy.data.objects['PELE_PES_MOCASSINS'];ankles=bpy.data.objects['PELE_TORNOZELOS_MOCASSINS']
shoes=bpy.data.objects['MOCASSINS_MARRONS'];pants=bpy.data.objects['CALCA_BEGE']
counts={}
counts['shoe_vertices_grown']=fit(shoes,1,np.linspace(-.21,.12,145),[feet],.010,lambda p:True)
counts['trouser_vertices_grown']=fit(pants,2,np.linspace(-.951,-.76,100),[ankles],.014,lambda p:p.z<-.765)
# Transfer lower-trouser weights from the native calf/ankle to keep the
# preserved skin covered when knees and feet bend.
from mathutils.bvhtree import BVHTree
legs=bpy.data.objects['REF_PERNAS_BERMUDA_014'];legs.data.calc_loop_triangles();tri=[tuple(t.vertices) for t in legs.data.loop_triangles];pts=[v.co.copy() for v in legs.data.vertices];bvh=BVHTree.FromPolygons(pts,tri,all_triangles=True)
for v in pants.data.vertices:
 t=1-smooth(-.89,-.74,v.co.z)
 if not t:continue
 p,n,idx,dist=bvh.find_nearest(v.co);indices=tri[idx];a,b,c=[pts[i] for i in indices];ab=b-a;ac=c-a;ap=p-a
 d00=ab.dot(ab);d01=ab.dot(ac);d11=ac.dot(ac);d20=ap.dot(ab);d21=ap.dot(ac);den=d00*d11-d01*d01
 u=(d11*d20-d01*d21)/den if abs(den)>1e-12 else 0;w=(d00*d21-d01*d20)/den if abs(den)>1e-12 else 0
 weights={pants.vertex_groups[g.group].name:g.weight*(1-t) for g in v.groups}
 for i,f in zip(indices,[1-u-w,u,w]):
  for g in legs.data.vertices[i].groups:
   name=legs.vertex_groups[g.group].name;weights[name]=weights.get(name,0)+t*max(0,f)*g.weight
 for g in list(v.groups):pants.vertex_groups[g.group].remove([v.index])
 top=sorted([(n,w) for n,w in weights.items() if w>1e-5],key=lambda a:a[1],reverse=True)[:4];total=sum(w for n,w in top)
 for n,w in top:
  if n not in pants.vertex_groups:pants.vertex_groups.new(name=n)
  pants.vertex_groups[n].add([v.index],w/total,'REPLACE')
for filename in [root/'CONJUNTO_COMPLETO.blend',root.parent/'camisa_estampada/PERSONAGEM_COM_CAMISA.blend',root.parent/'calca_bege/PERSONAGEM_COM_CALCA_BEGE.blend']:
 bpy.ops.wm.save_as_mainfile(filepath=str(filename))
(root/'work/skin_envelope_revision3.json').write_text(json.dumps(counts,indent=2));print('NATIVE_SKIN_ENCLOSED',counts,flush=True)
for side,angle in [('L',.4),('R',-.4)]:
 b=rig.pose.bones['SKEL_'+side+'_UpperArm'];q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion((0,1,0),angle)@q
sc=bpy.context.scene;sc.cycles.samples=16;cam=sc.camera
cam.location=(2,-3,-.83);cam.rotation_euler=(Vector((0,-.025,-.91))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.46
sc.render.resolution_x=800;sc.render.resolution_y=600;sc.render.filepath=str(root/'pes_revisao3.png');bpy.ops.render.render(write_still=True)
