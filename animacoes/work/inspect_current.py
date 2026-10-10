import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'deitado_tiro.blend'))
r=bpy.data.objects['GTA_Personagem_Rig'];r.animation_data.action=bpy.data.actions['DEITADO_mira'];bpy.context.scene.frame_set(1)
for b in r.pose.bones:
 if any(s in b.name for s in ('Arm','Clavicle','Hand','Elbow','Spine')):
  print('JOINT',b.name,'parent',b.parent.name if b.parent else '', 'world',tuple(round(v,4) for v in r.matrix_world@b.head),'loc',tuple(round(v,4) for v in b.location),'q',tuple(round(v,4) for v in b.rotation_quaternion))
sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps')
from szio.rpf import open_rpf
a=open_rpf(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V\x64e.rpf')
v=a.open_nested('levels/gta5/vehicles.rpf')
print('VEHICLES_ARCHIVES',list(a.list_dir('levels/gta5')))
if v:
 out=root.parent/'veiculos/work/assets';out.mkdir(parents=True,exist_ok=True)
 for n in v.list_dir(''):
  if n.startswith('rebel2.') or n=='rebel2_hi.yft':
   (out/n).write_bytes(v.read_bytes(n));print('EXTRACT',n)
