import bpy,json
from pathlib import Path
O=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(O/'ilha_porto_esperanca.blend'));s=bpy.context.scene
im=bpy.data.images.load(str(O/'fontes/pe_solo_rocha.png'),check_existing=True);im.pack()
for m in bpy.data.materials:
    if m.name.startswith('Solo nativo cs_islx_canyonrock_rough_01'):
        next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE').image=im
rows=json.loads((O/'dados/setores_alterados.json').read_text())
for row in rows:row['materials'][2]=dict(texture='pe_solo_rocha',file=str(O/'fontes/pe_solo_rocha.png'))
(O/'dados/setores_alterados.json').write_text(json.dumps(rows,indent=2))
# Save the editable project at the panorama camera before rendering a closer view.
s.camera=bpy.data.objects['Porto construido | panorama'];bpy.ops.wm.save_as_mainfile(filepath=str(O/'ilha_porto_esperanca.blend'),compress=True)
s.cycles.samples=16;s.cycles.use_denoising=True
try:
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
    for d in p.devices:d.use=d.type=='OPTIX'
    s.cycles.device='GPU'
except:pass
for name,file in [('Porto construido | panorama','porto_construido.png'),('Porto construido | bairro','bairro_texturizado.png')]:
    s.camera=bpy.data.objects[name];s.render.filepath=str(O/'previews'/file);bpy.ops.render.render(write_still=True);print('PREVIEW_READY',file,flush=True)
