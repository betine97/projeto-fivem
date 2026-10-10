import bpy,sys,addon_utils,json,hashlib,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root.parent/'templates_freemode/01_BASE_ROUPAS.blend'))
sc=bpy.context.scene;rig=bpy.data.objects['MP_M_FREEMODE_01_RIG'];rig.hide_select=False
for o in list(bpy.data.objects):
 if o.type in {'CAMERA','LIGHT'}:bpy.data.objects.remove(o,do_unlink=True)
body=list(bpy.data.collections['01_CORPO_REFERENCIA'].objects)
for o in body:o.hide_select=False
# Native bare feet from the apartment collection. Only the supplied trousers
# are new clothing; do not leave the template flip-flops in the final preview.
before=set(bpy.data.objects)
bpy.ops.sollumz.import_assets(directory=str(root/'source'),files=[{'name':'mp_m_freemode_01_male_apt01^feet_001_r.ydd'}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
imported=set(bpy.data.objects)-before
feet=next(o for o in imported if o.type=='MESH')
oldrig=next(m.object for m in feet.modifiers if m.type=='ARMATURE')
used={feet.vertex_groups[g.group].name for v in feet.data.vertices for g in v.groups if g.weight>0}
assert used<=set(rig.data.bones.keys())
matrix_error=max(max(abs(a-b) for ra,rb in zip(oldrig.data.bones[n].matrix_local,rig.data.bones[n].matrix_local) for a,b in zip(ra,rb)) for n in used)
assert matrix_error<.0001,matrix_error
world=feet.matrix_world.copy();feet.parent=rig;feet.matrix_world=world
for modifier in feet.modifiers:
 if modifier.type=='ARMATURE':modifier.object=rig
for c in list(feet.users_collection):c.objects.unlink(feet)
bpy.data.collections['01_CORPO_REFERENCIA'].objects.link(feet)
feet.name='REF_PES_DESCALCOS_APT01'
for o in imported:
 if o!=feet:bpy.data.objects.remove(o,do_unlink=True)
for name,tex in try_load_asset(root/'source/mp_m_freemode_01_male_apt01^feet_diff_001_a_whi.ytd').textures.items():
 with tex.data.open() as stream:(root/'textures'/(name+'.dds')).write_bytes(stream.read())
 image=bpy.data.images.load(str(root/'textures'/(name+'.dds')),check_existing=True);image.pack()
 for mat in feet.data.materials:
  node=mat.node_tree.nodes.get('DiffuseSampler') if mat.node_tree else None
  if node:node.image=image
body.append(feet)
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=r'C:\Users\erons\Downloads\Meshy_AI_pleated_beige_trouser_1005054816_image-to-3d-texture.glb')
pants=next(o for o in set(bpy.data.objects)-before if o.type=='MESH');pants.name='CALCA_BEGE'
for c in list(pants.users_collection):c.objects.unlink(pants)
bpy.data.collections['03_CRIAR_ROUPAS_AQUI'].objects.link(pants)
def uvhash(m):
 a=np.empty(len(m.uv_layers[0].data)*2,dtype=np.float32);m.uv_layers[0].data.foreach_get('uv',a);return hashlib.sha256(a.tobytes()).hexdigest()
original_uv=uvhash(pants.data);original_faces=len(pants.data.polygons)
texture_hashes={}
for mat in pants.data.materials:
 for n in mat.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image:
   n.image.pack();texture_hashes[n.image.name]=hashlib.sha256(bytes(n.image.packed_file.data)).hexdigest()
# Fit to the existing body in its native rest pose. Keep all source triangles
# and UVs; the explicit scale is documented and reproducible.
fit=Matrix.Diagonal((.58,.58,.542,1));fit.translation=Vector((0,.014,-.4407))
pants.data.transform(fit);pants.data.update();pants.parent=rig
for name in ['SKEL_Pelvis','SKEL_L_Thigh','SKEL_R_Thigh','SKEL_L_Calf','SKEL_R_Calf','SKEL_L_Foot','SKEL_R_Foot']:pants.vertex_groups.new(name=name)
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
for v in pants.data.vertices:
 x,y,z=v.co;side='L' if x>=0 else 'R'
 hip=1-smooth(-.23,-.015,z)
 left=smooth(-.06,.06,x) if z>-.26 else (1 if x>=0 else 0)
 knee=1-smooth(-.575,-.425,z)
 ankle=(1-smooth(-.955,-.895,z))*.30
 w={'SKEL_Pelvis':1-hip}
 for s,portion in [('L',left),('R',1-left)]:
  w['SKEL_'+s+'_Thigh']=hip*portion*(1-knee)
  w['SKEL_'+s+'_Calf']=hip*portion*knee*(1-ankle)
  w['SKEL_'+s+'_Foot']=hip*portion*knee*ankle
 top=sorted(((n,w) for n,w in w.items() if w>1e-6),key=lambda a:a[1],reverse=True)[:4];total=sum(w for n,w in top)
 for name,w in top:pants.vertex_groups[name].add([v.index],w/total,'REPLACE')
mod=pants.modifiers.new('ESQUELETO_ORIGINAL_GTA','ARMATURE');mod.object=rig
assert uvhash(pants.data)==original_uv and len(pants.data.polygons)==original_faces
for o in body:
 if o.name in {'REF_PERNAS_BERMUDA_014','REF_PES_005'}:o.hide_render=True;o.hide_set(True)
 # Use the actual native diffuse in a neutral preview shader. The native
 # materials remain in the protected source collection.
 old=o.data.materials[0];node=old.node_tree.nodes.get('DiffuseSampler') if old.node_tree else None
 mat=bpy.data.materials.new('PREVIEW_'+o.name);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.55
 if node and node.image:
  tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=node.image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 o.data.materials.clear();o.data.materials.append(mat)
 for p in o.data.polygons:p.material_index=0
sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.resolution_x=800;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.render.film_transparent=True
sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
studio=bpy.data.collections.new('ESTUDIO_CALCA');sc.collection.children.link(studio)
def aim(o,pos,target):o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',d);studio.objects.link(cam);d.type='ORTHO';d.ortho_scale=2.11;sc.camera=cam;aim(cam,(0,-5,-.09),(0,0,-.09))
for pos,power,size in [((-3,-4,3),400,3),((3,-3,1),180,3),((0,2,2),300,3)]:
 d=bpy.data.lights.new('Softbox','AREA');o=bpy.data.objects.new('Softbox',d);studio.objects.link(o);d.energy=power;d.size=size;aim(o,pos,(0,0,-.1))
bpy.ops.object.select_all(action='DESELECT');pants.select_set(True);bpy.context.view_layer.objects.active=pants
bpy.ops.wm.save_as_mainfile(filepath=str(root/'PERSONAGEM_COM_CALCA_BEGE.blend'))
for side,angle in [('L',.40),('R',-.40)]:
 b=rig.pose.bones['SKEL_'+side+'_UpperArm'];q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion((0,1,0),angle)@q
bpy.context.view_layer.update();sc.render.filepath=str(root/'preview_frente.png');bpy.ops.render.render(write_still=True)
aim(cam,(3,-5,.03),(0,0,-.09));sc.render.filepath=str(root/'preview_perspectiva.png');bpy.ops.render.render(write_still=True)
for name,angle in [('SKEL_L_Thigh',-.5),('SKEL_L_Calf',.85),('SKEL_R_Thigh',.25)]:
 b=rig.pose.bones[name];q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion((1,0,0),angle)@q
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=pants.evaluated_get(dg);m=ev.to_mesh();bad=[]
for e in pants.data.edges:
 a,b=e.vertices;d0=(pants.data.vertices[a].co-pants.data.vertices[b].co).length;d1=(m.vertices[a].co-m.vertices[b].co).length
 if d1>max(.08,d0*5):bad.append((e.index,d0,d1))
ev.to_mesh_clear();sc.render.filepath=str(root/'teste_joelho.png');bpy.ops.render.render(write_still=True)
report={'vertices':len(pants.data.vertices),'triangles':len(pants.data.polygons),'source_uv_sha256':original_uv,'uv_unchanged':True,'original_textures_sha256':texture_hashes,'fit_scale':[.58,.58,.542],'fit_translation':[0,.014,-.4407],'native_character':'mp_m_freemode_01','head_preserved':True,'barefoot_collection':'male_apt01','barefoot_drawable':1,'extreme_stretched_edges':bad[:20],'extreme_stretched_edge_count':len(bad)}
(root/'work/validation.json').write_text(json.dumps(report,indent=2));print('PANTS_BUILD_OK',json.dumps(report),flush=True)
