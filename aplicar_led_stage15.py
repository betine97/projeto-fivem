import bpy,json
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'warehouse_stage14_projeto_completo.blend'))
before={o.name:([m.name if m else None for m in getattr(o.data,'materials',[])],[list(r) for r in o.matrix_world]) for o in bpy.data.objects}
lights={o.name:(tuple(o.data.color),o.data.energy) for o in bpy.data.objects if o.type=='LIGHT'}
targets=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('LIGHT_FIXTURE_')]
leds=[o for o in targets if '_LED_' in o.name]
assert len(leds)==12,len(leds)
oldmat=leds[0].data.materials[0]
em=next((n for n in oldmat.node_tree.nodes if n.type=='EMISSION'),None)
strength=em.inputs['Strength'].default_value if em else 9.0
mats={}
for kind in ('rosa','preto'):
    mat=bpy.data.materials.new('STAGE15_LED_'+kind);mat.use_nodes=True;t=mat.node_tree;p=t.nodes.get('Principled BSDF')
    tex=t.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(BASE/'texturas_led'/(kind+'.png')));tex.extension='REPEAT'
    uv=t.nodes.new('ShaderNodeUVMap');uv.uv_map='LED_UV_metrico';t.links.new(uv.outputs[0],tex.inputs[0])
    t.links.new(tex.outputs['Color'],p.inputs['Base Color'])
    if kind=='rosa':
        t.links.new(tex.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=strength
        p.inputs['Roughness'].default_value=.42;mat.diffuse_color=(1,.008,.14,1)
    else:
        p.inputs['Metallic'].default_value=.60;p.inputs['Roughness'].default_value=.57;mat.diffuse_color=(.045,.045,.045,1)
        bump=t.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.0004
        t.links.new(tex.outputs['Color'],bump.inputs['Height']);t.links.new(bump.outputs[0],p.inputs['Normal'])
    mats[kind]=mat
changed={}
for o in targets:
    kind='rosa' if '_LED_' in o.name else 'preto'
    o.data.materials.clear();o.data.materials.append(mats[kind]);changed[o.name]=kind
    layer=o.data.uv_layers.get('LED_UV_metrico') or o.data.uv_layers.new(name='LED_UV_metrico')
    for p in o.data.polygons:
        p.material_index=0
        normal=o.matrix_world.to_3x3().inverted().transposed()@p.normal
        axis=max(range(3),key=lambda i:abs(normal[i]));a,b=[i for i in range(3) if i!=axis]
        for li in p.loop_indices:
            co=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
            layer.data[li].uv=(co[a]/.40,co[b]/.40)
    o.data.uv_layers.active=layer
for name,(materials,transform) in before.items():
    o=bpy.data.objects[name];assert [list(r) for r in o.matrix_world]==transform,name
    if name not in changed:assert [m.name if m else None for m in getattr(o.data,'materials',[])]==materials,name
assert set(before)==set(bpy.data.objects.keys())
for name,(color,energy) in lights.items():
    o=bpy.data.objects[name];assert tuple(o.data.color)==color and o.data.energy==energy
    if name.startswith('LIGHT_FIXTURE_'):
        direction=(o.matrix_world.to_3x3()@Vector((0,0,-1))).normalized()
        assert direction.dot(Vector((0,0,-1)))>.999,name
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath:im.pack()
assert all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.filepath)
report={'fixtures':6,'emissive_strips':len(leds),'emission_strength':strength,'changed':changed,'other_materials_preserved':True,'light_power_color_and_downward_direction_preserved':True,'geometry_and_positions_preserved':True}
(BASE/'warehouse_stage15_validacao.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;s.render.filepath=str(BASE/'warehouse_stage15_projeto_completo.png')
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'warehouse_stage15_projeto_completo.blend'))
bpy.ops.render.render(write_still=True)

# Detail review only, without saving temporary isolation or lighting.
prefix='LIGHT_FIXTURE_00_00';center=bpy.data.objects[prefix+'_BODY'].matrix_world.translation.copy()
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE','LIGHT'):o.hide_render=not o.name.startswith(prefix)
cam=s.camera;cam.location=center+Vector((.75,-1.5,-.8));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.9
data=bpy.data.lights.new('REVIEW_LED','AREA');data.energy=250;data.size=3
lamp=bpy.data.objects.new(data.name,data);s.collection.objects.link(lamp);lamp.location=center+Vector((0,-2,-2));lamp.rotation_euler=(center-lamp.location).to_track_quat('-Z','Y').to_euler()
s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.10,.10,.10,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
s.render.use_compositing=False;s.cycles.samples=64;s.render.resolution_x=1500;s.render.resolution_y=700
s.render.filepath=str(BASE/'warehouse_stage15_led_detalhe.png');bpy.ops.render.render(write_still=True)
print('STAGE15 OK',len(changed))
