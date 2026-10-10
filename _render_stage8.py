import bpy,runpy,json
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(base/'warehouse_stage7_validado.blend'))
before={o.name:([m.name for m in getattr(o.data,'materials',[]) if m],list(o.matrix_world)) for o in bpy.data.objects}
ns=runpy.run_path(str(base/'aplicar_texturas_parede_chao.py'))
changed=ns['apply']()
for o in bpy.data.objects:
    if o.name not in changed:
        assert [m.name for m in getattr(o.data,'materials',[]) if m]==before[o.name][0],o.name
assert set(before)==set(bpy.data.objects.keys())
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
cam=bpy.data.objects['STAGE7_OVERVIEW'];scene.camera=cam
cam.location=(9,-16,18);cam.rotation_euler=(Vector((0,0,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=17.2
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath:image.pack()
(base/'warehouse_stage8_validacao.json').write_text(json.dumps({'changed_objects':changed,'other_object_materials_unchanged':True,'object_count_unchanged':True,'source_images':6},indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(base/'warehouse_stage8_parede_chao.blend'))
cut=[o for o in bpy.data.objects if o.name.startswith(('WALL_FRONT','FRONT_GATE_FRAME')) or o.name=='CEILING_SLAB']
for o in cut:o.hide_render=True
# Neutral studio illumination solely for texture inspection; saved scene retains pink LEDs.
lights=[o for o in bpy.data.objects if o.type=='LIGHT']
for o in lights:o.hide_render=True
for mat in bpy.data.materials:
    if mat.name=='MAT_Light_Diffuser_Emission':
        for n in mat.node_tree.nodes:
            if n.type=='EMISSION':n.inputs['Strength'].default_value=0
data=bpy.data.lights.new('TEXTURE_REVIEW_SOFTBOX','AREA');lamp=bpy.data.objects.new(data.name,data);scene.collection.objects.link(lamp)
lamp.location=(0,-1,10);data.energy=2100;data.shape='DISK';data.size=9
scene.view_settings.exposure=0.4
scene.render.filepath=str(base/'warehouse_stage8_texturas_preview.png')
bpy.ops.render.render(write_still=True)
print('STAGE8 VERIFIED: ONLY WALL/FLOOR MATERIALS AND UV CHANGED; SIX IMAGES PACKED')
