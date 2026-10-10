"""Fit a lightweight, transparent version of the supplied GLB to both racks."""
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

root=Path(__file__).resolve().parents[2]
source=root/'laboratorio_fivem/source_assets/Meshy_cleanroom_containment_original.glb'
clear_texture=root/'laboratorio_fivem/containment_source/containment_clear_rgba.png'
out=root/'laboratorio_fivem/containment_source'
existing=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(source))
imported=[obj for obj in bpy.data.objects if obj not in existing and obj.type=='MESH']
assert imported
obj=max(imported,key=lambda item:len(item.data.polygons))
initial=len(obj.data.polygons)

# The original contains 1.8 million triangles. Keep its silhouette, pleats,
# clips and original UV atlas at a practical map-asset size.
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active=obj
decimate=obj.modifiers.new('Game-ready Meshy containment','DECIMATE')
decimate.ratio=.020
bpy.ops.object.modifier_apply(modifier=decimate.name)
triangulate=obj.modifiers.new('Triangulate for FiveM','TRIANGULATE')
bpy.ops.object.modifier_apply(modifier=triangulate.name)
mesh=obj.data
assert len(mesh.polygons)<60000 and len(mesh.polygons)>20000, len(mesh.polygons)

# The GLB's long X axis becomes the rack's long Y axis. The nonuniform fit is
# applied to vertices because YMAP entities cannot independently scale X/Y.
old_matrix=obj.matrix_world.copy()
for vertex in mesh.vertices:
    p=old_matrix@vertex.co
    vertex.co=(-p.y*(2.16/.754),p.x*(7.40/1.903),p.z*(2.65/.783)+1.625)
obj.matrix_world.identity()
mesh.update()

image=bpy.data.images.load(str(clear_texture),check_existing=True)
image.name='LAB_MESHY_CLEAR_VINYL_ATLAS'
image.colorspace_settings.name='sRGB'
image.pack()
material=bpy.data.materials.get('LAB_MESHY_CLEAR_CONTAINMENT') or bpy.data.materials.new('LAB_MESHY_CLEAR_CONTAINMENT')
material.use_nodes=True
material.surface_render_method='DITHERED'
nodes=material.node_tree.nodes
nodes.clear()
links=material.node_tree.links
uv=nodes.new('ShaderNodeUVMap')
uv.uv_map=mesh.uv_layers.active.name
uv.location=(-480,0)
tex=nodes.new('ShaderNodeTexImage')
tex.image=image
tex.location=(-260,0)
bsdf=nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Metallic'].default_value=.07
bsdf.inputs['Roughness'].default_value=.18
bsdf.inputs['IOR'].default_value=1.46
bsdf.location=(0,0)
output=nodes.new('ShaderNodeOutputMaterial')
output.location=(280,0)
links.new(uv.outputs['UV'],tex.inputs['Vector'])
links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
mesh.materials.clear()
mesh.materials.append(material)

# Save triangle corners after decimation with original UVs for the GTA asset.
positions=np.empty((len(mesh.polygons)*3,3),dtype=np.float32)
normals=np.empty_like(positions)
uvs=np.empty((len(mesh.polygons)*3,2),dtype=np.float32)
for face_index,polygon in enumerate(mesh.polygons):
    assert len(polygon.loop_indices)==3
    for vertex_index,loop_index in enumerate(polygon.loop_indices):
        target=face_index*3+vertex_index
        positions[target]=mesh.vertices[mesh.loops[loop_index].vertex_index].co
        normals[target]=polygon.normal
        uvs[target]=mesh.uv_layers.active.data[loop_index].uv
np.savez_compressed(out/'containment_fit_mesh.npz',position=positions,normal=normals,uv=uvs)

collection=bpy.data.collections.get('LAB_MESHY_CONTAINMENT') or bpy.data.collections.new('LAB_MESHY_CONTAINMENT')
if collection.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(collection)
for old_collection in list(obj.users_collection):old_collection.objects.unlink(obj)
collection.objects.link(obj)
obj.name='LAB_MESHY_RIGHT_CLEAR_CONTAINMENT'
obj.location=(2.48,-.80,0)
other=obj.copy()
other.data=obj.data
collection.objects.link(other)
other.name='LAB_MESHY_LEFT_CLEAR_CONTAINMENT'
other.location=(-2.48,-.80,0)
for imported_obj in imported:
    if imported_obj not in (obj,other):bpy.data.objects.remove(imported_obj,do_unlink=True)

bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'preparacao_fivem_stage18/warehouse_stage18_preparacao.blend'))
print('CONTAINMENT_BLENDER_OK',initial,'->',len(mesh.polygons),'triangles',len(mesh.vertices),'vertices',flush=True)
