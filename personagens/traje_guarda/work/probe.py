import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
for file,rig_name in [(root/'donor.blend','a_m_y_business_01'),(root/'templates_freemode/01_BASE_ROUPAS.blend','MP_M_FREEMODE_01_RIG')]:
 bpy.ops.wm.open_mainfile(filepath=str(file));r=bpy.data.objects[rig_name]
 print(file.name,'bones',len(r.data.bones))
 for b in r.data.bones:
  if b.name in ['SKEL_Pelvis','SKEL_Spine2','SKEL_L_UpperArm','SKEL_L_Forearm','SKEL_L_Hand','SKEL_L_Thigh','SKEL_L_Calf','SKEL_L_Foot','SKEL_Head','SKEL_Neck_1']:print(b.name,tuple(b.head_local),tuple(b.tail_local))
