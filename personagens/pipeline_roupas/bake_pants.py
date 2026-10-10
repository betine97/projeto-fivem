"""Bake supplied pants references and fabric panels onto unchanged native UVs."""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Vector

job, base, project = map(Path, sys.argv[sys.argv.index('--')+1:])
job_data=json.loads((job/'job.json').read_text(encoding='utf-8'))
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
material=bpy.data.materials.new('PANTS_REFERENCE_BAKE');material.use_nodes=True
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
silhouette=pixels[:,:,3]>.8
rows=np.flatnonzero(silhouette.sum(axis=1)>20)
if len(rows)<100:raise RuntimeError('Missing opaque reference silhouette')
ref_top,ref_bottom=int(rows.min()),int(rows.max())
verts=np.asarray([tuple(v.co) for v in obj.data.vertices])
edges=np.asarray([tuple(e.vertices) for e in obj.data.edges])
a,b=verts[edges[:,0]],verts[edges[:,1]]
z_top,z_bottom=float(verts[:,2].max()),float(verts[:,2].min())
ref_uv=obj.data.uv_layers.new(name='REFERENCE_FRONT')
vertex_uv=[];flame_vertex_uv=[];row_report=[]
for pos in verts:
 x,y,z=pos
 sy=int(round(ref_top+(z_top-z)/(z_top-z_bottom)*(ref_bottom-ref_top)));sy=max(ref_top,min(ref_bottom,sy))
 sx=np.flatnonzero(silhouette[sy])
 if len(sx)<10:
  for delta in range(1,25):
   sx=np.flatnonzero(silhouette[min(ref_bottom,sy+delta)])
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
 if 'flame_art' in job_data:
  flame=job_data['flame_art'];left,right=flame['canvas_uv_right'] if x>=0 else flame['canvas_uv_left']
  flame_vertex_uv.append((left+q*(right-left),(z-flame['z_bottom'])/(flame['z_top']-flame['z_bottom'])))
for loop in obj.data.loops:ref_uv.data[loop.index].uv=vertex_uv[loop.vertex_index]
obj.data.uv_layers.active_index=0
reference_coords=node('ShaderNodeUVMap');reference_coords.uv_map=ref_uv.name
reference=texture(art,reference_coords.outputs[0])
geometry=node('ShaderNodeNewGeometry');xyz=node('ShaderNodeSeparateXYZ');links.new(geometry.outputs['Position'],xyz.inputs[0])
normal=node('ShaderNodeSeparateXYZ');links.new(geometry.outputs['Normal'],normal.inputs[0])
# The supplied fabric panels follow individual legs, without repeating the large wear marks.
leg_center=math_node('MULTIPLY',math_node('SIGN',xyz.outputs['X']),.145)
u=math_node('ADD',.5,math_node('DIVIDE',math_node('SUBTRACT',xyz.outputs['X'],leg_center),.27))
upper=bpy.data.images.load(str(job/'inputs/tecido_cintura.png'));upper.pack()
thigh=bpy.data.images.load(str(job/'inputs/tecido_pernas.png'));thigh.pack()
hem=bpy.data.images.load(str(job/'inputs/tecido_barra.png'));hem.pack()
upper_color=texture(upper,vector(u,math_node('DIVIDE',math_node('ADD',xyz.outputs['Z'],.55),.65)))
thigh_color=texture(thigh,vector(u,math_node('DIVIDE',math_node('ADD',xyz.outputs['Z'],.88),.76)))
def clamp(a):return math_node('MINIMUM',math_node('MAXIMUM',a,0),1)
hem_color=texture(hem,vector(math_node('ADD',.15,math_node('MULTIPLY',clamp(u),.70)),math_node('ADD',.17,math_node('MULTIPLY',clamp(math_node('DIVIDE',math_node('ADD',xyz.outputs['Z'],1.00),.31)),.65))))
def mix_color(factor,c1,c2):
 n=node('ShaderNodeMixRGB');value(n.inputs[0],factor);value(n.inputs[1],c1);value(n.inputs[2],c2);return n.outputs[0]
hem_weight=clamp(math_node('DIVIDE',math_node('SUBTRACT',-.72,xyz.outputs['Z']),.08))
uv=node('ShaderNodeUVMap');uv.uv_map=obj.data.uv_layers[0].name
native_color=texture(native,uv.outputs[0])
native_luma=node('ShaderNodeRGBToBW');links.new(native_color,native_luma.inputs[0])
# Continuous leg coordinates keep vertical stripes upright around the side/back.
pattern_uv=obj.data.uv_layers.new(name='PATTERN_AUTHORING')
for polygon in obj.data.polygons:
 center=polygon.center.x
 leg_center=.145 if center>=0 else -.145
 values=[]
 for index in polygon.loop_indices:
  pos=obj.data.vertices[obj.data.loops[index].vertex_index].co
  horizontal=(math.atan2(pos.x-leg_center,-pos.y)/(2*math.pi)+.5)*.55
  values.append((index,horizontal,pos.z))
 if max(v[1] for v in values)-min(v[1] for v in values)>.275:
  values=[(i,u+.55 if u<.275 else u,v) for i,u,v in values]
 for i,u,v in values:pattern_uv.data[i].uv=(u*job_data.get('pattern_scale',1.8),v*job_data.get('pattern_scale',1.8))
obj.data.uv_layers.active_index=0
pattern_coords=node('ShaderNodeUVMap');pattern_coords.uv_map=pattern_uv.name
pattern=node('ShaderNodeTexImage');pattern.image=thigh;pattern.extension='REPEAT'
if 'clean_back_crop' in job_data:
 crop=job_data['clean_back_crop'];separate=node('ShaderNodeSeparateXYZ');links.new(pattern_coords.outputs[0],separate.inputs[0])
 cropped=vector(math_node('ADD',crop[0],math_node('MULTIPLY',math_node('FRACT',separate.outputs['X']),crop[2])),math_node('ADD',crop[1],math_node('MULTIPLY',math_node('FRACT',separate.outputs['Y']),crop[3])))
 links.new(cropped,pattern.inputs[0])
else:links.new(pattern_coords.outputs[0],pattern.inputs[0])
shade=math_node('MINIMUM',math_node('MAXIMUM',math_node('DIVIDE',native_luma.outputs[0],.18),.68),1.12)
pattern_color=pattern.outputs['Color']
if 'clean_back_crop' in job_data:
 # Keep photographic whiskers out of the repeating weave: retain source tone with subtle fiber contrast.
 source_pixels=np.asarray(thigh.pixels[:],dtype=np.float32).reshape(thigh.size[1],thigh.size[0],4)
 patch=source_pixels[int(crop[1]*thigh.size[1]):int((crop[1]+crop[3])*thigh.size[1]),int(crop[0]*thigh.size[0]):int((crop[0]+crop[2])*thigh.size[0]),:3]
 tone=np.percentile(patch.reshape(-1,3),20,axis=0)
 mean_luma=max(float((patch*np.array([.2126,.7152,.0722])).sum(axis=2).mean()),.001)
 fiber=node('ShaderNodeRGBToBW');links.new(pattern_color,fiber.inputs[0])
 amount=job_data.get('clean_back_contrast',.04)
 fiber_scale=math_node('MINIMUM',math_node('MAXIMUM',math_node('DIVIDE',fiber.outputs[0],mean_luma),1-amount),1+amount)
 weave=node('ShaderNodeMixRGB');weave.blend_type='MULTIPLY';weave.inputs[0].default_value=1
 value(weave.inputs[1],tuple(float(c) for c in tone)+(1,));value(weave.inputs[2],vector(fiber_scale,fiber_scale,fiber_scale))
 pattern_color=weave.outputs[0]
back=node('ShaderNodeMixRGB');back.blend_type='MULTIPLY';back.inputs[0].default_value=1
value(back.inputs[1],pattern_color);value(back.inputs[2],vector(shade,shade,shade))
back_color=back.outputs[0]
if 'flame_art' in job_data:
 flame_uv=obj.data.uv_layers.new(name='FLAME_CANVAS')
 for loop in obj.data.loops:flame_uv.data[loop.index].uv=flame_vertex_uv[loop.vertex_index]
 obj.data.uv_layers.active_index=0
 coords=node('ShaderNodeUVMap');coords.uv_map=flame_uv.name
 def flame_texture(filename):
  image=bpy.data.images.load(str(job/'inputs'/filename));image.pack()
  tex=node('ShaderNodeTexImage');tex.image=image;tex.extension='CLIP';links.new(coords.outputs[0],tex.inputs[0]);return tex
 front_art=flame_texture(job_data['flame_art']['front']);back_art=flame_texture(job_data['flame_art']['back'])
 # Remove the flames from the reference before applying the supplied front component once.
 rgb=node('ShaderNodeSeparateColor');rgb.mode='RGB';links.new(reference,rgb.inputs[0])
 warm=math_node('MULTIPLY',math_node('GREATER_THAN',rgb.outputs['Red'],math_node('MULTIPLY',rgb.outputs['Blue'],1.5)),math_node('GREATER_THAN',rgb.outputs['Red'],.12))
 reference=mix_color(warm,reference,back_color)
 reference=mix_color(front_art.outputs['Alpha'],reference,front_art.outputs['Color'])
 back_facing=clamp(math_node('DIVIDE',math_node('SUBTRACT',normal.outputs['Y'],.05),.45))
 back_color=mix_color(math_node('MULTIPLY',back_facing,back_art.outputs['Alpha']),back_color,back_art.outputs['Color'])
front=clamp(math_node('DIVIDE',math_node('SUBTRACT',-.50,normal.outputs['Y']),.40))
combined=mix_color(front,back_color,reference)
# Additional supplied upper panel is confined to the front fly below the belt.
upper_weight=math_node('MULTIPLY',front,math_node('MULTIPLY',math_node('GREATER_THAN',xyz.outputs['Z'],-.22),math_node('LESS_THAN',xyz.outputs['Z'],-.01)))
combined=mix_color(math_node('MULTIPLY',upper_weight,.10),combined,upper_color)
# The stitched hem panel is restricted to the forward-facing cuff to avoid stretched side grain.
hem_factor=math_node('MULTIPLY',math_node('MULTIPLY',hem_weight,front),job_data.get('hem_panel_weight',.12))
combined=mix_color(hem_factor,combined,hem_color)
# Preserve native skin/material regions at the cuff rather than painting denim onto them.
channels=node('ShaderNodeSeparateColor');channels.mode='RGB';links.new(native_color,channels.inputs[0])
skin=math_node('MULTIPLY',math_node('GREATER_THAN',channels.outputs['Red'],math_node('MULTIPLY',channels.outputs['Blue'],1.35)),math_node('LESS_THAN',xyz.outputs['Z'],-.90))
combined=mix_color(skin,combined,native_color)
emit=node('ShaderNodeEmission');links.new(combined,emit.inputs['Color'])
output=node('ShaderNodeOutputMaterial');links.new(emit.outputs[0],output.inputs['Surface'])
atlas=bpy.data.images.new('PANTS_NATIVE_UV_ATLAS',width=2048,height=2048,alpha=False)
target=node('ShaderNodeTexImage');target.image=atlas;nodes.active=target
obj.data.materials.clear();obj.data.materials.append(material)
for poly in obj.data.polygons:poly.material_index=0
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.bake.margin=16
bpy.ops.object.bake(type='EMIT')
atlas.filepath_raw=str(job/'inputs/atlas_calca.png');atlas.file_format='PNG';atlas.save();atlas.pack()
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
for name,position,power,size in [('KEY',(-1,-2,2),90,2),('FILL',(1,-1,1),40,2),('RIM',(0,2,1),60,2)]:
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
    'back_and_sides':'supplied leg fabric on continuous leg coordinates, native pocket/seam shading retained',
    'native_normal_specular':'preserved','atlas_size':[2048,2048],
    'views':['front','back','left','right'],'visual_review':'pending','reference_silhouette_rows':[ref_top,ref_bottom],'native_z_bounds':[z_bottom,z_top],
    'flame_art':job_data.get('flame_art'),'clean_back_crop':job_data.get('clean_back_crop')},indent=2),encoding='utf-8')
print('PANTS_BAKE_AND_FOUR_VIEWS_OK')
