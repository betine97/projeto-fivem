"""Bake authored Blender colors to UV atlases and export native GTA drawables."""
import bpy,sys,json,math,struct,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'laboratorio_fivem';OUT=WORK/'exports';BAKE=WORK/'bakes';BAKE.mkdir(exist_ok=True)
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
for o in bpy.data.collections['LOD_Vegetacao_Rascunho'].objects:
 if o.data.name not in seen:
  name='lab_planta_%02d'%len(seen);seen[o.data.name]=name;groups[name]=[o]
 instances.append({'model':seen[o.data.name],'matrix':[list(row) for row in o.matrix_world]})
# Hinged door authored locally from zero; collision attached later.
door=box('LAB_Door',(.575,0,1.13),(1.15,.055,2.26),bpy.data.materials['STAGE13_RACK_Metal_Escuro_Desgastado']);groups['lab_porta']=[door]
report=[];targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
for name,objects in groups.items():
 print('GROUP',name,len(objects),flush=True)
 copies=[];plant=name.startswith('lab_planta');pivot=objects[0].matrix_world.copy() if plant else Matrix.Identity(4)
 dg=bpy.context.evaluated_depsgraph_get()
 for src in objects:
  mesh=bpy.data.meshes.new_from_object(src.evaluated_get(dg),depsgraph=dg);mesh.transform(pivot.inverted()@src.matrix_world)
  ob=bpy.data.objects.new(name+'_part',mesh);s.collection.objects.link(ob);copies.append(ob)
 bpy.ops.object.select_all(action='DESELECT')
 for ob in copies:ob.select_set(True)
 bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=name+'_model'
 # Atlas UVs are independent from the source UV maps used by the material graphs.
 for mat in ob.data.materials:
  if mat and mat.use_nodes:
   for node in mat.node_tree.nodes:
    if node.type=='TEX_COORD':
     for link in list(node.outputs['UV'].links):
      uvnode=mat.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map=ob.data.uv_layers[0].name if ob.data.uv_layers else 'UVMap';mat.node_tree.links.new(uvnode.outputs[0],link.to_socket)
 uv=ob.data.uv_layers.new(name='BakeUV');ob.data.uv_layers.active=uv
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.006);bpy.ops.object.mode_set(mode='OBJECT')
 size=512 if plant or name=='lab_porta' else 2048
 im=bpy.data.images.new(name+'_color',width=size,height=size,alpha=False)
 for mat in ob.data.materials:
  node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.nodes.active=node
 bpy.ops.object.bake(type='EMIT',use_clear=True)
 im.filepath_raw=str(BAKE/(name+'.png'));im.file_format='PNG';im.save()
 # Native DDS storage, preserving the baked albedo.
 Image.open(BAKE/(name+'.png')).convert('RGBA').save(BAKE/(name+'.dds'),pixel_format='DXT5')
 material=create_shader('default.sps');material.name=name+'_GTA';tex=material.node_tree.nodes['DiffuseSampler'];tex.image=bpy.data.images.load(str(BAKE/(name+'.dds')));tex.texture_properties.embedded=True
 ob.data.materials.clear();ob.data.materials.append(material)
 for p in ob.data.polygons:p.material_index=0
 for old in list(ob.data.uv_layers):
  if old.name!='BakeUV':ob.data.uv_layers.remove(old)
 ob.data.uv_layers[0].name='UVMap 0';mesh_add_missing_uv_maps(ob.data);mesh_add_missing_color_attrs(ob.data)
 for attr in ob.data.color_attributes:
  attr.data.foreach_set('color_srgb',np.tile(np.array([1,1,1,1],dtype=np.float32),len(attr.data)))
 root=bpy.data.objects.new(name,None);s.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE;ob.parent=root;convert_obj_to_model(ob)
 with export_context_scope(ExportContext(name,ExportSettings(targets=targets))):export_ydr(root).save(OUT,targets)
 bb=[v.co for v in ob.data.vertices];lo=[min(v[j] for v in bb) for j in range(3)];hi=[max(v[j] for v in bb) for j in range(3)]
 report.append({'name':name,'lo':lo,'hi':hi,'triangles':sum(len(p.vertices)-2 for p in ob.data.polygons),'source_objects':len(objects)})
 (WORK/'export_report.json').write_text(json.dumps({'models':report,'plants':instances},indent=2))
 bpy.data.objects.remove(ob,do_unlink=True);bpy.data.objects.remove(root,do_unlink=True)
 print('EXPORTED',name,flush=True)
print('ALL_EXPORTED',len(report),flush=True)
