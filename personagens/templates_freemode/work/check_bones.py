exec(compile((__import__('pathlib').Path('personagens/templates_freemode/work/build_templates.py')).read_text().split('original=collection')[0],'<probe>','exec'))
a=bpy.data.objects['uppr_015_r'];b=bpy.data.objects['hash_976FBF04']
for bone in b.data.bones:
 if bone.name not in a.data.bones:
  tag=bone.bone_properties.tag
  match=next((x for x in a.data.bones if x.bone_properties.tag==tag),None)
  print('MISSING',bone.name,tag,'match',match.name if match else None)
print('HEADROOT',list(b.matrix_world))
