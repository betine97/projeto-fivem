"""Bake the supplied artwork onto the unmodified native shirt UVs."""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Vector

job, base, project = map(Path, sys.argv[sys.argv.index('--')+1:])
cfg=json.loads((job.parents[2]/'settings.json').read_text(encoding='utf-8'))
root=job.parents[4]
sys.path[:0]=[str(root/p) for p in cfg['native_dependencies']]+[cfg['sollumz']]
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
bpy.ops.wm.open_mainfile(filepath=str(project))
scene=bpy.context.scene
obj=next(o for o in bpy.data.collections['10_VARIACAO_TRABALHO'].objects if o.type=='MESH')
original_materials=list(obj.data.materials)
art=bpy.data.images.load(str(job/'inputs/arte_tecido_original.png'));art.pack()
native=bpy.data.images.load(str(base/'source/textures/jbib_diff_000_a_uni.dds'));native.pack()
material=bpy.data.materials.new('WEST_TEXAS_BAKE_PROJECTION');material.use_nodes=True
nodes=material.node_tree.nodes;nodes.clear();links=material.node_tree.links

def node(kind):return nodes.new(kind)
def value(socket, val):
    if hasattr(val,'node'):links.new(val,socket)
    else:socket.default_value=val
def math_node(op,a,b=None):
    n=node('ShaderNodeMath');n.operation=op;value(n.inputs[0],a)
    if b is not None:value(n.inputs[1],b)
    return n.outputs[0]
def vector(x,y,z=0):
    n=node('ShaderNodeCombineXYZ')
    for socket,v in zip(n.inputs,(x,y,z)):value(socket,v)
    return n.outputs[0]
def texture(image,coords):
    n=node('ShaderNodeTexImage');n.image=image;n.extension='EXTEND';links.new(coords,n.inputs['Vector']);return n.outputs['Color']

geometry=node('ShaderNodeNewGeometry');xyz=node('ShaderNodeSeparateXYZ');links.new(geometry.outputs['Position'],xyz.inputs[0])
normal=node('ShaderNodeSeparateXYZ');links.new(geometry.outputs['Normal'],normal.inputs[0])
# Image 2 is a front textile panel, not a ready-made GTA UV atlas.
# Width 36 cm; top .58 m; graphic lands at approx .27–.47 m above pelvis.
u=math_node('ADD',math_node('DIVIDE',xyz.outputs['X'],.36),.5)
v=math_node('DIVIDE',math_node('SUBTRACT',xyz.outputs['Z'],.13),.45)
print_color=texture(art,vector(u,v))
plain_u=math_node('FRACT',math_node('ADD',math_node('MULTIPLY',xyz.outputs['X'],3),.5))
plain_v=math_node('ADD',.82,math_node('MULTIPLY',math_node('FRACT',math_node('MULTIPLY',xyz.outputs['Z'],3)),.16))
plain_color=texture(art,vector(plain_u,plain_v))
front=math_node('MULTIPLY',math_node('LESS_THAN',normal.outputs['Y'],-.35),math_node('LESS_THAN',xyz.outputs['Y'],0))
front=math_node('MULTIPLY',front,math_node('GREATER_THAN',xyz.outputs['Z'],.24))
front=math_node('MULTIPLY',front,math_node('LESS_THAN',xyz.outputs['Z'],.50))
front=math_node('MULTIPLY',front,math_node('LESS_THAN',math_node('ABSOLUTE',xyz.outputs['X']),.19))
mix=node('ShaderNodeMixRGB');mix.blend_type='MIX';value(mix.inputs[0],front);value(mix.inputs[1],plain_color);value(mix.inputs[2],print_color)
# Retain the base's subtle baked fold shading without remaking the provided artwork.
uv=node('ShaderNodeUVMap');uv.uv_map=obj.data.uv_layers[0].name
native_color=texture(native,uv.outputs[0]);luma=node('ShaderNodeRGBToBW');links.new(native_color,luma.inputs[0])
shade=math_node('MINIMUM',math_node('MAXIMUM',math_node('DIVIDE',luma.outputs[0],.30),.85),1.08)
multiply=node('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
links.new(mix.outputs[0],multiply.inputs[1]);value(multiply.inputs[2],vector(shade,shade,shade))
emit=node('ShaderNodeEmission');links.new(multiply.outputs[0],emit.inputs['Color'])
output=node('ShaderNodeOutputMaterial');links.new(emit.outputs[0],output.inputs['Surface'])
atlas=bpy.data.images.new('WEST_TEXAS_UV_ATLAS',width=2048,height=2048,alpha=False)
target=node('ShaderNodeTexImage');target.image=atlas;nodes.active=target
obj.data.materials.clear();obj.data.materials.append(material)
for poly in obj.data.polygons:poly.material_index=0
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.bake.margin=16
bpy.ops.object.bake(type='EMIT')
atlas.filepath_raw=str(job/'inputs/atlas_west_texas.png');atlas.file_format='PNG';atlas.save();atlas.pack()
obj.data.materials.clear()
for mat in original_materials:obj.data.materials.append(mat)
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.shared.shader_nodes import SzShaderNodeParameter
meshes={obj.data}
for level in ('high','medium','low','very_low'):
    lod=getattr(obj.sz_lods,level)
    if lod.mesh:meshes.add(lod.mesh)
for mesh in meshes:
    for index,mat in enumerate(list(mesh.materials)):
        if not mat or not mat.node_tree:continue
        preset='ped.sps' if 'ped_default' not in mat.shader_properties.filename else 'ped_default.sps'
        replacement=create_shader(preset)
        old_nodes={n.name.lower():n for n in mat.node_tree.nodes}
        for n in replacement.node_tree.nodes:
            old=old_nodes.get(n.name.lower())
            if n.type=='TEX_IMAGE' and old and old.type=='TEX_IMAGE':n.image=old.image
            if isinstance(n,SzShaderNodeParameter) and isinstance(old,SzShaderNodeParameter):
                for i in range(min(n.num_cols*n.num_rows,old.num_cols*old.num_rows)):n.set(i,old.get(i))
            if n.name.lower()=='diffusesampler':n.image=atlas
        mesh.materials[index]=replacement

# Four technical views of the actual base mesh with the baked material.
scene.render.engine='CYCLES';scene.cycles.samples=12
scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.world.color=(.35,.35,.35);scene.view_settings.view_transform='Standard'
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
for name,position,power,size in [('KEY',(-1,-2,2),170,2),('FILL',(1,-1,1),80,2),('RIM',(0,2,1),120,2)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=position
    light.rotation_euler=(Vector((0,0,.25))-light.location).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('QA_CAMERA');camera=bpy.data.objects.new('QA_CAMERA',camera_data);scene.collection.objects.link(camera)
camera_data.type='ORTHO';camera_data.ortho_scale=.91;scene.camera=camera
for name,angle in [('front',0),('back',math.pi),('left',math.pi/2),('right',-math.pi/2)]:
    camera.location=(2*math.sin(angle),-2*math.cos(angle),.28)
    camera.rotation_euler=(Vector((0,0,.25))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(job/'qa'/f'{name}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(job/'work/variacao.blend'))
(job/'qa/art_projection.json').write_text(json.dumps({'method':'Blender emission bake from supplied original image',
    'front_projection_width_m':.36,'front_projection_z_range_m':[.13,.58],
    'back_and_sleeves':'unprinted textile from original image',
    'native_normal_specular':'preserved','atlas_size':[2048,2048],
    'views':['front','back','left','right'],'visual_review':'pending'},indent=2),encoding='utf-8')
print('WEST_TEXAS_BAKE_AND_FOUR_VIEWS_OK')
