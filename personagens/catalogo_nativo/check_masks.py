import render_catalog as r
for m in r.DATA['models']:
 if m['part']=='berd' and m['sex']=='male' and ((m['collection'].endswith('_tuner') and m['index']==0) or (m['collection'].endswith('_heist4') and m['index']==3)):
  a=r.try_load_asset(r.vpath(m['path']))
  print(m['collection'])
  for d in a.drawables.values():
   print('embedded',list(d.shader_group.embedded_textures))
   print('diffuse',[p.value for s in d.shader_group.shaders for p in s.parameters if p.name.lower()=='diffusesampler'])
