import bpy,math,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'deitado_tiro.blend'))
rig=bpy.data.objects['GTA_Personagem_Rig'];sc=bpy.context.scene
rig.animation_data.action=bpy.data.actions['DEITADO_mira'];sc.frame_set(1);bpy.context.view_layer.update()
base={b.name:b.matrix.copy() for b in rig.pose.bones}
rig.animation_data.action=bpy.data.actions['DEITADO_levantar']
sc.frame_set(1);bpy.context.view_layer.update()
assert max(abs(b.matrix[i][j]-base[b.name][i][j]) for b in rig.pose.bones for i in range(4) for j in range(4))<.0001
heights={}
for f in range(1,92):
 sc.frame_set(f);bpy.context.view_layer.update()
 assert all(math.isfinite(x) for b in rig.pose.bones for row in b.matrix for x in row)
 heights[f]=(rig.matrix_world@rig.pose.bones['SKEL_Pelvis'].head).z
assert heights[1]<heights[49]<heights[91]
assert abs(heights[49]-heights[61])<.0001
assert max(abs(heights[i]-heights[i-1]) for i in range(2,92))<.05
cam=sc.camera;cam.data.ortho_scale=2.8;cam.location=(2.8,-3,1.8)
cam.rotation_euler=(Vector((0,-.08,.6))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.resolution_x=800;sc.render.resolution_y=800;sc.cycles.samples=12
for f in (25,75,91):
 sc.frame_set(f);sc.render.filepath=str(root/f'saida_quadro_{f}.png');bpy.ops.render.render(write_still=True)
(root/'validacao_saida.json').write_text(json.dumps({'frames_checked':91,'source_duration_seconds':3,'game_clip_rate':2,'duration_seconds':1.5,'kneel_hold_frames':[49,61],'start_matches_prone':True,'continuous_pelvis_height':True,'game_tested':False},indent=2))
print('EXIT PASS: 91 finite frames, matching start, kneel hold and continuous height')
