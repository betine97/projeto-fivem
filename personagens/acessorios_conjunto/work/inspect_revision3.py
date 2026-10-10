import bpy,json
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'CONJUNTO_COMPLETO.blend'))
rig=bpy.data.objects['MP_M_FREEMODE_01_RIG']
r={'bones':{b.name:[list(b.head_local),list(b.tail_local)] for b in rig.data.bones if b.name in ['SKEL_L_UpperArm','SKEL_L_Forearm','SKEL_L_Calf','SKEL_L_Foot']}}
for n in ['REF_PERNAS_BERMUDA_014','REF_PES_DESCALCOS_APT01','CALCA_BEGE','CAMISA_ESTAMPADA','REF_TRONCO_015']:
 o=bpy.data.objects[n];a=np.array([v.co[:] for v in o.data.vertices]);rows=[]
 for z in ([-.80,-.85,-.90,-.94,-.97] if 'CAMISA' not in n and 'TRONCO' not in n else [.15,.20,.25,.3,.35,.4]):
  q=a[(abs(a[:,2]-z)<.018)&(a[:,0]>.06)]
  if len(q):rows.append([z,len(q),q.min(0).tolist(),q.max(0).tolist()])
 r[n]={'slices':rows,'groups':[g.name for g in o.vertex_groups]}
(root/'work/inspection_revision3.json').write_text(json.dumps(r,indent=2))
