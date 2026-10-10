import bpy,sys
from pathlib import Path
O=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(O/'ilha_porto_esperanca.blend'));s=bpy.context.scene
# GN phase differs per instance and would force thousands of evaluated crowns in Cycles.
# Static previews share each rest mesh; native game wind remains encoded in the exported drawables.
for o in bpy.data.objects:
    for m in o.modifiers:
        if m.type=='NODES':m.show_render=False
    if o.name.startswith('COL_'):o.hide_render=True
s.cycles.samples=16;s.cycles.use_denoising=True
try:
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
    for d in p.devices:d.use=d.type=='OPTIX'
    s.cycles.device='GPU'
except:pass
for name,file in [('Porto construido | panorama','porto_construido.png'),('Ilha completa','ilha_completa.png')]:
    s.camera=bpy.data.objects[name];s.render.filepath=str(O/'previews'/file);bpy.ops.render.render(write_still=True);print('PREVIEW_READY',file,flush=True)
