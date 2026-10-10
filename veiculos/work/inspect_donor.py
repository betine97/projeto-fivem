import sys,bpy,json
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
import addon_utils
addon_utils.enable('Sollumz',default_set=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.sollumz.import_assets(directory=str(root/'assets'),files=[{'name':'rebel2.yft'}])
for o in bpy.data.objects:
 print('OBJ',o.name,o.type,str(o.sollum_type),'parent',o.parent.name if o.parent else '', 'bone',o.parent_bone,'dim',tuple(round(x,3) for x in o.dimensions))
 if o.type=='MESH':print('MATS',[(m.name if m else '') for m in o.data.materials],'VGS',[g.name for g in o.vertex_groups])
 if o.type=='ARMATURE':print('BONES',[(b.name,tuple(round(v,3) for v in b.head_local)) for b in o.data.bones])
bpy.ops.wm.save_as_mainfile(filepath=str(root/'donor.blend'))
