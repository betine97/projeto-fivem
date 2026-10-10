import hashlib, json, sys
from pathlib import Path
R=Path(__file__).resolve().parents[3]; P=R/'teste-ilha/cayo_perico'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
rows=json.loads((P/'catalogo.json').read_text()); selected=[]
for q in rows:
    arc=q['archive'].split('|')[-1]
    if any(k in arc for k in ('/mph4_island/','/mph4_terrain/','/interiors/dlc_int_0','/interiors/int_placement_h4.rpf','/lodlights.rpf','/props/prop_h4_','/props/high/int_mp_')):
        if any(k in arc for k in ('casino','arcade','/prop_h4_sub.rpf')): continue
        if Path(q['file']).suffix in ('.ymap','.ybn','.ytyp','.ydr','.ytd','.ydd','.yft','.ycd'): selected.append(q)
cache={}; result=[]; size=0
for i,q in enumerate(selected):
    parts=q['archive'].split('|'); key=q['archive']
    if key not in cache:
        ar=open_rpf(parts[0])
        for s in parts[1:]: ar=ar.open_nested(s)
        cache[key]=ar
    data=cache[key].read_bytes(q['file']); name=Path(q['file']).name
    category='mapas' if name.endswith('.ymap') else 'colisoes' if name.endswith('.ybn') else 'assets'
    path=P/'originais'/category/name; path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=data: raise RuntimeError('duplicate differing file: '+name)
    path.write_bytes(data); size+=len(data)
    result.append({**q,'category':category,'name':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    if i%500==0: print('EXTRAINDO',i,'/',len(selected),round(size/2**20),'MiB',flush=True)
(P/'proveniencia.json').write_text(json.dumps(result,indent=2))
print('EXTRAIDOS',len(result),round(size/2**20),'MiB',flush=True)
