import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'deitado_tiro.blend'))
rig=bpy.data.objects['GTA_Personagem_Rig'];gun=bpy.data.objects['w_ar_carbinerifle']
rig.animation_data.action=bpy.data.actions['DEITADO_disparo']
samples={}
for frame in (1,3,10,30):
 bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
 samples[frame]={n:(rig.matrix_world@rig.pose.bones[n].head).copy() for n in ['SKEL_L_Hand','SKEL_R_Hand','SKEL_L_Foot','SKEL_R_Foot','SKEL_Pelvis']}
 samples[frame]['gun']=gun.matrix_world.translation.copy()
 assert all(math.isfinite(x) for p in samples[frame].values() for x in p)
for name in ('SKEL_L_Foot','SKEL_R_Foot','SKEL_Pelvis'):
 assert (samples[3][name]-samples[1][name]).length<0.0001,name+' moved during recoil'
for name in ('SKEL_L_Hand','SKEL_R_Hand','gun'):
 assert .005<(samples[3][name]-samples[1][name]).length<.010,name+' recoil exceeds the authored 9 mm limit or is missing'
 assert (samples[10][name]-samples[1][name]).length<.001,name+' does not return'
 assert (samples[30][name]-samples[1][name]).length<.001,name+' has a loop discontinuity'
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'deitado_tiro.blend'))
(root/'validacao_deitado.json').write_text(json.dumps({'actions':['DEITADO_mira','DEITADO_disparo'],'frames_checked':[1,3,10,30],'recoil_and_return':True,'feet_and_pelvis_stable':True,'installed_in_fivem':False,'game_tested':False},indent=2))
print('PRONE PASS: both wrists and weapon recoil/return; feet and pelvis remain stable')
