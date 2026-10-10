import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz')
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from szio.rpf import open_rpf
from szio.gta5 import try_load_asset
r=open_rpf(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\x64e.rpf').open_nested('levels/gta5/vehicles.rpf')
for name in ['vehshare.ytd']:
 if r.exists(name):(root/'work/assets'/name).write_bytes(r.read_bytes(name))
for file in [root/'work/assets/rebel2.ytd',root/'work/assets/vehshare.ytd']:
 if not file.exists():continue
 txd=try_load_asset(file)
 for name,t in txd.textures.items():
  if t.data:
   with t.data.open() as source:(root/'work'/(name+'.dds')).write_bytes(source.read())
bpy.ops.wm.open_mainfile(filepath=str(root/'sertao.blend'))
for name in ['wheel_lf.child','wheel_lf','wheelmesh_lf']:
 o=bpy.data.objects.get(name)
 if o:
  print('WHEEL',name,'loc',tuple(o.location),'world',list(map(list,o.matrix_world)),'constraints',[(c.type,c.subtarget if hasattr(c,'subtarget') else '') for c in o.constraints])
  print('DATA',(tuple(o.data.vertices[0].co) if o.type=='MESH' else ''))
for o in bpy.data.objects:
 if o.type=='MESH' and o.sollum_type=='sollumz_drawable_model':
  print('LOD',o.name,o.sz_lods.active_lod_level)
