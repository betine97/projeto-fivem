import bpy,bmesh,sys,json,hashlib,addon_utils
from pathlib import Path
import numpy as np
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'CONJUNTO_COMPLETO.blend.revisao2'))
rig=bpy.data.objects['MP_M_FREEMODE_01_RIG'];body=bpy.data.objects['REF_TRONCO_015'];shirt=bpy.data.objects['CAMISA_ESTAMPADA'];pants=bpy.data.objects['CALCA_BEGE'];shoes=bpy.data.objects['MOCASSINS_MARRONS']
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def uvhash(o):
 a=np.empty(len(o.data.uv_layers[0].data)*2,np.float32);o.data.uv_layers[0].data.foreach_get('uv',a);return hashlib.sha256(a.tobytes()).hexdigest()
hashes={o.name:uvhash(o) for o in [shirt,pants,shoes]}
# Taper the sleeves independently of the already-fitted torso.
for v in shirt.data.vertices:
 x,y,z=v.co;s=smooth(.205,.295,abs(x))*(1-smooth(.43,.49,z))
 v.co.y=y+( .054+(y-.054)*.63-y)*s
 v.co.x=x+(1 if x>0 else -1)*.024*s*(1-smooth(.30,.44,z))
body.data.calc_loop_triangles();tris=[tuple(t.vertices) for t in body.data.loop_triangles];points=[v.co.copy() for v in body.data.vertices]
bvh=BVHTree.FromPolygons(points,tris,all_triangles=True)
bodyweights=[{body.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0} for v in body.data.vertices]
for group in list(shirt.vertex_groups):shirt.vertex_groups.remove(group)
def assign(o,index,weights):
 w=sorted([(n,w) for n,w in weights.items() if w>1e-5],key=lambda a:a[1],reverse=True)[:4];total=sum(w for n,w in w)
 assert total>0
 for n,w in w:
  if n not in o.vertex_groups:o.vertex_groups.new(name=n)
  o.vertex_groups[n].add([index],w/total,'REPLACE')
for v in shirt.data.vertices:
 hit,normal,i,dist=bvh.find_nearest(v.co);ia,ib,ic=tris[i];a,b,c=points[ia],points[ib],points[ic]
 ab=b-a;ac=c-a;ap=hit-a;d00=ab.dot(ab);d01=ab.dot(ac);d11=ac.dot(ac);d20=ap.dot(ab);d21=ap.dot(ac);den=d00*d11-d01*d01
 if abs(den)<1e-12:coeff=[1,0,0]
 else:
  bcoef=(d11*d20-d01*d21)/den;ccoef=(d00*d21-d01*d20)/den;coeff=[1-bcoef-ccoef,bcoef,ccoef]
 weights={}
 for idx,t in zip([ia,ib,ic],coeff):
  for n,w in bodyweights[idx].items():weights[n]=weights.get(n,0)+max(0,t)*w
 assign(shirt,v.index,weights)
# Restore all native foot vertices/UVs/weights; keep the ankle joined to its
# original calf. Nothing at the shoe opening is deleted or reconstructed.
for name in ['PELE_PES_MOCASSINS','PELE_TORNOZELOS_MOCASSINS']:
 bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
skin=[]
for name,newname in [('REF_PES_DESCALCOS_APT01','PELE_PES_MOCASSINS'),('REF_PERNAS_BERMUDA_014','PELE_TORNOZELOS_MOCASSINS')]:
 src=bpy.data.objects[name];o=src.copy();o.data=src.data.copy();bpy.context.scene.collection.objects.link(o);o.name=newname;o.hide_render=False;o.hide_set(False);o.hide_select=False
 if 'TORNOZELOS' in newname:
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=(0,0,-.835),plane_no=(0,0,1),clear_outer=True,clear_inner=False);bm.to_mesh(o.data);bm.free()
 skin.append(o)
foot=skin[0];original=bpy.data.objects['REF_PES_DESCALCOS_APT01']
assert len(foot.data.vertices)==len(original.data.vertices) and uvhash(foot)==uvhash(original)
assert all((a.co-b.co).length==0 for a,b in zip(foot.data.vertices,original.data.vertices))
# Give the toe box the space required by the actual native foot.
for v in shoes.data.vertices:
 x,y,z=v.co;center=.16 if x>0 else -.16
 v.co.x=center+(x-center)*1.10
 v.co.y=.035+(y-.035)*1.13
 v.co.z=-1.004+(z+1.002222)*1.045
# The lower trouser fronts were behind the native shin. Move them forward
# smoothly while keeping the slimmer side silhouette from revision 2.
for v in pants.data.vertices:
 x,y,z=v.co;t=1-smooth(-.90,-.72,z)
 v.co.y-=.045*t
for o in [shirt,pants,shoes]:assert uvhash(o)==hashes[o.name];o.data.update()
for filename in [root/'CONJUNTO_COMPLETO.blend',root.parent/'camisa_estampada/PERSONAGEM_COM_CAMISA.blend',root.parent/'calca_bege/PERSONAGEM_COM_CALCA_BEGE.blend']:
 bpy.ops.wm.save_as_mainfile(filepath=str(filename))
report={'revision':3,'native_foot_complete':True,'native_foot_vertices':len(foot.data.vertices),'native_foot_uv_sha256':uvhash(foot),'ankle_upper_cut_z':-.835,'sleeve_weights':'barycentric native upper body surface weights, max 4 influences','clothing_uv_unchanged':hashes}
(root/'work/refined_revision3.json').write_text(json.dumps(report,indent=2));print('REVISION3_BUILD_OK',json.dumps(report),flush=True)
if '--no-render' in sys.argv:sys.exit(0)
def pose(name,axis,angle):
 b=rig.pose.bones[name];q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion(axis,angle)@q
pose('SKEL_L_UpperArm',(0,1,0),.4);pose('SKEL_R_UpperArm',(0,1,0),-.4)
sc=bpy.context.scene;sc.cycles.samples=16;cam=sc.camera
def render(name,loc,target,scale,rx=800,ry=800):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=rx;sc.render.resolution_y=ry;sc.render.filepath=str(root/name);bpy.ops.render.render(write_still=True)
render('mangas_revisao3.png',(3,-4,.33),(0,0,.30),.96)
render('pes_revisao3.png',(2,-3,-.83),(0,-.025,-.91),.46,800,600)
pose('SKEL_L_UpperArm',(0,1,0),-.40);pose('SKEL_L_Forearm',(0,1,0),-.75)
pose('SKEL_R_UpperArm',(1,0,0),-.65);pose('SKEL_R_Forearm',(0,1,0),.6)
render('mangas_movimento_revisao3.png',(3,-4,.33),(0,0,.30),1.15)
