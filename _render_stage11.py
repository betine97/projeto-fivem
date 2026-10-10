import bpy,runpy,json
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(base/'warehouse_stage10_preview_melhorado.blend'))
before={o.name:[m.name for m in getattr(o.data,'materials',[]) if m] for o in bpy.data.objects}
ns=runpy.run_path(str(base/'aplicar_texturas_ventiladores.py'));changed=ns['apply']()
for o in bpy.data.objects:
    if o.name not in changed:assert before[o.name]==[m.name for m in getattr(o.data,'materials',[]) if m],o.name
assert set(before)==set(bpy.data.objects.keys())
for prefix in ['SIDE_FAN_LEFT','SIDE_FAN_RIGHT','EXHAUST_FAN_LEFT','EXHAUST_FAN_RIGHT','CEILING_VENT']:
    assert any(n.startswith(prefix) for n in changed)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath:image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(base/'warehouse_stage11_ventiladores.blend'))
(base/'warehouse_stage11_validacao.json').write_text(json.dumps({'changed':changed,'other_materials_preserved':True,'geometry_unchanged':True,'assemblies':11},indent=2),encoding='utf-8')
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True
s.render.resolution_x=1200;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.render.use_compositing=False
cam=bpy.data.objects['STAGE7_OVERVIEW'];s.camera=cam
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE','LIGHT'):o.hide_render=True
root=bpy.data.objects['SIDE_FAN_LEFT_00_ROOT'];center=root.matrix_world.translation
for o in bpy.data.objects:
    if o.name.startswith('SIDE_FAN_LEFT_00_'):o.hide_render=False
cam.location=center+Vector((2,-0.6,0.6));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.25
data=bpy.data.lights.new('REVIEW_FAN','AREA');light=bpy.data.objects.new(data.name,data);s.collection.objects.link(light)
light.location=center+Vector((2,-1,3));light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler();data.energy=220;data.size=2
s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.15,0.15,0.15,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.5
s.view_settings.exposure=0
s.render.filepath=str(base/'warehouse_stage11_ventilador_detalhe.png');bpy.ops.render.render(write_still=True)
for o in bpy.data.objects:
    if o.name.startswith('SIDE_FAN_LEFT_00_'):o.hide_render=True
root=bpy.data.objects['CEILING_VENT_00_ROOT'];center=root.matrix_world.translation
for o in bpy.data.objects:
    if o.name.startswith('CEILING_VENT_00_'):o.hide_render=False
cam.location=center+Vector((0.65,-0.7,-2));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.3
light.location=center+Vector((1,-1,-3));light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(base/'warehouse_stage11_exaustor_teto.png');bpy.ops.render.render(write_still=True)
print('STAGE11 VERIFIED',len(changed))
