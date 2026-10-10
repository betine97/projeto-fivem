"""Keep the supplied Meshy GLB in Blender; show clean movable curtains instead."""
from pathlib import Path
import math

import bpy

root=Path(__file__).resolve().parents[2]
folder=root/'laboratorio_fivem/containment_source'
source=bpy.data.collections['LAB_MESHY_CONTAINMENT']
for obj in source.objects:
    if obj.name.startswith(('LAB_MESHY_','LAB_CLEAR_VINYL_')):
        obj.hide_render=True
        obj.hide_set(True)

old=bpy.data.collections.get('LAB_MOVING_VINYL')
if old:
    for obj in list(old.objects):bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.collections.remove(old)
collection=bpy.data.collections.new('LAB_MOVING_VINYL')
bpy.context.scene.collection.children.link(collection)

metal=bpy.data.materials.get('LAB_CURTAIN_TRACK_BLACK') or bpy.data.materials.new('LAB_CURTAIN_TRACK_BLACK')
metal.diffuse_color=(.025,.027,.029,1)
metal.use_nodes=True
metal.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.025,.027,.029,1)

image=bpy.data.images.load(str(folder/'vinyl_strip_clear_rgba.png'),check_existing=False)
image.name='LAB_CLEAR_MOVING_VINYL_IMAGE'
image.pack()
clear=bpy.data.materials.get('LAB_CLEAR_MOVING_VINYL') or bpy.data.materials.new('LAB_CLEAR_MOVING_VINYL')
clear.use_nodes=True
clear.surface_render_method='BLENDED'
nodes=clear.node_tree.nodes
nodes.clear()
tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.location=(-250,0)
bsdf=nodes.new('ShaderNodeBsdfPrincipled');bsdf.location=(0,0)
bsdf.inputs['Roughness'].default_value=.30
bsdf.inputs['IOR'].default_value=1.46
out=nodes.new('ShaderNodeOutputMaterial');out.location=(250,0)
clear.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
clear.node_tree.links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
clear.node_tree.links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])

verts=[];faces=[];uv_faces=[]
for j in range(10):
    for i in range(2):
        u0,u1=i/2,(i+1)/2
        v0,v1=j/10,(j+1)/10
        first=len(verts)
        for u,v in ((u0,v0),(u1,v0),(u1,v1),(u0,v1)):
            verts.append(((u-.5)*.375,.006*math.sin(2*math.pi*v+u*math.pi),-.045-v*2.57))
        faces.append((first,first+1,first+2,first+3))
        uv_faces.append(((u0,v0),(u1,v0),(u1,v1),(u0,v1)))
mesh=bpy.data.meshes.new('LAB_VINYL_STRIP_PIVOT_TOP_MESH')
mesh.from_pydata(verts,[],faces);mesh.update()
uv=mesh.uv_layers.new(name='Vinyl UV')
for polygon,coords in zip(mesh.polygons,uv_faces):
    for loop_index,coord in zip(polygon.loop_indices,coords):uv.data[loop_index].uv=coord
mesh.materials.append(clear)

def box(name,location,scale):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    obj=bpy.context.object
    obj.name=name
    obj.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(metal)
    for previous in list(obj.users_collection):previous.objects.unlink(obj)
    collection.objects.link(obj)
    return obj

count=0
for rack_label,rack_x in (('LEFT',-2.48),('RIGHT',2.48)):
    for side in (-1,1):
        x=rack_x+side*1.072
        box(f'LAB_TRACK_{rack_label}_{side}_TOP',(x,-.8,2.954),(.096,7.44,.076))
        box(f'LAB_TRACK_{rack_label}_{side}_LOWER',(x,-.8,2.885),(.042,7.44,.03))
        for i in range(1,21):
            obj=bpy.data.objects.new(f'LAB_VINYL_{rack_label}_SIDE_{side}_{i:02}',mesh)
            collection.objects.link(obj)
            obj.location=(rack_x+side*1.07,-.8-3.70+(i-.5)*.37,2.95)
            obj.rotation_euler.z=math.pi/2
            obj['rail']=f'{rack_label} side {side}'
            obj['interaction']='E: slide curtain to ends'
            count+=1
    box(f'LAB_TRACK_{rack_label}_FRONT',(rack_x,-4.50,2.954),(2.20,.096,.076))
    for i in range(1,7):
        obj=bpy.data.objects.new(f'LAB_VINYL_{rack_label}_FRONT_{i:02}',mesh)
        collection.objects.link(obj)
        obj.location=(rack_x-1.08+(i-.5)*.36,-4.50,2.95)
        obj['rail']=f'{rack_label} front'
        obj['interaction']='E: slide curtain to sides'
        count+=1

# The original supplied GLB remains in LAB_MESHY_CONTAINMENT for inspection.
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'preparacao_fivem_stage18/warehouse_stage18_preparacao.blend'))
print('BLENDER_MOVING_VINYL_OK',count,'independent strips',flush=True)
