import bpy,bmesh,sys,json,addon_utils
from pathlib import Path
from mathutils import Vector,Quaternion
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'CONJUNTO_COMPLETO.blend'))
o=bpy.data.objects['PELE_TORNOZELOS_MOCASSINS'];bm=bmesh.new();bm.from_mesh(o.data)
# Only skin below the trouser hem can appear. The rest of the calf is covered.
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,0,-.942),plane_no=(0,0,1),clear_outer=True,clear_inner=False)
bm.to_mesh(o.data);bm.free();print('SKIN_CROP',len(o.data.vertices),len(o.data.polygons),flush=True)
o=bpy.data.objects['PELE_PES_MOCASSINS'];bm=bmesh.new();bm.from_mesh(o.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,0,-.942),plane_no=(0,0,1),clear_outer=True,clear_inner=False)
bm.to_mesh(o.data);bm.free()
for filename in [root/'CONJUNTO_COMPLETO.blend',root.parent/'camisa_estampada/PERSONAGEM_COM_CAMISA.blend',root.parent/'calca_bege/PERSONAGEM_COM_CALCA_BEGE.blend']:
 bpy.ops.wm.save_as_mainfile(filepath=str(filename))
rig=bpy.data.objects['MP_M_FREEMODE_01_RIG']
for side,angle in [('L',.4),('R',-.4)]:
 b=rig.pose.bones['SKEL_'+side+'_UpperArm'];q=b.bone.matrix_local.to_quaternion();b.rotation_mode='QUATERNION';b.rotation_quaternion=q.inverted()@Quaternion((0,1,0),angle)@q
sc=bpy.context.scene;sc.cycles.samples=16
sc.camera.location=(2,-3,-.84);sc.camera.rotation_euler=(Vector((0,0,-.87))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=.46
sc.render.resolution_x=800;sc.render.resolution_y=600;sc.render.filepath=str(root/'barra_pele_corrigida.png');bpy.ops.render.render(write_still=True)
