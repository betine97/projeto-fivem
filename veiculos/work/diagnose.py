import bpy, sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
from szio.gta5 import try_load_asset
for path in [root/'work/assets/rebel2.yft',root/'exports/sertao.yft']:
 a=try_load_asset(path)
 print('ASSET',path.name,'textures',[(t.name,t.width,t.height) for t in a.drawable.shader_group.embedded_textures.values()])
 print('PHYS_FIELDS',list(a.physics.__dataclass_fields__))
 for c in a.physics.lod1.children:
  if c.drawable and c.drawable.models: print('CHILD',c.bone_tag,{str(k):len(v) for k,v in c.drawable.models.items()})
for fn in ['work/donor.blend','sertao.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(root/fn))
 for o in bpy.data.objects:
  if o.type=='MESH' and ('wheel' in o.name or o.name in ['Caixa municao','Grade base']):
   print('OBJECT',fn,o.name,'hidden',o.hide_render,'props',[(k,str(v)) for k,v in o.items()],'constraints',[(c.type,getattr(c,'subtarget','')) for c in o.constraints])
   print('UV',[(u.name,min(v.uv.x for v in u.data),max(v.uv.x for v in u.data)) for u in o.data.uv_layers])
   print('MATERIAL',[(m.name,m.shader_properties.filename) for m in o.data.materials if m])
   if o.name=='wheel_lf.child':
    from Sollumz.sollumz_properties import LODLevel
    print('WHEEL_LODS',[(str(l),str(o.sz_lods.get_lod(l).mesh)) for l in LODLevel],o.parent.name)
