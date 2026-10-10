import bpy,json,sys,addon_utils
from pathlib import Path
import numpy as np
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\sollumz']
addon_utils.enable('Sollumz',default_set=True)
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'CONJUNTO_COMPLETO.blend'))
report={}
for name in ['CAMISA_ESTAMPADA','REF_TRONCO_015','CALCA_BEGE','REF_PES_DESCALCOS_APT01','MOCASSINS_MARRONS']:
 o=bpy.data.objects[name];a=np.array([v.co[:] for v in o.data.vertices]);info={'bbox':[a.min(0).tolist(),a.max(0).tolist()], 'materials':[],'slices':[]}
 for m in o.data.materials:
  info['materials'].append({'name':m.name,'images':[(n.name,n.image.name,n.image.filepath) for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]})
 for z in ([.0,.1,.2,.3,.4] if 'CAMISA' in name or 'TRONCO' in name else [-.8,-.88,-.92,-.96]):
  b=a[abs(a[:,2]-z)<.02];info['slices'].append([z,b.min(0).tolist(),b.max(0).tolist()] if len(b) else [z])
 report[name]=info
for piece in ['relogio','sapatos']:
 folder=root/piece;cfg=json.loads((folder/'export_config.json').read_text());before=set(bpy.data.objects)
 bpy.ops.sollumz.import_assets(directory=str(folder/'source'),files=[{'name':cfg['component']+'.ydd'}],use_custom_settings=True,dwd_import_external_skeleton='FROM_DIR')
 report[piece+'_donor']=[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None} for o in set(bpy.data.objects)-before]
(root/'work/fit_inspection.json').write_text(json.dumps(report,indent=2))
print('FIT_INSPECTED')
