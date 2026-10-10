import bpy,sys,addon_utils
from pathlib import Path
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parent.parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.sollumz.import_assets(directory=str(root/'animacoes/work/assets'),files=[{'name':'a_m_y_business_01.ydd'}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
for o in bpy.data.objects:
 print('OBJ',o.name,o.type,'PARENT',o.parent.name if o.parent else '',o.sollum_type)
 if o.type=='ARMATURE':
  print('BONES',[(b.name,tuple(round(c,3) for c in b.head_local)) for b in o.data.bones if b.name.startswith('SKEL_')])
 if o.type=='MESH':print('MESH',len(o.data.vertices),[m.name for m in o.data.materials],list(o.matrix_world))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'personagens/donor.blend'))
