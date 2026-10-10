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
art=bpy.data.images.load(str(job/'inputs'/json.loads((job/'job.json').read_text(encoding='utf-8'))['reference_image']));art.pack()
native=bpy.data.images.load(str(base/'source/textures/lowr_diff_001_a_whi.dds'));native.pack()
material=bpy.data.materials.new('JEANS_WASHED_BAKE_PROJECTION');material.use_nodes=True
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

# Register front-photo coordinates using source silhouette rows and native mesh cross-sections.
# This is a Blender material bake; all original native UVs and vertex buffers remain untouched.
import numpy as np
pixels=np.asarray(art.pixels[:],dtype=np.float32).reshape(art.size[1],art.size[0],4)[::-1]
blue=(pixels[:,:,3]>.5)&(pixels[:,:,2]>pixels[:,:,0]*1.03)&(pixels[:,:,2]>.07)
verts=np.asarray([tuple(v.co) for v in obj.data.vertices])
edges=np.asarray([tuple(e.vertices) for e in obj.data.edges])
a,b=verts[edges[:,0]],verts[edges[:,1]]
ref_uv=obj.data.uv_layers.new(name='REFERENCE_FRONT')
vertex_uv=[];row_report=[]
for pos in verts:
 x,y,z=pos
 sy=int(round(65+(.084-z)/(1.070)*(1345-65)));sy=max(66,min(1344,sy))
 sx=np.flatnonzero(blue[sy])
 if len(sx)<10:
  for delta in range(1,25):
   sx=np.flatnonzero(blue[min(1344,sy+delta)])
   if len(sx)>10:break
 intersects=((a[:,2]<=z)&(b[:,2]>=z))|((b[:,2]<=z)&(a[:,2]>=z))
 valid=intersects&(abs(b[:,2]-a[:,2])>1e-7)
 t=(z-a[valid,2])/(b[valid,2]-a[valid,2])
 nx=a[valid,0]+t*(b[valid,0]-a[valid,0])
 if z<-.20:
  nx=nx[nx>=0] if x>=0 else nx[nx<=0]
  sx=sx[sx>=art.size[0]/2] if x>=0 else sx[sx<=art.size[0]/2]
 if len(nx)<2:nx=verts[verts[:,0]>=0,0] if x>=0 else verts[verts[:,0]<=0,0]
 if len(sx)<2:sx=np.array([art.size[0]*.3,art.size[0]*.7])
 lo,hi=float(nx.min()),float(nx.max())
 q=max(0,min(1,(x-lo)/max(hi-lo,1e-5)))
 u=(float(sx.min())+q*(float(sx.max())-float(sx.min())))/art.size[0]
 vertex_uv.append((u,1-sy/art.size[1]))
for loop in obj.data.loops:ref_uv.data[loop.index].uv=vertex_uv[loop.vertex_index]
obj.data.uv_layers.active_index=0
reference_coords=node('ShaderNodeUVMap');reference_coords.uv_map=ref_uv.name
reference=texture(art,reference_coords.outputs[0])
geometry=node('ShaderNodeNewGeometry');xyz=node('ShaderNodeSeparateXYZ');links.new(geometry.outputs['Position'],xyz.inputs[0])
normal=node('ShaderNodeSeparateXYZ');links.new(geometry.outputs['Normal'],normal.inputs[0])
# The supplied fabric panels follow individual legs, without repeating the large wear marks.
leg_center=math_node('MULTIPLY',math_node('SIGN',xyz.outputs['X']),.145)
u=math_node('ADD',.5,math_node('DIVIDE',math_node('SUBTRACT',xyz.outputs['X'],leg_center),.27))
upper=bpy.data.images.load(str(job/'inputs/denim_upper.png'));upper.pack()
thigh=bpy.data.images.load(str(job/'inputs/denim_thigh.png'));thigh.pack()
hem=bpy.data.images.load(str(job/'inputs/denim_hem.png'));hem.pack()
upper_color=texture(upper,vector(u,math_node('DIVIDE',math_node('ADD',xyz.outputs['Z'],.55),.65)))
thigh_color=texture(thigh,vector(u,math_node('DIVIDE',math_node('ADD',xyz.outputs['Z'],.88),.76)))
hem_color=texture(hem,vector(u,math_node('DIVIDE',math_node('ADD',xyz.outputs['Z'],1.00),.31)))
def clamp(a):return math_node('MINIMUM',math_node('MAXIMUM',a,0),1)
def mix_color(factor,c1,c2):
 n=node('ShaderNodeMixRGB');value(n.inputs[0],factor);value(n.inputs[1],c1);value(n.inputs[2],c2);return n.outputs[0]
low=clamp(math_node('DIVIDE',math_node('SUBTRACT',-.24,xyz.outputs['Z']),.25))
cloth=mix_color(low,upper_color,thigh_color)
hem_weight=clamp(math_node('DIVIDE',math_node('SUBTRACT',-.72,xyz.outputs['Z']),.08))
cloth=mix_color(hem_weight,cloth,hem_color)
uv=node('ShaderNodeUVMap');uv.uv_map=obj.data.uv_layers[0].name
native_color=texture(native,uv.outputs[0])
native_luma=node('ShaderNodeRGBToBW');links.new(native_color,native_luma.inputs[0])
# Recolor native back-pocket/seam shading, rather than repeating front whiskers on the back.
ramp=node('ShaderNodeValToRGB');links.new(native_luma.outputs[0],ramp.inputs[0])
colors=[(0,(.012,.032,.068,1)),(.010,(.018,.052,.115,1)),(.032,(.045,.110,.205,1)),(.090,(.105,.205,.315,1)),(.250,(.280,.365,.440,1)),(1,(.55,.47,.30,1))]
for old in list(ramp.color_ramp.elements)[1:]:ramp.color_ramp.elements.remove(old)
ramp.color_ramp.elements[0].position=colors[0][0];ramp.color_ramp.elements[0].color=colors[0][1]
for pos,col in colors[1:]:e=ramp.color_ramp.elements.new(pos);e.color=col
# Square unprinted weave patch from supplied image 2, baked and box-projected at uniform scale.
weave=bpy.data.images.new('DENIM_WEAVE',width=512,height=512,alpha=False)
wm=bpy.data.materials.new('DENIM_WEAVE_BAKE');wm.use_nodes=True;wn=wm.node_tree.nodes;wn.clear();wl=wm.node_tree.links
wu=wn.new('ShaderNodeTexCoord');wv=wn.new('ShaderNodeVectorMath');wv.operation='MULTIPLY_ADD'
wl.new(wu.outputs['UV'],wv.inputs[0]);wv.inputs[1].default_value=(.18,.18,1);wv.inputs[2].default_value=(.6,.82,0)
wt=wn.new('ShaderNodeTexImage');wt.image=upper;wl.new(wv.outputs[0],wt.inputs[0])
we=wn.new('ShaderNodeEmission');wl.new(wt.outputs[0],we.inputs[0]);wo=wn.new('ShaderNodeOutputMaterial');wl.new(we.outputs[0],wo.inputs['Surface'])
wb=wn.new('ShaderNodeTexImage');wb.image=weave;wn.active=wb
bpy.ops.mesh.primitive_plane_add(size=1);plane=bpy.context.object;plane.data.materials.append(wm)
scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.bake.margin=0
bpy.ops.object.bake(type='EMIT');weave.pack();bpy.data.objects.remove(plane,do_unlink=True)
ws=node('ShaderNodeTexImage');ws.image=weave;ws.extension='REPEAT';ws.projection='BOX';ws.projection_blend=.2
wc=node('ShaderNodeVectorMath');wc.operation='SCALE';wc.inputs['Scale'].default_value=7
links.new(geometry.outputs['Position'],wc.inputs[0]);links.new(wc.outputs[0],ws.inputs[0])
wluma=node('ShaderNodeRGBToBW');links.new(ws.outputs['Color'],wluma.inputs[0])
wshade=math_node('MINIMUM',math_node('MAXIMUM',math_node('DIVIDE',wluma.outputs[0],.025),.82),1.12)
back=node('ShaderNodeMixRGB');back.blend_type='MULTIPLY';back.inputs[0].default_value=1
value(back.inputs[1],ramp.outputs[0]);value(back.inputs[2],vector(wshade,wshade,wshade))
# Fading from image 3 contributes gently on the lateral thighs; the front follows the reference.
wear_luma=node('ShaderNodeRGBToBW');links.new(thigh_color,wear_luma.inputs[0])
wear=math_node('MINIMUM',math_node('MAXIMUM',wear_luma.outputs[0],0),.30)
back_color=mix_color(math_node('MULTIPLY',wear,.12),back.outputs[0],thigh_color)
front=clamp(math_node('DIVIDE',math_node('SUBTRACT',-.50,normal.outputs['Y']),.40))
combined=mix_color(front,back_color,reference)
# The stitched hem panel is restricted to the forward-facing cuff to avoid stretched side grain.
hem_factor=math_node('MULTIPLY',math_node('MULTIPLY',hem_weight,front),.12)
combined=mix_color(hem_factor,combined,hem_color)
# Preserve native skin/material regions at the cuff rather than painting denim onto them.
channels=node('ShaderNodeSeparateColor');channels.mode='RGB';links.new(native_color,channels.inputs[0])
skin=math_node('MULTIPLY',math_node('GREATER_THAN',channels.outputs['Red'],math_node('MULTIPLY',channels.outputs['Blue'],1.35)),math_node('LESS_THAN',xyz.outputs['Z'],-.90))
combined=mix_color(skin,combined,native_color)
emit=node('ShaderNodeEmission');links.new(combined,emit.inputs['Color'])
output=node('ShaderNodeOutputMaterial');links.new(emit.outputs[0],output.inputs['Surface'])
atlas=bpy.data.images.new('JEANS_WASHED_UV_ATLAS',width=2048,height=2048,alpha=False)
target=node('ShaderNodeTexImage');target.image=atlas;nodes.active=target
obj.data.materials.clear();obj.data.materials.append(material)
for poly in obj.data.polygons:poly.material_index=0
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.bake.margin=16
bpy.ops.object.bake(type='EMIT')
atlas.filepath_raw=str(job/'inputs/atlas_jeans_washed.png');atlas.file_format='PNG';atlas.save();atlas.pack()
obj.data.materials.clear()
for mat in original_materials:obj.data.materials.append(mat)
meshes={obj.data}
for level in ('high','medium','low','very_low'):
 lod=getattr(obj.sz_lods,level)
 if lod.mesh:meshes.add(lod.mesh)
for mesh in meshes:
 for mat in mesh.materials:
  if mat and mat.node_tree:
   for n in mat.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.name.lower()=='diffusesampler':n.image=atlas

# Four technical views of the actual base mesh with the baked material.
scene.render.engine='CYCLES';scene.cycles.samples=12
scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.world.color=(.35,.35,.35);scene.view_settings.view_transform='Standard'
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
for name,position,power,size in [('KEY',(-1,-2,2),170,2),('FILL',(1,-1,1),80,2),('RIM',(0,2,1),120,2)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=position
    light.rotation_euler=(Vector((0,0,-.45))-light.location).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('QA_CAMERA');camera=bpy.data.objects.new('QA_CAMERA',camera_data);scene.collection.objects.link(camera)
camera_data.type='ORTHO';camera_data.ortho_scale=1.31;scene.camera=camera
for name,angle in [('front',0),('back',math.pi),('left',math.pi/2),('right',-math.pi/2)]:
    camera.location=(2*math.sin(angle),-2*math.cos(angle),-.45)
    camera.rotation_euler=(Vector((0,0,-.45))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(job/'qa'/f'{name}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(job/'work/variacao.blend'))
(job/'qa/art_projection.json').write_text(json.dumps({'method':'Blender emission bake from supplied original image',
    'front_projection':'silhouette-registered source reference to native mesh cross-sections',
    'back_and_sides':'supplied denim upper/thigh/hem panels with native structure retained',
    'native_normal_specular':'preserved','atlas_size':[2048,2048],
    'views':['front','back','left','right'],'visual_review':'pending'},indent=2),encoding='utf-8')
print('JEANS_WASHED_BAKE_AND_FOUR_VIEWS_OK')
