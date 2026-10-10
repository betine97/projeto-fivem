from locate import *
for f in N.glob('bh1_lod*slod3*'):
 if f.suffix=='.ydr':
  a=try_load_asset(f);print(f.name,[(k.name,sum(len(g.index_buffer)//3 for m in ms for g in m.geometries)) for k,ms in a.models.items()])
 if f.suffix=='.ydd' and 'emissive' in f.name:print(f.name,list(try_load_asset(f).drawables))
