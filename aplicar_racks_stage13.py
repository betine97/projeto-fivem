import bpy,json
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'warehouse_stage12_plantas.blend'))
before={o.name:{'materials':[m.name if m else None for m in getattr(o.data,'materials',[])], 'matrix':[list(r) for r in o.matrix_world]} for o in bpy.data.objects}
racks=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('RACK_LEFT_','RACK_RIGHT_'))]
assert racks
mat=bpy.data.materials.new('STAGE13_RACK_Metal_Escuro_Desgastado');mat.use_nodes=True
t=mat.node_tree;p=t.nodes.get('Principled BSDF')
tex=t.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(BASE/'texturas_racks'/'metal_escuro_desgastado.png'))
tex.image.colorspace_settings.name='sRGB';tex.interpolation='Linear';tex.extension='REPEAT'
uv=t.nodes.new('ShaderNodeUVMap');uv.uv_map='RackUV_metrico';t.links.new(uv.outputs[0],tex.inputs[0])
t.links.new(tex.outputs['Color'],p.inputs['Base Color'])
p.inputs['Metallic'].default_value=.72;p.inputs['Roughness'].default_value=.57
bump=t.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.0008
t.links.new(tex.outputs['Color'],bump.inputs['Height']);t.links.new(bump.outputs[0],p.inputs['Normal'])
rough=t.nodes.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=0;rough.inputs['From Max'].default_value=.6
rough.inputs['To Min'].default_value=.42;rough.inputs['To Max'].default_value=.72
t.links.new(tex.outputs['Color'],rough.inputs['Value']);t.links.new(rough.outputs[0],p.inputs['Roughness'])
mat.diffuse_color=(.06,.055,.047,1)
for obj in racks:
    obj.data.materials.clear();obj.data.materials.append(mat)
    layer=obj.data.uv_layers.get('RackUV_metrico') or obj.data.uv_layers.new(name='RackUV_metrico')
    # Planar mapping per face in real scene units: no stretched texture on long beams.
    for poly in obj.data.polygons:
        poly.material_index=0
        normal=obj.matrix_world.to_3x3().inverted().transposed()@poly.normal
        axis=max(range(3),key=lambda i:abs(normal[i]));a,b=[i for i in range(3) if i!=axis]
        for li in poly.loop_indices:
            co=obj.matrix_world@obj.data.vertices[obj.data.loops[li].vertex_index].co
            layer.data[li].uv=(co[a]/.65,co[b]/.65)
    obj.data.uv_layers.active=layer

# All previously textured components stay together, with their existing materials.
changed={o.name for o in racks}
for name,old in before.items():
    obj=bpy.data.objects[name]
    assert [list(r) for r in obj.matrix_world]==old['matrix'],name
    if name not in changed:assert [m.name if m else None for m in getattr(obj.data,'materials',[])]==old['materials'],name
assert len([o for o in bpy.data.objects if o.name.endswith('_PLANT') and o.name.startswith('PLACEHOLDER_')])==18

hidden=[]
for obj in bpy.data.objects:
    if any(x in obj.name.upper() for x in ('ROOF','CEILING_SLAB','WALL_FRONT')):
        obj.hide_render=True;obj.hide_set(True);hidden.append(obj.name)

col=bpy.data.collections.new('APRESENTACAO_Luz_de_apoio');bpy.context.scene.collection.children.link(col)
data=bpy.data.lights.new('APRESENTACAO_Preenchimento','AREA');data.energy=1400;data.size=8
lamp=bpy.data.objects.new(data.name,data);col.objects.link(lamp);lamp.location=(0,0,7)
s=bpy.context.scene;s.camera=bpy.data.objects['STAGE7_OVERVIEW']
s.render.engine='CYCLES';s.cycles.samples=128;s.cycles.use_denoising=True
s.cycles.preview_samples=64;s.cycles.use_preview_denoising=True
s.render.resolution_x=1600;s.render.resolution_y=1400;s.render.resolution_percentage=100
s.render.filepath=str(BASE/'warehouse_stage13_projeto_completo.png')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.region_3d.view_perspective='CAMERA';sp.region_3d.view_camera_zoom=0
            sp.shading.type='MATERIAL';sp.shading.use_scene_world=True;sp.shading.use_scene_lights=True
            sp.overlay.show_overlays=False
for obj in bpy.context.selected_objects:obj.select_set(False)
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath:im.pack()
assert all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.filepath)
report={'rack_parts':len(racks),'rack_objects':sorted(changed),'previous_materials_preserved':True,'previous_object_transforms_preserved':True,'plants':18,'packed_images':sum(bool(i.packed_file) for i in bpy.data.images),'cutaway_hidden_objects':hidden}
(BASE/'warehouse_stage13_validacao.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'warehouse_stage13_projeto_completo.blend'))
bpy.ops.render.render(write_still=True)
print('STAGE13 OK',json.dumps(report))
