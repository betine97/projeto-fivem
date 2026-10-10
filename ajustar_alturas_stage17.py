import bpy,json
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'warehouse_stage16_projeto_completo.blend'))
rise=.75
for o in bpy.data.objects:
    if o.name.startswith('RACK_'):
        if '_POST_' in o.name:
            o.scale.z*=2.8/2.05;o.location.z+=rise/2
        elif o.name.endswith('_TOP') or '_LIGHT_RAIL_' in o.name:o.location.z+=rise
fixtures=[o for o in bpy.data.objects if o.name.startswith('LIGHT_FIXTURE_')]
for o in fixtures:
    # Children of fixture parts already follow their parent (pink edges, etc.).
    if not o.parent or not o.parent.name.startswith('LIGHT_FIXTURE_'):o.location.z+=rise
plants=[o for o in bpy.data.objects if o.name.startswith('PLACEHOLDER_') and o.name.endswith('_PLANT')]
for o in plants:o.scale.z*=1.65
roof=bpy.data.objects['CEILING_SLAB'];roof.hide_render=False;roof.hide_set(False);roof.hide_viewport=False
for o in bpy.data.objects:
    if o.name.startswith('WALL_FRONT'):o.hide_render=False;o.hide_set(False)
# The exterior presentation light cannot illuminate through the closed ceiling.
for o in bpy.data.objects:
    if o.name.startswith('APRESENTACAO_'):o.hide_render=True;o.hide_set(True)
col=bpy.data.collections.new('ILUMINACAO_Ambiente_Interior');bpy.context.scene.collection.children.link(col)
for i,y in enumerate((-4,0,4)):
    d=bpy.data.lights.new('INTERIOR_Apoio_'+str(i),'AREA');d.energy=100;d.size=2.5;d.color=(.83,.88,1)
    o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=(0,y,2.8)
s=bpy.context.scene
d=bpy.data.cameras.new('CAMERA_INTERIOR');cam=bpy.data.objects.new(d.name,d);s.collection.objects.link(cam)
cam.location=(0,-5.72,1.80);target=Vector((0,3.5,1.65));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.type='PERSP';d.lens=19;d.clip_start=.03
s.camera=cam
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.context.view_layer.update()
tops=[max((o.matrix_world@Vector(c)).z for c in o.bound_box) for o in plants]
assert len(plants)==18 and max(tops)<2.55
assert not roof.hide_render
for o in fixtures:
    if o.type=='LIGHT':assert (o.matrix_world.to_3x3()@Vector((0,0,-1))).normalized().z<-.999
report={'rack_height_m':2.8,'rack_and_led_raise_m':rise,'plant_vertical_scale':1.65,'plant_top_min_m':min(tops),'plant_top_max_m':max(tops),'pot_size_unchanged':True,'closed_roof':True}
(BASE/'warehouse_stage17_validacao.json').write_text(json.dumps(report,indent=2))
s.render.resolution_x=1500;s.render.resolution_y=1100;s.cycles.samples=80;s.render.filepath=str(BASE/'warehouse_stage17_interior.png')
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'warehouse_stage17_teto_fechado.blend'))
bpy.ops.render.render(write_still=True)
print('STAGE17 OK',report)
