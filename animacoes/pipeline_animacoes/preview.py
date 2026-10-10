"""Render the copied runtime studies, without changing saved sources."""
import bpy
from pathlib import Path
HERE=Path(__file__).resolve().parent
for posture in ('ajoelhado','deitado','sentado'):
    bpy.ops.wm.open_mainfile(filepath=str(HERE/'sources'/f'{posture}_ak.blend'))
    rig=bpy.data.objects['GTA_Personagem_Rig']
    for label,action,frame in [('mira','MIRA',1),('recarga','RECARGA',40)]:
        rig.animation_data.action=bpy.data.actions[f'{action}_{posture}_ak']
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
        bpy.context.scene.render.filepath=str(HERE/'previews'/f'{posture}_{label}.png')
        bpy.ops.render.render(write_still=True)
print('PREVIEWS_OK')
