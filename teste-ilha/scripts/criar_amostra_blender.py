"""Author the pilot terrain materials and a native-asset preview in Blender."""
from pathlib import Path
import sys,json,math,copy,bpy,addon_utils
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];R=P.parent;A=P/'amostra_natural';cfg=json.loads((A/'config.json').read_text());tile=cfg['tile']['name']
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
import numpy as np
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import SollumType
from Sollumz.tools.drawablehelper import convert_obj_to_model
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs,get_color_attr_name
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from Sollumz.ydr.ydrexport import export_ydr
from szio.gta5 import AssetTarget,AssetFormat,AssetVersion,try_load_asset,LodLevel
bpy.ops.wm.open_mainfile(filepath=str(P/'teste-ilha.blend'));scene=bpy.context.scene;T=A/'texturas'
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
def bind(m,sampler,path,normal=False):
 node=m.node_tree.nodes[sampler];node.image=bpy.data.images.load(str(path),check_existing=True);node.image.pack();node.texture_properties.embedded=True
 if normal:node.image.colorspace_settings.name='Non-Color'
 m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],node.inputs['Vector'])
layered=create_shader('terrain_cb_4lyr.sps');layered.name='Amostra grama terra barro rocha'
for i,row in enumerate(cfg['layers'][:4]):
 bind(layered,'TextureSampler_layer'+str(i),T/(row['diffuse']+'.dds'));bind(layered,'BumpSampler_layer'+str(i),T/(row['normal']+'.dds'),True)
layered.node_tree.nodes['bumpiness'].set(0,1.0)
layered.node_tree.nodes['specularIntensityMult'].set(0,.008)
sand=create_shader('normal.sps');sand.name='Amostra areia nativa';row=cfg['layers'][4]
bind(sand,'DiffuseSampler',T/(row['diffuse']+'.dds'));bind(sand,'BumpSampler',T/(row['normal']+'.dds'),True)
sand.node_tree.nodes['specularIntensityMult'].set(0,.015)
original=create_shader('default.sps');original.name='Borda do setor preservada';bind(original,'DiffuseSampler',P/'nativo/texturas'/f'{tile}.dds')
grid=np.load(P/'dados/terreno.npz')['terrain'];x0,y0,x1,y1=cfg['tile']['grid_bounds'];lo=grid[y0,x0];hi=grid[y1,x1];center=[float((lo[0]+hi[0])/2),float((lo[1]+hi[1])/2),0]
def weights(x,y,z,n):
 slope=math.hypot(n.x,n.y)/max(abs(n.z),.01)
 path=-715+14*math.sin((y+160)/54);dirt=max(0,1-abs(x-path)/6)
 mud=max(0,1-((x+750)/12)**2-((y+230)/22)**2)*.9
 rock=np.clip((slope-.30)/.28,0,1)
 return (0,float(max(mud,rock)),float(max(dirt,rock)),1)
def configure(me):
 me.materials.clear()
 for m in [layered,sand,original]:me.materials.append(m)
 mesh_add_missing_uv_maps(me);mesh_add_missing_color_attrs(me)
 for uv in me.uv_layers:
  for lp in me.loops:
   v=me.vertices[lp.vertex_index].co;uv.data[lp.index].uv=(v.x/6,v.y/6)
 for poly in me.polygons:
  p=poly.center;edge=min(p.x-lo[0],hi[0]-p.x,p.y-lo[1],hi[1]-p.y)
  poly.material_index=2 if edge<7 or p.y>-118 or p.z<0 else 1 if p.z<8 else 0
  poly.use_smooth=True
 # UVs for the untouched border preserve the original satellite texture.
 for poly in me.polygons:
  if poly.material_index==2:
   for ix in poly.loop_indices:
    p=me.vertices[me.loops[ix].vertex_index].co;me.uv_layers[0].data[ix].uv=((p.x-lo[0])/(hi[0]-lo[0]),(p.y-lo[1])/(hi[1]-lo[1]))
 for attr in me.color_attributes:
  is_mask=attr.name==get_color_attr_name(1)
  for lp in me.loops:
   v=me.vertices[lp.vertex_index]
   attr.data[lp.index].color_srgb=weights(*v.co,v.normal) if is_mask else (1,1,1,1)
for suffix in ['', '_MED','_LOW','_VLOW']:
 src=bpy.data.objects[tile+suffix];me=src.data.copy();me.transform(src.matrix_world);me.update();configure(me)
 if not suffix:src.data=me.copy();src.matrix_world=Matrix.Identity(4)
 me.transform(Matrix.Translation(tuple(-v for v in center)))
 root=bpy.data.objects.new(tile+suffix,None);scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE
 o=bpy.data.objects.new(tile+suffix+'_native',me);scene.collection.objects.link(o);o.parent=root;convert_obj_to_model(o)
 with export_context_scope(ExportContext(tile+suffix,ExportSettings(targets=targets))):export_ydr(root).save(A/'exportados',targets)
 bpy.data.objects.remove(o,do_unlink=True);bpy.data.objects.remove(root,do_unlink=True)
 print('PILOT_TERRAIN_EXPORTED',suffix or 'HIGH',flush=True)
# Reconstruct the native meshes for an editable preview; the game itself uses
# their existing archetypes, shaders, textures, LODs and collision dictionaries.
col=bpy.data.collections.new('08_AMOSTRA_NATURAL_GTA');scene.collection.children.link(col);sources={};preview_materials={}
def preview_mat(shader,name):
 key=(name,shader.preset_filename,repr(shader.parameters))
 if key in preview_materials:return preview_materials[key]
 m=bpy.data.materials.new(name+' '+shader.preset_filename);m.use_nodes=True;n=m.node_tree.nodes;links=m.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=.88
 params={str(p.name).lower():p.value for p in shader.parameters}
 for channel in ['diffusesampler','bumpsampler']:
  name=str(params.get(channel,''));path=T/(name.lower()+'.dds')
  if not path.exists():continue
  tx=n.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(path),check_existing=True);tx.image.pack()
  if channel=='diffusesampler':
   links.new(tx.outputs['Color'],bs.inputs['Base Color']);links.new(tx.outputs['Alpha'],bs.inputs['Alpha'])
   m.surface_render_method='DITHERED'
  else:
   tx.image.colorspace_settings.name='Non-Color';nm=n.new('ShaderNodeNormalMap');links.new(tx.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 preview_materials[key]=m;return m
for name in cfg['models']:
 a=try_load_asset(A/'fontes'/f'{name}.ydr');parts=[]
 for model in a.models[LodLevel.HIGH]:
  for k,g in enumerate(model.geometries):
   if 'shadow_proxy' in a.shader_group.shaders[g.shader_index].preset_filename:continue
   me=bpy.data.meshes.new(name+' '+str(len(parts)));me.from_pydata(g.vertex_buffer['Position'].tolist(),[],g.index_buffer.reshape(-1,3).tolist());me.update()
   me.materials.append(preview_mat(a.shader_group.shaders[g.shader_index],name))
   uv=me.uv_layers.new(name='UVMap 0')
   if 'TexCoord0' in g.vertex_buffer.dtype.names:
    for lp in me.loops:
     u,v=g.vertex_buffer['TexCoord0'][lp.vertex_index];uv.data[lp.index].uv=(u,1-v)
   for p in me.polygons:p.use_smooth=True
   parts.append(me)
 sources[name]=parts
for row in cfg['placements']:
 for k,me in enumerate(sources[row['name']]):
  obj=bpy.data.objects.new(row['family']+' '+row['name']+' '+str(k),me);col.objects.link(obj)
  obj.location=row['position'];obj.rotation_euler[2]=math.radians(row['heading']);obj.scale=(row['scale'],)*3
  obj['native_archetype']=row['name'];obj['lod_distance_m']=row['lod']
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.world.use_nodes=True
background=scene.world.node_tree.nodes.get('Background');background.inputs['Color'].default_value=(.55,.70,1,1);background.inputs['Strength'].default_value=.6
for obj in scene.objects:
 if obj.type=='LIGHT' and obj.data.type=='SUN':obj.data.energy=3;obj.rotation_euler=(math.radians(28),math.radians(-20),math.radians(-35))
def camera(name,pos,target,lens):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;return o
overview=camera('Amostra costa nativa',(-980,-515,200),(-730,-230,18),47)
ground=camera('Amostra ao caminhar',(-720,-158,21.5),(-727,-212,20),25)
scene.camera=overview
(A/'exportados/centro.json').write_text(json.dumps(center));bpy.ops.wm.save_as_mainfile(filepath=str(A/'amostra_natural.blend'),compress=True)
for name,cam in [('amostra_geral.png',overview),('amostra_chao.png',ground)]:
 scene.camera=cam;scene.render.filepath=str(A/name);bpy.ops.render.render(write_still=True);print('PILOT_RENDER',name,flush=True)
print('NATURAL_BLENDER_READY',flush=True)
