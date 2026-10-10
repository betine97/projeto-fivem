from locate import *
for f in (P/'stream').glob('*.ydr'):
 a=try_load_asset(f);print(f.name,[(g.shader_index,len(g.vertex_buffer),len(g.index_buffer)//3) for m in a.models[LodLevel.HIGH] for g in m.geometries]);print('lights',len(a.lights),'tex',[(k,t.width,t.height) for k,t in a.shader_group.embedded_textures.items()])
