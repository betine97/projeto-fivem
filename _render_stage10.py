import bpy,runpy,json
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(base/'warehouse_stage9_dutos_texturizados.blend'))
before={o.name:[m.name for m in getattr(o.data,'materials',[]) if m] for o in bpy.data.objects}
ns=runpy.run_path(str(base/'aplicar_metal_tubulacoes_stage10.py'))
changed=ns['apply']()
for o in bpy.data.objects:
    if o.name not in changed:assert before[o.name]==[m.name for m in getattr(o.data,'materials',[]) if m],o.name
assert set(before)==set(bpy.data.objects.keys())
assert all(n in changed for n in ('DUCT_ELBOW_LEFT_SEG_00','CEILING_VENT_00_BELL','CEILING_DUCT_MAIN_00','SERVICE_LEFT_MAIN_PIPE_0','CONDUIT_BACK_MAIN'))
bpy.ops.wm.save_as_mainfile(filepath=str(base/'warehouse_stage10_tubulacoes.blend'))
(base/'warehouse_stage10_validacao.json').write_text(json.dumps({'changed':changed,'other_materials_preserved':True,'geometry_unchanged':True},indent=2),encoding='utf-8')
scene=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='LIGHT':o.hide_render=True
    if o.name.startswith(('WALL_FRONT','FRONT_GATE_FRAME')) or o.name=='CEILING_SLAB':o.hide_render=True
for n in bpy.data.materials['MAT_Light_Diffuser_Emission'].node_tree.nodes:
    if n.type=='EMISSION':n.inputs['Strength'].default_value=0
data=bpy.data.lights.new('REVIEW_STEEL','AREA');lamp=bpy.data.objects.new(data.name,data);scene.collection.objects.link(lamp)
lamp.location=(0,-1,10);data.energy=2100;data.shape='DISK';data.size=9
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.view_settings.exposure=0.4
cam=bpy.data.objects['STAGE7_OVERVIEW'];scene.camera=cam
scene.render.filepath=str(base/'warehouse_stage10_preview.png');bpy.ops.render.render(write_still=True)
cam.location=(4,-6,6);cam.rotation_euler=(Vector((0,-2.5,3.05))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.8
scene.render.filepath=str(base/'warehouse_stage10_detalhe.png');bpy.ops.render.render(write_still=True)
print('STAGE10 VERIFIED',len(changed))
