"""Inspect, fit and preserve the supplied Meshy elevator in the lab Blender project."""
from pathlib import Path
import shutil

import bpy
import numpy as np
from mathutils import Vector

root=Path(__file__).resolve().parents[2]
source=Path(r'C:\Users\erons\Downloads\Meshy_AI_industrial_elevator_c_1004184824_image-to-3d-texture.glb')
folder=root/'laboratorio_fivem/elevator_source'
folder.mkdir(exist_ok=True)
shutil.copy2(source,root/'laboratorio_fivem/source_assets/Meshy_industrial_elevator_original.glb')

existing=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(source))
imported=[o for o in bpy.data.objects if o not in existing and o.type=='MESH']
original=max(imported,key=lambda o:len(o.data.polygons))
for obj in imported:
    if obj!=original:bpy.data.objects.remove(obj,do_unlink=True)
old=bpy.data.collections.get('LAB_ELEVATOR')
if old:
    for obj in list(old.objects):bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.collections.remove(old)
collection=bpy.data.collections.new('LAB_ELEVATOR')
bpy.context.scene.collection.children.link(collection)
for coll in list(original.users_collection):coll.objects.unlink(original)
collection.objects.link(original)
original.name='ELEVATOR_MESHY_SOURCE_HIGHRES'
original.hide_render=True
original.hide_set(True)

color=bpy.data.images.get('Image_0')
assert color and color.size[0]==4096
color.pack()
texture=color.copy()
texture.name='LAB_ELEVATOR_METAL_ATLAS'
texture.scale(2048,2048)
texture.filepath_raw=str(folder/'elevator_color_2048.png')
texture.file_format='PNG'
texture.save()
texture.pack()

mesh_copy=original.data.copy()
obj=bpy.data.objects.new('LAB_ELEVATOR_FLOOR_0',mesh_copy)
collection.objects.link(obj)
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active=obj
dec=obj.modifiers.new('Elevator game mesh','DECIMATE')
dec.ratio=.055
bpy.ops.object.modifier_apply(modifier=dec.name)
tri=obj.modifiers.new('Triangulate','TRIANGULATE')
bpy.ops.object.modifier_apply(modifier=tri.name)
assert 25000<len(obj.data.polygons)<75000,len(obj.data.polygons)

# Open model face is -Y. Fit it into the center rear wall, with the entire
# walkable cabin forward of the original wall at Y=6.1.
for vertex in obj.data.vertices:
    p=original.matrix_world@vertex.co
    vertex.co=(p.x*1.17,p.y*.67,p.z*1.44+1.26)
obj.data.update()
obj.location=(0,5.33,0)
material=obj.data.materials[0]
for node in material.node_tree.nodes:
    if node.type=='TEX_IMAGE' and node.image==color:node.image=texture

uv_layer=obj.data.uv_layers.active
positions=np.empty((len(obj.data.polygons)*3,3),dtype=np.float32)
normals=np.empty_like(positions)
uvs=np.empty((len(obj.data.polygons)*3,2),dtype=np.float32)
for fi,polygon in enumerate(obj.data.polygons):
    assert len(polygon.loop_indices)==3
    for ci,loop_index in enumerate(polygon.loop_indices):
        idx=fi*3+ci
        positions[idx]=obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
        normals[idx]=polygon.normal
        uvs[idx]=uv_layer.data[loop_index].uv
np.savez_compressed(folder/'elevator_fit_mesh.npz',position=positions,normal=normals,uv=uvs)

lower=obj.copy();lower.data=obj.data
collection.objects.link(lower)
lower.name='LAB_ELEVATOR_FLOOR_MINUS_1'
lower.location.z=-8

steel=bpy.data.materials.get('LAB_ELEVATOR_BRUSHED_STEEL') or bpy.data.materials.new('LAB_ELEVATOR_BRUSHED_STEEL')
steel.diffuse_color=(.33,.36,.38,1)
steel.use_nodes=True
steel.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.33,.36,.38,1)
steel.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.8
steel.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.29
screen=bpy.data.materials.get('LAB_ELEVATOR_DISPLAY_BLACK') or bpy.data.materials.new('LAB_ELEVATOR_DISPLAY_BLACK')
screen.diffuse_color=(.005,.005,.006,1)
screen.use_nodes=True
screen.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.005,.005,.006,1)
orange=bpy.data.materials.get('LAB_ELEVATOR_NUMBER_ORANGE') or bpy.data.materials.new('LAB_ELEVATOR_NUMBER_ORANGE')
orange.diffuse_color=(1,.19,.015,1)
orange.use_nodes=True
orange.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(1,.19,.015,1)
orange.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(1,.12,.01,1)
orange.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=2

def box(name,location,size,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    part=bpy.context.object
    part.name=name
    part.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    part.data.materials.append(mat)
    for old_collection in list(part.users_collection):old_collection.objects.unlink(part)
    collection.objects.link(part)
    return part

for suffix,down,label in (('0',0,'0'),('MINUS_1',-8,'-1')):
    for side in (-1,1):
        panel=box(f'LAB_ELEVATOR_DOOR_{suffix}_{"L" if side<0 else "R"}',
                  (side*.35,4.67,1.14+down),(.67,.045,2.25),steel)
        panel['door_direction']=side
        panel['slide_open_distance']=.67
    box(f'LAB_ELEVATOR_DISPLAY_{suffix}',(0,4.615,2.40+down),(.58,.035,.42),screen)
    font=bpy.data.curves.new(f'LAB_ELEVATOR_NUMBER_{suffix}','FONT')
    font.body=label;font.align_x='CENTER';font.align_y='CENTER';font.size=.15; font.extrude=.001
    number=bpy.data.objects.new(f'LAB_ELEVATOR_NUMBER_{suffix}',font)
    collection.objects.link(number)
    number.location=(0,4.588,2.40+down)
    number.rotation_euler.x=np.pi/2
    font.materials.append(orange)

# The sublevel is a separate, unfurnished shell. Architectural walls and floor
# alone are retained there; the rear of the elevator is fully closed.
concrete=bpy.data.materials.get('LAB_SUBLEVEL_CONCRETE') or bpy.data.materials.new('LAB_SUBLEVEL_CONCRETE')
concrete.diffuse_color=(.11,.11,.11,1)
for name,loc,size in (
 ('FLOOR',(0,0,-8.10),(8.2,12.2,.20)),
 ('CEILING',(0,0,-4.40),(8.2,12.2,.16)),
 ('FRONT',(0,-6.10,-6.20),(8.2,.20,3.6)),
 ('LEFT',(-4.10,0,-6.20),(.20,12.2,3.6)),
 ('RIGHT',(4.10,0,-6.20),(.20,12.2,3.6)),
 ('BACK',(0,6.10,-6.20),(8.2,.20,3.6)),
):box('LAB_SUBLEVEL_'+name,loc,size,concrete)

bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'preparacao_fivem_stage18/warehouse_stage18_preparacao.blend'))
print('ELEVATOR_BLENDER_OK',len(obj.data.polygons),'triangles',flush=True)
