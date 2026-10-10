import bpy,sys,addon_utils,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
import numpy as np
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root.parent/'calca_bege/PERSONAGEM_COM_CALCA_BEGE.blend'))
rig=bpy.data.objects['MP_M_FREEMODE_01_RIG'];body=bpy.data.objects['REF_TRONCO_015'];sc=bpy.context.scene
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=r'C:\Users\erons\Downloads\Meshy_AI_retro_pattern_shirt_3_1005054809_image-to-3d-texture.glb')
shirt=next(o for o in set(bpy.data.objects)-before if o.type=='MESH');shirt.name='CAMISA_ESTAMPADA'
for c in list(shirt.users_collection):c.objects.unlink(shirt)
bpy.data.collections['03_CRIAR_ROUPAS_AQUI'].objects.link(shirt)
def uvhash(mesh):
 a=np.empty(len(mesh.uv_layers[0].data)*2,dtype=np.float32);mesh.uv_layers[0].data.foreach_get('uv',a);return hashlib.sha256(a.tobytes()).hexdigest()
original_uv=uvhash(shirt.data);original_faces=len(shirt.data.polygons)
for mat in shirt.data.materials:
 for n in mat.node_tree.nodes:
  if n.type=='TEX_IMAGE':n.image.pack()
fit=Matrix.Diagonal((.40,.60,.36,1));fit.translation=Vector((0,-.02,.235));shirt.data.transform(fit);shirt.parent=rig
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
for v in shirt.data.vertices:
 v.co.z+=.02*smooth(.28,.43,v.co.z)
 # Continuous sleeve weights avoid nearest-surface discontinuities at armpits.
 x,y,z=v.co;arm=smooth(.18,.32,abs(x))*smooth(.12,.28,z)
 levels=[('SKEL_Pelvis',-.08),('SKEL_Spine0',0),('SKEL_Spine1',.084),('SKEL_Spine2',.17),('SKEL_Spine3',.283)]
 weights={levels[0][0]:1}
 for (n0,z0),(n1,z1) in zip(levels,levels[1:]):
  if z>=z0:
   t=smooth(z0,z1,z);weights={n0:1-t,n1:t}
 weights={n:w*(1-arm) for n,w in weights.items()}
 weights['SKEL_'+('L' if x>0 else 'R')+'_UpperArm']=arm
 for name,w in weights.items():
  if w>0:
   if name not in shirt.vertex_groups:shirt.vertex_groups.new(name=name)
   shirt.vertex_groups[name].add([v.index],w,'REPLACE')
mod=shirt.modifiers.new('ESQUELETO_ORIGINAL_GTA','ARMATURE');mod.object=rig
assert uvhash(shirt.data)==original_uv and len(shirt.data.polygons)==original_faces
bpy.ops.object.select_all(action='DESELECT');shirt.select_set(True);bpy.context.view_layer.objects.active=shirt
bpy.ops.wm.save_as_mainfile(filepath=str(root/'PERSONAGEM_COM_CAMISA.blend'))
for side,angle in [('L',.4),('R',-.4)]:
 b=rig.pose.bones['SKEL_'+side+'_UpperArm'];q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion((0,1,0),angle)@q
sc.render.filepath=str(root/'preview.png');bpy.ops.render.render(write_still=True)
for side,angle in [('L',-.45),('R',.25)]:
 b=rig.pose.bones['SKEL_'+side+'_UpperArm'];q=b.bone.matrix_local.to_quaternion();b.rotation_quaternion=q.inverted()@Quaternion((0,1,0),angle)@q
b=rig.pose.bones['SKEL_L_Forearm'];q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion((0,0,1),-.7)@q
bpy.context.view_layer.update();evaluated=shirt.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh();bad=0
for e in shirt.data.edges:
 a,b=e.vertices;d0=(shirt.data.vertices[a].co-shirt.data.vertices[b].co).length;d1=(mesh.vertices[a].co-mesh.vertices[b].co).length
 if d1>max(.08,d0*5):bad+=1
evaluated.to_mesh_clear();sc.render.filepath=str(root/'movimento.png');bpy.ops.render.render(write_still=True)
report={'vertices':len(shirt.data.vertices),'triangles':original_faces,'uv_sha256':original_uv,'uv_preserved':True,'weight_source':'continuous original GTA spine/upper-arm weights','extreme_stretched_edges':bad,'fit_scale':[.4,.6,.36],'fit_translation':[0,-.02,.235]}
(root/'work/validation.json').write_text(json.dumps(report,indent=2));print('SHIRT_BUILD_OK',json.dumps(report),flush=True)
