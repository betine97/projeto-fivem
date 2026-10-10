from locate import *
a=try_load_asset(P/'stream/hc_mobiliario_0.ydr')
for i,s in enumerate(a.shader_group.shaders):
 if any(str(p.value)=='hc_signs' for p in s.parameters):
  for m in a.models[LodLevel.HIGH]:
   for g in m.geometries:
    if g.shader_index==i:print(g.vertex_buffer[['Position','TexCoord0']][:12])
