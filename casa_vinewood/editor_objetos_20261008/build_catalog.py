"""Convert movable YMAP props into a stable script-owned catalogue, once.
Only the camera-only world triangles duplicated by these props are removed.
The originals and hashes are retained for rollback and exact verification.
"""
import sys, json, math, shutil, hashlib
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent; R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion
from szio.gta5.bounds import BoundPrimitive
D=R/'server-data/resources/cidade_mansao'; B=P/'backup'; O=P/'package'; O.mkdir(exist_ok=True)
if not B.exists():
    shutil.copytree(D,B)
    (P/'baseline.json').write_text(json.dumps({str(f.relative_to(D)):hashlib.sha256(f.read_bytes()).hexdigest() for f in D.rglob('*') if f.is_file()},indent=2))
S=B/'stream'; targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
protect={'mansao_paredes','mansao_pisos','mansao_escada','mansao_teto','mansao_vidros','mansao_pendentes','mansao_spots_led','mansao_spot_embutido','mansao_cozinha_parede','mansao_porta_madeira_095'}
labels={'mansao_mobiliario':'Sofa, chaise e mesa de centro','mansao_jantar':'Mesa de jantar, cadeiras e decoracao','mansao_ilha':'Ilha e banquetas','mansao_tv':'Painel e console de TV','mansao_tapete_sala':'Tapete da sala','mansao_vaso_folhagem':'Vaso com folhagem','mansao_piano_cauda':'Piano de cauda','mansao_tapete_urso':'Tapete de urso','mansao_tapete_classico':'Tapete classico'}
archetypes={}
for f in S.glob('*.ytyp'):
    for a in try_load_asset(f).archetypes: archetypes[str(a.name)]=a
cfg=json.loads((B/'decoracao_iluminacao.json').read_text(encoding='utf-8-sig'))
native={}
for a in cfg['paintings']: native[a['model']]=(a['bounds']['lo'],a['bounds']['hi'])
for a in cfg['plants']:
    x,y,z=a['position']; l=a['footprint']; sc=a['scale']
    native[a['model']]=([(l[0]-x)/sc,(l[1]-y)/sc,(a['floor_z']-z)/sc],[(l[2]-x)/sc,(l[3]-y)/sc,(a['floor_z']-z+a['height_m'])/sc])
catalog=[]; maps={}
for name in ['cidade_mansao','mansao_decoracao','mansao_vasos_autorais','mansao_referencias','mansao_cozinha_completa','mansao_piano_tapetes']:
    if not (S/(name+'.ymap')).exists():
        shutil.copy2(D/'stream'/(name+'.ymap'),S/(name+'.ymap'))
        shutil.copy2(D/'stream'/(name+'.ytyp'),S/(name+'.ytyp'))
        for ar in try_load_asset(S/(name+'.ytyp')).archetypes: archetypes[str(ar.name)]=ar
    a=try_load_asset(S/(name+'.ymap')); keep=[]
    for i,e in enumerate(a.entities):
        model=str(e.archetype_name)
        if model in protect: keep.append(e); continue
        q=list(e.rotation); assert abs(q[1])+abs(q[2])<1e-6
        heading=math.degrees(-2*math.atan2(q[3],q[0]))%360
        ar=archetypes.get(model); lo,hi=(list(ar.bb_min),list(ar.bb_max)) if ar else native[model]
        catalog.append(dict(id=f'{name}:{i}',model=model,label=labels.get(model,'Quadro' if 'artwall' in model or 'quadro' in model else 'Vaso de planta'),
            p=list(e.position),h=heading,s=[float(e.scale_xy),float(e.scale_xy),float(e.scale_z)],lo=lo,hi=hi,lod=float(e.lod_dist)))
    maps[name]={'before':len(a.entities),'after':len(keep)}; a.entities=keep
    save_asset(a,targets,O,name)
# Remove matching embedded furniture collider triangles from the fixed camera YBN.
origin=np.array(json.loads((R/'casa_vinewood/medidas_estudo.json').read_text())['native_origin'])
def triangles(bound,offset):
    if hasattr(bound,'children'):
        for c in bound.children:
            if c is not None: yield from triangles(c,offset)
    elif hasattr(bound,'geometry_primitives'):
        for t in bound.geometry_primitives:
            if len(t.vertices)!=3: continue
            yield t,np.array([bound.geometry_vertices[i].co for i in t.vertices])+offset
def key(points):
    # Current native quantisation can differ slightly between local and world bounds.
    return tuple(sorted(tuple(round(float(v),2) for v in p) for p in points))
remove=Counter()
for model in ['mansao_mobiliario','mansao_jantar','mansao_ilha','mansao_tv']:
    asset=try_load_asset(S/(model+'.ydr'))
    if asset.bounds:
        remove.update(key(p) for _,p in triangles(asset.bounds,origin))
world=try_load_asset(S/'cidade_mansao.ybn'); removed=0; original=0
for bound in world.children:
    keep=[]
    for t,p in triangles(bound,np.zeros(3)):
        original+=1; k=key(p)
        if remove[k]>0: remove[k]-=1; removed+=1
        else: keep.append(t)
    bound.geometry_primitives=keep
save_asset(world,targets,O,'cidade_mansao')
assert removed>0
for name in maps:
    assert len(try_load_asset(O/(name+'.ymap')).entities)==maps[name]['after']
assert sum(m['before']-m['after'] for m in maps.values())==len(catalog)
(O/'objetos_catalogo.json').write_text(json.dumps({'version':1,'objects':catalog,'protectedModels':sorted(protect)},ensure_ascii=False,indent=2),encoding='utf-8')
(P/'catalog_verification.json').write_text(json.dumps({'objects':len(catalog),'maps':maps,'camera_before':original,'camera_removed':removed,'camera_after':original-removed,'unmatched_embedded_triangles':sum(remove.values()),'native_roundtrip':True},indent=2))
print(json.dumps({'objects':len(catalog),'maps':maps,'camera_before':original,'camera_removed':removed,'unmatched':sum(remove.values())},indent=2))
