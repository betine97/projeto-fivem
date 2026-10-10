import json
import render_catalog as r
p=r.ROOT/'personagens/catalogo_nativo/lower_expansion_report.json'
d=json.loads(p.read_text(encoding='utf-8'));counts={}
for entry in d['skipped']:
 a=r.try_load_asset(r.vpath(entry['model']['path']))
 tris=sum(len(g.index_buffer)//3 for dr in a.drawables.values() for m in dr.models[min(dr.models)] for g in m.geometries)
 entry['nativeTriangles']=tris
 counts[(entry['reason'],tris>0)]=counts.get((entry['reason'],tris>0),0)+1
 if tris: print('HAS_GEOMETRY',entry['model'],tris,'embedded',list(next(iter(a.drawables.values())).shader_group.embedded_textures))
print('AUDIT',counts)
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
