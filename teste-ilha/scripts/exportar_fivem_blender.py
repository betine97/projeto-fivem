from pathlib import Path
import sys,json,bpy,numpy as np,addon_utils
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];R=P.parent
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz']
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import SollumType
from Sollumz.tools.drawablehelper import convert_obj_to_model
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from Sollumz.ydr.ydrexport import export_ydr
from szio.gta5 import AssetTarget,AssetFormat,AssetVersion
bpy.ops.wm.open_mainfile(filepath=str(P/'teste-ilha.blend'));scene=bpy.context.scene
meta=json.loads((P/'dados/medidas.json').read_text());grid=np.load(P/'dados/terreno.npz')['terrain'];rows=[]
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
def shader(name):
 m=create_shader('default.sps');m.name=name;n=m.node_tree.nodes['DiffuseSampler'];n.image=bpy.data.images.load(str(P/'nativo/texturas'/f'{name}.dds'));n.image.pack();n.texture_properties.embedded=True;m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],n.inputs['Vector']);return m
def export(name,sources,center,material,uv_bounds=None):
 root=bpy.data.objects.new(name,None);scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE;parts=[]
 for src in sources:
  me=src.data.copy();me.transform(src.matrix_world)
  me.transform(Matrix.Translation(tuple(-v for v in center)))
  me.materials.clear();me.materials.append(material)
  if uv_bounds:
   x0,y0,x1,y1=uv_bounds;uv=me.uv_layers[0];uv.name='UVMap 0'
   for lp in me.loops:
    v=me.vertices[lp.vertex_index].co;uv.data[lp.index].uv=((v.x+center[0]-x0)/(x1-x0),(v.y+center[1]-y0)/(y1-y0))
  mesh_add_missing_uv_maps(me);mesh_add_missing_color_attrs(me)
  for attr in me.color_attributes:attr.data.foreach_set('color_srgb',np.tile(np.array([1,1,1,1],np.float32),len(attr.data)))
  o=bpy.data.objects.new(name+'_mesh',me);scene.collection.objects.link(o);o.parent=root;convert_obj_to_model(o);parts.append(o)
 with export_context_scope(ExportContext(name,ExportSettings(targets=targets))):export_ydr(root).save(P/'nativo/ydr',targets)
 for o in parts:bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.objects.remove(root,do_unlink=True)
for tile in meta['tiles']:
 x0,y0,x1,y1=tile['grid_bounds'];a=grid[y0,x0];b=grid[y1,x1];center=[float((a[0]+b[0])/2),float((a[1]+b[1])/2),0];mat=shader(tile['name']);row={'name':tile['name'],'center':center,'grid_bounds':tile['grid_bounds']}
 for suffix in ['','_MED','_LOW','_VLOW']:export(tile['name']+suffix,[bpy.data.objects[tile['name']+suffix]],center,mat,[a[0],a[1],b[0],b[1]])
 rows.append(row);print('NATIVE_SECTOR_EXPORTED',tile['name'],flush=True)
for name,key,objs in [('ti_pista','ti_asfalto',[o for o in bpy.data.collections['03_PISTA_POUSO'].objects if 'pouso simples' in o.name]),('ti_sinalizacao','ti_faixas',[o for o in bpy.data.collections['03_PISTA_POUSO'].objects if 'pouso simples' not in o.name])]:
 export(name,objs,[0,0,0],shader(key));rows.append({'name':name,'center':[0,0,0],'runway':True})
(P/'nativo/modelos.json').write_text(json.dumps(rows,indent=2));print('NATIVE_BLENDER_EXPORT_READY',len(rows),flush=True)
