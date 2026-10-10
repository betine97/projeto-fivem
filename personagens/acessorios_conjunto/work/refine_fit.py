import bpy,bmesh,sys,json,hashlib,addon_utils
from pathlib import Path
import numpy as np
from mathutils import Vector,Quaternion
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'CONJUNTO_COMPLETO.blend.antes-ajuste'))
rig=bpy.data.objects['MP_M_FREEMODE_01_RIG']
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def uvhash(o):
 a=np.empty(len(o.data.uv_layers[0].data)*2,np.float32);o.data.uv_layers[0].data.foreach_get('uv',a);return hashlib.sha256(a.tobytes()).hexdigest()
shirt=bpy.data.objects['CAMISA_ESTAMPADA'];pants=bpy.data.objects['CALCA_BEGE'];hashes={o.name:uvhash(o) for o in [shirt,pants]}
for v in shirt.data.vertices:
 x,y,z=v.co;strength=1-smooth(.43,.55,z)
 sleeve=smooth(.20,.32,abs(x))
 ratio=1-strength*(.32-.10*sleeve)
 v.co.y=.018+(y-.018)*ratio
 v.co.x=x*(1-.025*strength*(1-sleeve))
for v in pants.data.vertices:
 x,y,z=v.co;t=1-smooth(-.94,-.68,z);center=.155 if x>0 else -.155
 v.co.x=center+(x-center)*(1-.30*t)
 v.co.y=.072+(y-.072)*(1-.34*t)
 v.co.z=z+.012*t
for o in [shirt,pants]:assert uvhash(o)==hashes[o.name];o.data.update()
skins=[]
for name,part in [('REF_PES_DESCALCOS_APT01','PELE_PES_MOCASSINS'),('REF_PERNAS_BERMUDA_014','PELE_TORNOZELOS_MOCASSINS')]:
 src=bpy.data.objects[name];o=src.copy();o.data=src.data.copy();bpy.context.scene.collection.objects.link(o);o.name=part;o.hide_render=False;o.hide_set(False);o.hide_select=False
 bm=bmesh.new();bm.from_mesh(o.data)
 if 'TORNOZELOS' in part:
  remove=[v for v in bm.verts if v.co.z>-.81]
 else:
  remove=[v for v in bm.verts if v.co.z<-.963 or v.co.y<-.105]
 bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(o.data);bm.free()
 if 'PES' in part:
  for v in o.data.vertices:
   center=.156 if v.co.x>0 else -.156
   v.co.x=center+(v.co.x-center)*.92
   v.co.y=.03+(v.co.y-.03)*.84
   v.co.z+=.004
 skins.append(o)
feet=bpy.data.objects['REF_PES_DESCALCOS_APT01'];feet.hide_render=True;feet.hide_set(True)
legs=bpy.data.objects['REF_PERNAS_BERMUDA_014'];legs.hide_render=True;legs.hide_set(True)
for o in [shirt,pants]:o['ajuste_revisao']=2
bpy.ops.wm.save_as_mainfile(filepath=str(root/'CONJUNTO_COMPLETO.blend'))
# Keep each established authoring file synchronized with the final fitted outfit.
bpy.ops.wm.save_as_mainfile(filepath=str(root.parent/'camisa_estampada/PERSONAGEM_COM_CAMISA.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(root.parent/'calca_bege/PERSONAGEM_COM_CALCA_BEGE.blend'))
report={'revision':2,'original_uvs_preserved':hashes,'shirt_depth_scale':.68,'hem_width_scale':.70,'hem_depth_scale':.66,'hem_raise_m':.012,'skin_parts':{o.name:len(o.data.polygons) for o in skins}}
(root/'work/refined_fit.json').write_text(json.dumps(report,indent=2));print('REFINED_FIT_OK',json.dumps(report),flush=True)
for side,angle in [('L',.4),('R',-.4)]:
 b=rig.pose.bones['SKEL_'+side+'_UpperArm'];q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion((0,1,0),angle)@q
sc=bpy.context.scene;sc.cycles.samples=16
sc.camera.location=(4,-2,-.09);sc.camera.rotation_euler=(Vector((0,0,-.09))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=str(root/'perfil_corrigido.png');bpy.ops.render.render(write_still=True)
sc.camera.location=(2,-3,-.84);sc.camera.rotation_euler=(Vector((0,0,-.87))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=.46
sc.render.resolution_x=800;sc.render.resolution_y=600;sc.render.filepath=str(root/'barra_pele_corrigida.png');bpy.ops.render.render(write_still=True)
