import bpy,json
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parent

def material(name,metal,rough,color):
    m=bpy.data.materials.new('STAGE14_'+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    t=m.node_tree;p=t.nodes.get('Principled BSDF');p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    image=bpy.data.images.load(str(BASE/'texturas_zona_tecnica'/(name+'.png')),check_existing=True)
    geo=t.nodes.new('ShaderNodeNewGeometry')
    density=t.nodes.new('ShaderNodeVectorMath');density.operation='SCALE';density.inputs[3].default_value=1/.85;t.links.new(geo.outputs['Position'],density.inputs[0])
    coord=t.nodes.new('ShaderNodeSeparateXYZ');t.links.new(density.outputs[0],coord.inputs[0])
    ab=t.nodes.new('ShaderNodeVectorMath');ab.operation='ABSOLUTE';t.links.new(geo.outputs['Normal'],ab.inputs[0])
    normal=t.nodes.new('ShaderNodeSeparateXYZ');t.links.new(ab.outputs[0],normal.inputs[0])
    weights=[]
    for axis in range(3):
        n=t.nodes.new('ShaderNodeMath');n.operation='POWER';n.inputs[1].default_value=4;t.links.new(normal.outputs[axis],n.inputs[0]);weights.append(n.outputs[0])
    summ=t.nodes.new('ShaderNodeMath');summ.operation='ADD';t.links.new(weights[0],summ.inputs[0]);t.links.new(weights[1],summ.inputs[1])
    total=t.nodes.new('ShaderNodeMath');total.operation='ADD';t.links.new(summ.outputs[0],total.inputs[0]);t.links.new(weights[2],total.inputs[1])
    colors=[]
    for axis,(a,b) in enumerate(((1,2),(0,2),(0,1))):
        vec=t.nodes.new('ShaderNodeCombineXYZ');t.links.new(coord.outputs[a],vec.inputs[0]);t.links.new(coord.outputs[b],vec.inputs[1])
        tex=t.nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='REPEAT';t.links.new(vec.outputs[0],tex.inputs[0])
        w=t.nodes.new('ShaderNodeMath');w.operation='DIVIDE';t.links.new(weights[axis],w.inputs[0]);t.links.new(total.outputs[0],w.inputs[1])
        mul=t.nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;t.links.new(tex.outputs['Color'],mul.inputs[1]);t.links.new(w.outputs[0],mul.inputs[2]);colors.append(mul.outputs[0])
    add=t.nodes.new('ShaderNodeMixRGB');add.blend_type='ADD';add.inputs[0].default_value=1;t.links.new(colors[0],add.inputs[1]);t.links.new(colors[1],add.inputs[2])
    final=t.nodes.new('ShaderNodeMixRGB');final.blend_type='ADD';final.inputs[0].default_value=1;t.links.new(add.outputs[0],final.inputs[1]);t.links.new(colors[2],final.inputs[2])
    t.links.new(final.outputs[0],p.inputs['Base Color'])
    bump=t.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.0008
    t.links.new(final.outputs[0],bump.inputs['Height']);t.links.new(bump.outputs[0],p.inputs['Normal'])
    return m

def classify(n):
    if n.startswith('TECH_BLUE_TANK_'):return 'preto_desgastado' if n.endswith('_CAP') else 'azul_desgastado'
    if n.startswith('TECH_BENCH_') and not n.startswith('TECH_BENCH_CASE_'):return 'metal_claro'
    if n.startswith('TECH_SHELF_'):return 'metal_claro' if ('BOARD' in n or n.endswith('_LID')) else 'preto_desgastado'
    if n.startswith('TECH_CABINET_'):return 'metal_claro' if '_DOOR_' in n else 'preto_desgastado'
    if n.startswith('MAIN_ELECTRICAL_PANEL'):return 'preto_desgastado' if n.endswith(('_BODY','_SWITCH_BASE','_SWITCH')) else 'metal_claro'
    if n.startswith('MAIN_PANEL_BOLT_'):return 'metal_claro'

bpy.ops.wm.open_mainfile(filepath=str(BASE/'warehouse_stage13_projeto_completo.blend'))
before={o.name:([m.name if m else None for m in getattr(o.data,'materials',[])],[list(r) for r in o.matrix_world]) for o in bpy.data.objects}
mats={n:material(n,m,r,c) for n,m,r,c in [('azul_desgastado',.22,.56,(.015,.09,.30)),('preto_desgastado',.48,.60,(.055,.052,.048)),('metal_claro',.82,.48,(.40,.42,.44))]}
changed={}
for obj in bpy.data.objects:
    kind=classify(obj.name)
    if kind and obj.type in ('MESH','CURVE'):
        obj.data.materials.clear();obj.data.materials.append(mats[kind])
        for part in (obj.data.polygons if obj.type=='MESH' else obj.data.splines):part.material_index=0
        changed[obj.name]=kind
for name,(materials,transform) in before.items():
    obj=bpy.data.objects[name];assert [list(r) for r in obj.matrix_world]==transform,name
    if name not in changed:assert [m.name if m else None for m in getattr(obj.data,'materials',[])]==materials,name
assert set(before)==set(bpy.data.objects.keys())
assert all(any(n.startswith(prefix) for n in changed) for prefix in ('TECH_BLUE_TANK_','TECH_BENCH_','TECH_SHELF_','TECH_CABINET_','MAIN_ELECTRICAL_PANEL'))
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath:im.pack()
assert all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.filepath)
report={'changed':changed,'previous_other_materials_preserved':True,'geometry_and_transforms_preserved':True,'packed_images':sum(bool(i.packed_file) for i in bpy.data.images)}
(BASE/'warehouse_stage14_validacao.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;s.render.filepath=str(BASE/'warehouse_stage14_projeto_completo.png')
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'warehouse_stage14_projeto_completo.blend'))
bpy.ops.render.render(write_still=True)

# Rear-zone detail from inside the room. This temporary camera/light is not saved.
cam=s.camera;target=Vector((0,5.3,1.15));cam.location=(0,.5,2.2);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8.2
s.render.resolution_x=1800;s.render.resolution_y=850;s.cycles.samples=96
data=bpy.data.lights.new('REVIEW_TECH_AREA','AREA');data.energy=650;data.size=5
lamp=bpy.data.objects.new(data.name,data);s.collection.objects.link(lamp);lamp.location=(0,2.6,3);lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(BASE/'warehouse_stage14_zona_tecnica.png');bpy.ops.render.render(write_still=True)
print('STAGE14 OK',len(changed))
