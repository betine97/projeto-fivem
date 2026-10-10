"""Bake authored Blender colors to UV atlases and export native GTA drawables."""
import bpy,sys,json,math,struct,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'laboratorio_fivem';OUT=WORK/'exports_hd';OUT.mkdir(exist_ok=True);BAKE=WORK/'bakes_hd';BAKE.mkdir(exist_ok=True)
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\media_deps']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from PIL import Image
from Sollumz.sollumz_properties import SollumType
from Sollumz.tools.drawablehelper import convert_obj_to_model
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.ydr.ydrexport import export_ydr
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from szio.gta5 import *
from szio.types import Vector as SV
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'preparacao_fivem_stage18/warehouse_stage18_preparacao.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=1;s.cycles.device='CPU';s.render.bake.margin=6
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_set(False)
# Bake base-color graphs through emission, retaining authored texture scaling and weathering.
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 ns=mat.node_tree.nodes;ls=mat.node_tree.links
 bs=next((n for n in ns if n.type=='BSDF_PRINCIPLED'),None);out=next((n for n in ns if n.type=='OUTPUT_MATERIAL'),None)
 if bs and out:
  em=ns.new('ShaderNodeEmission');inp=bs.inputs['Base Color']
  if inp.is_linked:ls.new(inp.links[0].from_socket,em.inputs['Color'])
  else:em.inputs['Color'].default_value=inp.default_value
  ls.new(em.outputs[0],out.inputs['Surface'])
# Permanent infill of unused exits and a short entrance vestibule.
extra=[];collisions=[]
def box(name,loc,dims,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);extra.append(o);collisions.append({'loc':list(loc),'dims':list(dims)});return o
wall=bpy.data.materials['STAGE8_PAREDE_REFERENCIAS'];floor=bpy.data.materials['STAGE8_CHAO_REFERENCIAS']
box('LAB_Seal_Back',(0,6,1.1),(1.1,.20,2.2),wall);box('LAB_Seal_Side',(-4,-3.6,1.1),(.20,1.1,2.2),wall)
box('LAB_Vestibule_Floor',(-1.05,-7.05,-.08),(5.7,2.30,.16),floor)
box('LAB_Vestibule_Ceiling',(-1.05,-7.05,3.4),(5.7,2.3,.15),wall)
box('LAB_Vestibule_Left',(-3.9,-7.05,1.7),(.15,2.3,3.4),wall)
box('LAB_Vestibule_Right',(1.8,-7.05,1.7),(.15,2.3,3.4),wall)
# External opening centered x=-2.695, y=-7.962, width 1.2.
box('LAB_Vestibule_Front_Left',(-3.60,-8.04,1.7),(.6,.15,3.4),wall)
box('LAB_Vestibule_Front_Right',(-.15,-8.04,1.7),(3.9,.15,3.4),wall)
box('LAB_Vestibule_Lintel',(-2.695,-8.04,2.84),(1.2,.15,1.12),wall)
# Original architectural boxes and useful prop collision surfaces.
for o in bpy.data.collections['COLISAO_Proxies'].objects:
 bb=[o.matrix_world@Vector(v) for v in o.bound_box];lo=Vector([min(v[j] for v in bb) for j in range(3)]);hi=Vector([max(v[j] for v in bb) for j in range(3)])
 collisions.append({'loc':list((lo+hi)*.5),'dims':list(hi-lo)})
for loc,dims in [((-2.475,-.8,1.15),(2.15,7.4,2.3)),((2.475,-.8,1.15),(2.15,7.4,2.3))]:collisions.append({'loc':list(loc),'dims':list(dims)})
(WORK/'collisions.json').write_text(json.dumps(collisions,indent=2))
groups={};instances=[]
for o in list(bpy.data.collections['EXPORT_Estrutura'].objects)+list(bpy.data.collections['EXPORT_Props'].objects)+extra:
 if o.type not in ('MESH','CURVE') or o.name.startswith('DOOR_'):continue
 n=o.name
 if n.startswith(('WALL_','LAB_','CEILING_SLAB')):g='lab_estrutura'
 elif n.startswith('FLOOR_') and 'HOSE' not in n:g='lab_piso'
 elif n.startswith('PLACEHOLDER_'):g='lab_vasos'
 elif any(x in n for x in ('FAN','VENT','DUCT','PIPE','CONDUIT')):g='lab_ventilacao'
 elif n.startswith(('LIGHT_','LED_')):g='lab_leds'
 elif 'RACK' in n:g='lab_racks'
 else:g='lab_equipamentos'
 groups.setdefault(g,[]).append(o)
# All 54 plants use 18 shared meshes.
seen={}
for o in bpy.data.collections['EXPORT_Vegetacao'].objects:
 if o.data.name not in seen:
  name='lab_planta_%02d'%len(seen);seen[o.data.name]=name;groups[name]=[o]
 instances.append({'model':seen[o.data.name],'matrix':[list(row) for row in o.matrix_world]})
# Hinged door authored locally from zero; collision attached later.
door=box('LAB_Door',(.575,0,1.13),(1.15,.055,2.26),bpy.data.materials['STAGE13_RACK_Metal_Escuro_Desgastado']);groups['lab_porta']=[door]
report=json.loads((WORK/'export_report_hd.json').read_text())['models'] if (WORK/'export_report_hd.json').exists() else [];targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
import bmesh,re,subprocess
for name,objects in groups.items():
 if any(m['name']==name for m in report) and (OUT/(name+'.ydr')).exists():continue
 print('GROUP_HD',name,len(objects),flush=True)
 plant=name.startswith('lab_planta');pivot=objects[0].matrix_world.copy() if plant else Matrix.Identity(4)
 root=bpy.data.objects.new(name,None);s.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE
 parts=[];dg=bpy.context.evaluated_depsgraph_get()
 for src in objects:
  mesh=bpy.data.meshes.new_from_object(src.evaluated_get(dg),depsgraph=dg);mesh.transform(pivot.inverted()@src.matrix_world)
  ob=bpy.data.objects.new(name+'_part',mesh);s.collection.objects.link(ob);parts.append(ob)
 bpy.ops.object.select_all(action='DESELECT')
 for ob in parts:ob.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();joined=bpy.context.object
 source_mesh=joined.data;materials=list(source_mesh.materials);completed=[];modelstats=[]
 # Each authored material gets its own UV budget instead of sharing with hundreds of unrelated parts.
 for mi,source_mat in enumerate(materials):
  if source_mat is None or not any(p.material_index==mi for p in source_mesh.polygons):continue
  mesh=source_mesh.copy();bm=bmesh.new();bm.from_mesh(mesh)
  bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=mi],context='FACES');bm.to_mesh(mesh);bm.free()
  ob=bpy.data.objects.new(name+'_'+str(mi),mesh);s.collection.objects.link(ob)
  mat=source_mat.copy();mesh.materials.clear();mesh.materials.append(mat)
  for poly in mesh.polygons:poly.material_index=0
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  for node in list(mat.node_tree.nodes):
   if node.type=='TEX_COORD':
    for link in list(node.outputs['UV'].links):
     uvnode=mat.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map=mesh.uv_layers[0].name if mesh.uv_layers else 'UVMap';mat.node_tree.links.new(uvnode.outputs[0],link.to_socket)
  uv=mesh.uv_layers.new(name='BakeUV');mesh.uv_layers.active=uv
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.002);bpy.ops.object.mode_set(mode='OBJECT')
  label=name+'_'+str(mi);is_sign=source_mat.name.startswith('PLACA_');is_led='LED_rosa' in source_mat.name
  size=2048 if plant else (1024 if is_sign or name=='lab_porta' else 4096)
  if not any(n.type=='TEX_IMAGE' and n.image for n in mat.node_tree.nodes):size=512
  if source_mat.name.startswith('STAGE10_'):size=4096
  ns=mat.node_tree.nodes;ls=mat.node_tree.links;bs=next((n for n in ns if n.type=='BSDF_PRINCIPLED'),None);out=next(n for n in ns if n.type=='OUTPUT_MATERIAL')
  emissive=next(n for n in ns if n.type=='EMISSION');maps={}
  for channel in ('color','normal'):
   if channel=='normal' and (is_sign or is_led):continue
   cached=BAKE/(label+'_'+channel+'.dds')
   if cached.exists():maps[channel]=str(cached);continue
   map_size=min(size,2048) if channel=='normal' else size
   im=bpy.data.images.new(label+'_'+channel,width=map_size,height=map_size,alpha=False)
   if channel=='normal':im.colorspace_settings.name='Non-Color';ls.new(bs.outputs[0],out.inputs['Surface'])
   else:ls.new(emissive.outputs[0],out.inputs['Surface'])
   node=ns.new('ShaderNodeTexImage');node.image=im;ns.active=node
   s.render.bake.normal_g='NEG_Y'
   bpy.ops.object.bake(type='NORMAL' if channel=='normal' else 'EMIT',use_clear=True)
   im.filepath_raw=str(BAKE/(label+'_'+channel+'.png'));im.file_format='PNG';im.save()
   Image.open(im.filepath_raw).convert('RGBA').save(BAKE/(label+'_'+channel+'.dds'),pixel_format='DXT5')
   maps[channel]=str(BAKE/(label+'_'+channel+'.dds'));ns.remove(node);bpy.data.images.remove(im)
  for channel,path in list(maps.items()):
   dest=BAKE/'runtime';dest.mkdir(exist_ok=True)
   target_size=min(size,2048) if channel=='normal' else size
   target_path=dest/Path(path).name
   if not target_path.exists():subprocess.run([str(ROOT/'.downloads/texconv.exe'),'-y','-nologo','-f','BC3_UNORM','-m','0','-w',str(target_size),'-h',str(target_size),'-o',str(dest),str(Path(path).with_suffix('.png'))],check=True,stdout=subprocess.DEVNULL)
   maps[channel]=str(target_path)
  shader='emissive.sps' if is_led else ('default.sps' if is_sign else 'normal_spec.sps')
  gta=create_shader(shader);gta.name=label+'_GTA'
  for channel,sampler in [('color','DiffuseSampler'),('normal','BumpSampler')]:
   if channel in maps and sampler in gta.node_tree.nodes:
    tex=gta.node_tree.nodes[sampler];tex.image=bpy.data.images.load(maps[channel]);tex.texture_properties.embedded=True
  # GTA specular response derived from the authored material, not the diffuse brightness.
  if 'SpecSampler' in gta.node_tree.nodes:
   metal=bs.inputs['Metallic'].default_value;rough=bs.inputs['Roughness'].default_value
   spec=bpy.data.images.new(label+'_spec',width=4,height=4,alpha=False);strength=.12+.35*metal
   spec.generated_color=(strength,strength,strength,1);spec.filepath_raw=str(BAKE/(label+'_spec.png'));spec.file_format='PNG';spec.save()
   Image.open(spec.filepath_raw).convert('RGBA').save(BAKE/(label+'_spec.dds'),pixel_format='DXT5')
   tex=gta.node_tree.nodes['SpecSampler'];tex.image=bpy.data.images.load(str(BAKE/(label+'_spec.dds')));tex.texture_properties.embedded=True
  mesh.materials.clear();mesh.materials.append(gta)
  for old in list(mesh.uv_layers):
   if old.name!='BakeUV':mesh.uv_layers.remove(old)
  mesh.uv_layers[0].name='UVMap 0';mesh_add_missing_uv_maps(mesh);mesh_add_missing_color_attrs(mesh)
  for attr in mesh.color_attributes:attr.data.foreach_set('color_srgb',np.tile(np.array([.45,.45,.45,1],dtype=np.float32),len(attr.data)))
  ob.parent=root;convert_obj_to_model(ob);completed.append(ob);modelstats.append({'material':source_mat.name,'resolution':size,'shader':shader})
  print('MATERIAL_HD',label,source_mat.name,size,flush=True)
 bb=[v.co for v in source_mesh.vertices];lo=[min(v[j] for v in bb) for j in range(3)];hi=[max(v[j] for v in bb) for j in range(3)]
 report.append({'name':name,'lo':lo,'hi':hi,'triangles':sum(len(p.vertices)-2 for p in source_mesh.polygons),'source_objects':len(objects),'materials':modelstats})
 bpy.data.objects.remove(joined,do_unlink=True)
 with export_context_scope(ExportContext(name,ExportSettings(targets=targets))):export_ydr(root).save(OUT,targets)
 (WORK/'export_report_hd.json').write_text(json.dumps({'models':report,'plants':instances},indent=2))
 for ob in completed:bpy.data.objects.remove(ob,do_unlink=True)
 bpy.data.objects.remove(root,do_unlink=True)
 print('EXPORTED_HD',name,flush=True)
print('ALL_EXPORTED_HD',len(report),flush=True)
