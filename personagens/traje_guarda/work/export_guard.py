import bpy,sys,addon_utils,bmesh,json,shutil,copy
import numpy as np
import struct
from pathlib import Path
from mathutils import Matrix
import xml.etree.ElementTree as ET
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import LODLevel
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydd.yddexport import export_ydd
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion
root=Path(__file__).resolve().parents[1];out=root/'exports';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'GUARDA_ESQUELETO_GTA.blend'))
source=bpy.data.objects['GUARDA_MALHA_ORIGINAL'];original_rig=source.parent
for pb in original_rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
source_mesh=source.data.copy();source_mesh.transform(source.matrix_world)
source_weights=[{source.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0} for v in source.data.vertices]
source_triangles=len(source_mesh.polygons)
# Keep a complete native skeleton wrapper and component metadata. Shared body
# bone bind matrices are identical to the Freemode skeleton used by the authoring file.
old_objects=list(bpy.data.objects)
with bpy.data.libraries.load(str(root.parent/'donor.blend'),link=False) as (src,dst):dst.objects=src.objects
imported=[o for o in dst.objects if o]
for o in imported:bpy.context.scene.collection.objects.link(o)
rig=next(o for o in imported if o.name=='a_m_y_business_01');rig.name='guardalab'
donors=[o for o in imported if o.type=='MESH']
for o in old_objects:bpy.data.objects.remove(o,do_unlink=True)
native_materials={o.name:o.data.materials[0].copy() for o in donors}
for row in source_weights:
 for name in row:assert name in rig.data.bones,name
mat=create_shader('ped.sps');mat.name='GUARDA_MATERIAL_ORIGINAL'
for key,name in [('DiffuseSampler','guard_diff'),('BumpSampler','guard_normal'),('SpecSampler','guard_spec')]:
 image=bpy.data.images.load(str(root/'textures'/(name+'.dds')),check_existing=True);image.pack()
 if key!='DiffuseSampler':image.colorspace_settings.name='Non-Color'
 node=mat.node_tree.nodes.get(key);node.image=image;node.texture_properties.embedded=True
for name,value in [('specularIntensityMult',.45),('specularFalloffMult',40),('bumpiness',1)]:
 node=mat.node_tree.nodes.get(name)
 if node:node.set_float(value)
source_mesh.update()
regions=['uppr']*len(source_mesh.polygons)
total=0
for ob in donors:
 kind='uppr' if ob.name=='SKEL_ROOT.003' else 'hidden'
 mesh=source_mesh.copy();bm=bmesh.new();bm.from_mesh(mesh);bm.faces.ensure_lookup_table()
 layer=bm.verts.layers.int.new('source_index')
 for v in bm.verts:v[layer]=v.index
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if regions[f.index]!=kind],context='FACES')
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
 if kind=='hidden':
  v=[bm.verts.new(co) for co in [(0,0,0),(.001,0,0),(0,.001,0)]];bm.faces.new(v)
 bm.verts.ensure_lookup_table();ids=[v[layer] for v in bm.verts];bm.to_mesh(mesh);bm.free()
 if kind!='hidden':total+=len(mesh.polygons)
 reserved=create_shader('ped_default.sps');reserved.name='GUARDA_RESERVED_'+ob.name
 component=mat.copy();component.name='GUARDA_'+ob.name
 # Match the texture names expected by the donor's persistent YMT variation.
 for key in ['DiffuseSampler','BumpSampler','SpecSampler']:
  native=native_materials[ob.name].node_tree.nodes.get(key);node=component.node_tree.nodes.get(key)
  if native and native.image and node and node.image:
   filename=native.image.name.split('.')[0]+'.dds';path=out/filename
   if kind=='hidden':
    color=(0,0,0,0) if key!='BumpSampler' else (128,128,255,255)
    hdr=[124,0x100f,16,16,64,0,0]+[0]*11+[32,0x41,0,32,255,65280,16711680,4278190080]+[0x1000,0,0,0,0]
    path.write_bytes(b'DDS '+struct.pack('<31I',*hdr)+bytes(color)*256)
   else:
    source_name={'DiffuseSampler':'guard_diff','BumpSampler':'guard_normal','SpecSampler':'guard_spec'}[key]
    shutil.copy2(root/'textures'/(source_name+'.dds'),path)
   image=bpy.data.images.load(str(path),check_existing=False);image.name=filename;image.pack()
   if key!='DiffuseSampler':image.colorspace_settings.name='Non-Color'
   node.image=image
 mesh.materials.clear();mesh.materials.append(reserved);mesh.materials.append(component)
 if mesh.uv_layers:mesh.uv_layers[0].name='UVMap 0'
 mesh_add_missing_uv_maps(mesh);mesh_add_missing_color_attrs(mesh)
 for p in mesh.polygons:p.material_index=1;p.use_smooth=True
 for a in mesh.color_attributes:
  for d in a.data:d.color=(1,.21586,0,1) if a.name.endswith('0') else (0,0,0,0)
 ob.data=mesh;ob.vertex_groups.clear()
 for name in sorted({name for i in ids for name in source_weights[i]}|{'SKEL_Pelvis'}):ob.vertex_groups.new(name=name)
 for i,idx in enumerate(ids):
  for name,w in ({'SKEL_Pelvis':1} if kind=='hidden' else source_weights[idx]).items():ob.vertex_groups[name].add([i],w,'REPLACE')
 # Original near mesh remains intact. Copies for distance reduce redundant memory.
 for lod,ratio in [(LODLevel.HIGH,1),(LODLevel.MEDIUM,.15),(LODLevel.LOW,.04),(LODLevel.VERYLOW,.01)]:
  lod_mesh=mesh
  if kind!='hidden' and ratio<1:
   tmp=ob.copy();tmp.data=mesh.copy();bpy.context.scene.collection.objects.link(tmp)
   for mod in list(tmp.modifiers):tmp.modifiers.remove(mod)
   bpy.ops.object.select_all(action='DESELECT');tmp.select_set(True);bpy.context.view_layer.objects.active=tmp
   mod=tmp.modifiers.new('COPIA_DISTANCIA','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name);lod_mesh=tmp.data
   bpy.data.objects.remove(tmp,do_unlink=True)
  ob.sz_lods.get_lod(lod).mesh=lod_mesh
 print('COMPONENT',kind,ob.parent.name,len(mesh.vertices),len(mesh.polygons),flush=True)
assert total==source_triangles,(total,source_triangles)
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
with export_context_scope(ExportContext('guardalab',ExportSettings(targets=targets))):bundle=export_ydd(rig)
txd=try_load_asset(root.parent.parent/'animacoes/work/assets/a_m_y_business_01.ytd');txd.textures.clear()
for d in bundle.main_asset.drawables.values():
 txd.textures.update(d.shader_group.embedded_textures);d.shader_group.embedded_textures.clear()
bundle.save(out,targets);save_asset(txd,targets,out,'guardalab')
for ext in ['yft','ymt']:shutil.copy2(root.parent.parent/'animacoes/work/assets'/('a_m_y_business_01.'+ext),out/('guardalab.'+ext))
meta=ET.parse(root.parent/'exports/peds.meta');items=meta.getroot().find('InitDatas');ped=items[0];ped.find('Name').text='guardalab';ET.indent(meta);meta.write(out/'guardalab_peds.meta',encoding='utf-8',xml_declaration=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'GUARDA_FIVEM.blend'))
roundtrip=try_load_asset(out/'guardalab.ydd');assert len(roundtrip.drawables)==8
assert len(txd.textures)==24
print('GUARD_EXPORT_OK',source_triangles,len(txd.textures),flush=True)
(out/'validation.json').write_text(json.dumps({'original_triangles':source_triangles,'preserved_triangles':total,'drawables':len(roundtrip.drawables),'texture_names':list(txd.textures),'high_lod_preserves_geometry':True,'distant_lod_ratios':[.15,.04,.01]},indent=2))
