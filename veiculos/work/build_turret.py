"""Export movable gun separately, with an explicit shared texture dictionary."""
import bpy,sys,json
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parent.parent;out=root/'exports'
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import SollumType,LODLevel
from Sollumz.yft.yftexport import export_yft
from Sollumz.ydr.ydrexport import export_ydr
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion,Archetype,ArchetypeType,ArchetypeAssetType,AssetMapTypes
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
bpy.ops.wm.open_mainfile(filepath=str(root/'sertao.blend'))
rig=bpy.data.objects['sertao']
gun=bpy.data.objects.new('sertao_torre',None);bpy.context.collection.objects.link(gun)
gun.sollum_type=SollumType.DRAWABLE
pivot=Vector((0,-1.15,1.61))
for o in list(bpy.data.objects):
 if o.type!='MESH':continue
 if not any(g.name=='sertao_turret_pitch' for g in o.vertex_groups):continue
 o.parent=gun;o.modifiers.clear();o.vertex_groups.clear();o.constraints.clear()
 seen=set()
 for level in LODLevel:
  mesh=o.sz_lods.get_lod(level).mesh
  if mesh is not None and mesh.name not in seen:
   mesh.transform(Matrix.Translation(-pivot));seen.add(mesh.name)
# The original gun is now a separate drawable: no static duplicate inside the YFT.
with export_context_scope(ExportContext('sertao_torre',ExportSettings(targets=targets))):
 export_ydr(gun).save(out,targets)
with export_context_scope(ExportContext('sertao',ExportSettings(targets=targets))):
 export_yft(rig).save(out,targets)
# Shared YTD includes donor cabin maps and every new material, including wheel children.
txd=try_load_asset(root/'work/assets/rebel2.ytd')
if (root/'work/assets/bobcatxl.ytd').exists():
 txd.textures.update(try_load_asset(root/'work/assets/bobcatxl.ytd').textures)
for name in ['sertao.yft','sertao_hi.yft','sertao_torre.ydr']:
 a=try_load_asset(out/name);d=a.drawable if name.endswith('yft') else a
 txd.textures.update(d.shader_group.embedded_textures)
save_asset(txd,targets,out,'sertao')
save_asset(txd,targets,out,'sertao_torre')
archetype=Archetype(name='sertao_torre',type=ArchetypeType.BASE,flags=32,lod_dist=180,special_attribute=0,hd_texture_dist=50,texture_dictionary='sertao_torre',clip_dictionary='',drawable_dictionary='',physics_dictionary='',bb_min=Vector((-.52,-.59,-.39)),bb_max=Vector((.25,2.14,.31)),bs_center=Vector((-.13,.77,-.04)),bs_radius=1.50,asset_name='sertao_torre',asset_type=ArchetypeAssetType.DRAWABLE,extensions=[])
save_asset(AssetMapTypes(name='sertao_props',archetypes=[archetype]),targets,out,'sertao_props')
gun.location=pivot
rig['turret_functional']=True
bpy.ops.wm.save_as_mainfile(filepath=str(root/'sertao_funcional.blend'))
print('TURRET_EXPORT_OK',len(txd.textures),'textures')
