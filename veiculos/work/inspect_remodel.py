import bpy
from pathlib import Path
root=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'sertao.blend'))
for name in ['bodyshell','windscreen','bonnet','CAB_ROOF']:
 o=bpy.data.objects.get(name)
 if o:
  print('BOUNDS',name,[(round(min(v.co[i] for v in o.data.vertices),3),round(max(v.co[i] for v in o.data.vertices),3)) for i in range(3)])
  if name=='bodyshell':print('ROOF',sorted(set(tuple(round(c,3) for c in v.co) for v in o.data.vertices if v.co.z>1.22))[:100])
for img in bpy.data.images:
 if any(n in img.name for n in ['MILITARY','grade','glass']):print('IMAGE',img.name,img.colorspace_settings.name,img.filepath)
rig=bpy.data.objects['sertao']
for name in ['boot','bonnet','door_dside_f']:
 b=rig.pose.bones[name];print('POSE',name,'basis',list(map(list,b.matrix_basis)),'rest',list(map(list,b.bone.matrix_local)))
 print('EVAL',name,list(map(list,b.matrix)),[(c.name,c.type) for c in b.constraints])
for name in ['TAILGATE','BED_FLOOR','BED_SIDE_-1']:
 o=bpy.data.objects[name];print('PART',name,'matrix',list(map(list,o.matrix_world)),'bounds',list(o.dimensions),'mesh',[(min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)) for i in range(3)])
