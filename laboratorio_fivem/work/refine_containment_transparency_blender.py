"""Keep Meshy metal details, replace its layered vinyl with clear single strips."""
from pathlib import Path
import bpy
import numpy as np

root=Path(__file__).resolve().parents[2]
folder=root/'laboratorio_fivem/containment_source'
collection=bpy.data.collections['LAB_MESHY_CONTAINMENT']

def packed_image(path,name):
    image=bpy.data.images.load(str(path),check_existing=False)
    image.name=name
    image.colorspace_settings.name='sRGB'
    image.pack()
    return image

frame_image=packed_image(folder/'containment_clear_rgba.png','LAB_MESHY_FRAME_CLEAR_ATLAS')
frame_material=bpy.data.materials['LAB_MESHY_CLEAR_CONTAINMENT']
frame_material.surface_render_method='BLENDED'
for node in frame_material.node_tree.nodes:
    if node.type=='TEX_IMAGE':node.image=frame_image

strip_image=packed_image(folder/'vinyl_strip_clear_rgba.png','LAB_CLEAR_VINYL_STRIP_IMAGE')
material=bpy.data.materials.get('LAB_CLEAR_VINYL_STRIPS') or bpy.data.materials.new('LAB_CLEAR_VINYL_STRIPS')
material.use_nodes=True
material.surface_render_method='BLENDED'
nodes=material.node_tree.nodes
nodes.clear()
links=material.node_tree.links
tex=nodes.new('ShaderNodeTexImage')
tex.image=strip_image
tex.location=(-280,0)
bsdf=nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Metallic'].default_value=.04
bsdf.inputs['Roughness'].default_value=.13
bsdf.inputs['IOR'].default_value=1.46
bsdf.location=(0,0)
output=nodes.new('ShaderNodeOutputMaterial')
output.location=(280,0)
links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])

data=np.load(folder/'containment_strips.npz')
positions=data['position']
uvs=data['uv']
assert len(positions)%3==0
mesh=bpy.data.meshes.new('LAB_CLEAR_VINYL_STRIPS_MESH')
mesh.from_pydata(positions.tolist(),[],[(i,i+1,i+2) for i in range(0,len(positions),3)])
mesh.update()
layer=mesh.uv_layers.new(name='LAB_CLEAR_STRIP_UV')
for i,texcoord in enumerate(uvs):layer.data[i].uv=texcoord
mesh.materials.append(material)
for name,x in [('LAB_CLEAR_VINYL_RIGHT',2.48),('LAB_CLEAR_VINYL_LEFT',-2.48)]:
    old=bpy.data.objects.get(name)
    if old:bpy.data.objects.remove(old,do_unlink=True)
    obj=bpy.data.objects.new(name,mesh)
    collection.objects.link(obj)
    obj.location=(x,-.8,0)

bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'preparacao_fivem_stage18/warehouse_stage18_preparacao.blend'))
print('BLENDER_CLEAR_STRIPS_OK',len(positions)//3,'triangles','two racks',flush=True)
