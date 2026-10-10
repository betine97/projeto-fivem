import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
print('PROPS',list(bpy.ops.sollumz.import_assets.get_rna_type().properties.keys()))
bpy.ops.sollumz.import_assets(directory=str(root/'assets'),files=[{'name':'a_m_y_business_01.ydd'},{'name':'w_ar_carbinerifle.ydr'}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
for o in bpy.data.objects:
 print('OBJ',o.name,o.type)
 if o.type=='ARMATURE':
  print('BONES',[(b.name,tuple(round(v,3) for v in b.head_local)) for b in o.data.bones if b.name.startswith('SKEL_')])
bpy.ops.wm.save_as_mainfile(filepath=str(root.parent/'combate_base.blend'))
for o in bpy.data.objects:
 if o.type=='MESH':
  print('MESHINFO',o.name,'parent',o.parent.name if o.parent else None,'dim',tuple(round(x,2) for x in o.dimensions),'mats',[m.name for m in o.data.materials])
  print('MOD',[(m.type,m.object.name if m.type=='ARMATURE' and m.object else '') for m in o.modifiers])

