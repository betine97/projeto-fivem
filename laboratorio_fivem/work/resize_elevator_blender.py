"""Fit the deeper lift and matching basement finishes in the Blender source."""
from pathlib import Path
import bpy

root=Path(__file__).resolve().parents[2]
collection=bpy.data.collections['LAB_ELEVATOR']
car=bpy.data.objects['LAB_ELEVATOR_FLOOR_0']
if not car.get('widened_double_depth'):
    for v in car.data.vertices:
        v.co.x*=1.5
        v.co.y=v.co.y*2+.637
    car.data.update()
    car['widened_double_depth']=True

def textured_material(name,filename,metallic=0.0,roughness=.85):
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    principled=nodes.get('Principled BSDF')
    old=nodes.get(name+'_IMAGE')
    if old:nodes.remove(old)
    image=bpy.data.images.load(str(root/'laboratorio_fivem/elevator_source'/filename),check_existing=False)
    image.pack()
    tex=nodes.new('ShaderNodeTexImage')
    tex.name=name+'_IMAGE';tex.image=image
    mat.node_tree.links.new(tex.outputs['Color'],principled.inputs['Base Color'])
    principled.inputs['Metallic'].default_value=metallic
    principled.inputs['Roughness'].default_value=roughness
    return mat

door_mat=textured_material('LAB_ELEVATOR_BRUSHED_STEEL','elevator_door_metal.png',.65,.35)
trim_mat=textured_material('LAB_ELEVATOR_DARK_CLADDING','elevator_dark_steel.png',.65,.38)
wall_mat=textured_material('LAB_SUBLEVEL_MATCHING_WALL','elevator_basement_wall.png')
floor_mat=textured_material('LAB_SUBLEVEL_MATCHING_FLOOR','elevator_basement_floor.png')

def box(name,location,size,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    obj=bpy.context.object
    obj.name=name
    obj.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(material)
    for old in list(obj.users_collection):old.objects.unlink(obj)
    collection.objects.link(obj)
    return obj

for suffix,z in (('0',0),('MINUS_1',-8)):
    for letter,side in (('L',-1),('R',1)):
        panel=bpy.data.objects[f'LAB_ELEVATOR_DOOR_{suffix}_{letter}']
        panel.location.x=side*.52
        panel.dimensions=(1.02,.055,2.24)
        panel['slide_open_distance']=.63
        panel.data.materials.clear()
        panel.data.materials.append(door_mat)
    display=bpy.data.objects[f'LAB_ELEVATOR_DISPLAY_{suffix}']
    display.location=(0,4.525,2.46+z)
    display.dimensions=(.50,.035,.22)
    number=bpy.data.objects[f'LAB_ELEVATOR_NUMBER_{suffix}']
    number.location=(0,4.499,2.46+z)
    for old in [o for o in collection.objects if o.name.startswith(f'LAB_ELEVATOR_TRIM_{suffix}_')]:
        bpy.data.objects.remove(old,do_unlink=True)
    boxes=[
        ((-1.145,-.68,1.15),(.12,.13,2.30)),
        (( 1.145,-.68,1.15),(.12,.13,2.30)),
        ((0,-.68,2.46),(2.40,.13,.43)),
        ((0,-.68,.025),(2.40,.13,.05)),
        ((-1.055,.66,1.12),(.055,2.45,2.24)),
        (( 1.055,.66,1.12),(.055,2.45,2.24)),
        ((0,1.88,1.12),(2.05,.055,2.24)),
        ((0,.66,.055),(2.05,2.45,.055)),
        ((0,.66,2.30),(2.05,2.45,.055)),
    ]
    for i,(center,size) in enumerate(boxes):
        box(f'LAB_ELEVATOR_TRIM_{suffix}_{i}',
            (center[0],center[1]+5.33,center[2]+z),size,trim_mat)

shell={
 'FLOOR':((0,.7,-8.10),(8.2,13.6,.24),floor_mat),
 'CEILING':((0,.7,-4.38),(8.2,13.6,.16),wall_mat),
 'FRONT':((0,-6.10,-6.20),(8.2,.20,3.6),wall_mat),
 'LEFT':((-4.10,.7,-6.20),(.20,13.6,3.6),wall_mat),
 'RIGHT':((4.10,.7,-6.20),(.20,13.6,3.6),wall_mat),
 'BACK':((0,7.50,-6.20),(8.2,.20,3.6),wall_mat),
}
for name,(location,size,material) in shell.items():
    obj=bpy.data.objects['LAB_SUBLEVEL_'+name]
    obj.location=location
    obj.dimensions=size
    obj.data.materials.clear()
    obj.data.materials.append(material)
    uv=obj.data.uv_layers.active or obj.data.uv_layers.new(name='UVMap')
    for polygon in obj.data.polygons:
        n=polygon.normal
        for loop_index in polygon.loop_indices:
            vertex=obj.data.vertices[obj.data.loops[loop_index].vertex_index]
            point=obj.matrix_world@vertex.co
            if abs(n.z)>.5:coord=(point.x/1.9,point.y/1.9)
            elif abs(n.x)>.5:coord=(point.y/1.9,point.z/1.9)
            else:coord=(point.x/1.9,point.z/1.9)
            uv.data[loop_index].uv=coord

bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'preparacao_fivem_stage18/warehouse_stage18_preparacao.blend'))
print('RESIZED_ELEVATOR_BLENDER_OK',flush=True)
