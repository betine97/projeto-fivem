import bpy,runpy,json
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(base/'warehouse_stage8_parede_chao.blend'))
before={o.name:[m.name for m in getattr(o.data,'materials',[]) if m] for o in bpy.data.objects}
ns=runpy.run_path(str(base/'aplicar_texturas_dutos_retos.py'))
changed=ns['apply']()
assert len(changed)==17,len(changed)
for o in bpy.data.objects:
    if o.name not in changed:assert before[o.name]==[m.name for m in getattr(o.data,'materials',[]) if m],o.name
assert set(before)==set(bpy.data.objects.keys())
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath:image.pack()
scene=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(base/'warehouse_stage9_dutos_texturizados.blend'))
(base/'warehouse_stage9_validacao.json').write_text(json.dumps({'changed':changed,'other_materials_preserved':True,'object_count_unchanged':True},indent=2),encoding='utf-8')
# Temporary neutral review lighting. Never saved over the deliverable.
for o in bpy.data.objects:
    if o.type=='LIGHT':o.hide_render=True
    if o.name.startswith(('WALL_FRONT','FRONT_GATE_FRAME')) or o.name=='CEILING_SLAB':o.hide_render=True
mat=bpy.data.materials.get('MAT_Light_Diffuser_Emission')
for n in mat.node_tree.nodes:
    if n.type=='EMISSION':n.inputs['Strength'].default_value=0
data=bpy.data.lights.new('REVIEW_DUCTS','AREA');lamp=bpy.data.objects.new('REVIEW_DUCTS',data);scene.collection.objects.link(lamp)
lamp.location=(0,-1,10);data.energy=2100;data.shape='DISK';data.size=9
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.view_settings.exposure=0.4
cam=bpy.data.objects['STAGE7_OVERVIEW'];scene.camera=cam
scene.render.filepath=str(base/'warehouse_stage9_preview.png');bpy.ops.render.render(write_still=True)
cam.location=(4,-6,6);cam.rotation_euler=(Vector((0,-2.5,3.05))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.8
scene.render.filepath=str(base/'warehouse_stage9_duto_detalhe.png');bpy.ops.render.render(write_still=True)
print('STAGE9 VERIFIED: 17 STRAIGHT SECTIONS; OTHER MATERIALS PRESERVED')
