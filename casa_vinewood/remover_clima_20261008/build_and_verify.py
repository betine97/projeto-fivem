"""Remove the climate MLO, restore original structural collision, retain current lights.

This script stages and verifies files only. Installation is a separate step.
"""
import sys, json, shutil, hashlib, math
from pathlib import Path
from dataclasses import fields, is_dataclass
from enum import Enum
from collections import Counter

P=Path(__file__).resolve().parent; R=P.parents[1]
D=R/'server-data/resources/cidade_mansao'
B=R/'casa_vinewood/clima_interior_20261008/backup'
O=P/'package'; O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset,save_asset,AssetTarget,AssetFormat,AssetVersion
from szio.gta5.archetypes import ArchetypeType
from szio.gta5.entities import EntityMloInstance
from szio.gta5.bounds import AssetBoundComposite,AssetBoundBvh
import pymateria.gta5.gen8 as pmg8

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def equal(a,b):
    if isinstance(a,np.ndarray):return np.array_equal(a,b)
    if is_dataclass(a):
        return type(a)==type(b) and all(equal(getattr(a,f.name),getattr(b,f.name)) for f in fields(a) if f.name!='user_metadata')
    if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if isinstance(a,Enum):return a==b
    if isinstance(a,(float,np.floating)):return math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-7)
    try:return bool(a==b)
    except ValueError:return bool(np.array_equal(a,b))
def graphics(a,b):
    assert a.models.keys()==b.models.keys()
    for lod in a.models:
        assert len(a.models[lod])==len(b.models[lod])
        for x,y in zip(a.models[lod],b.models[lod]):
            assert len(x.geometries)==len(y.geometries)
            for gx,gy in zip(x.geometries,y.geometries):
                assert np.array_equal(gx.vertex_buffer,gy.vertex_buffer)
                assert np.array_equal(gx.index_buffer,gy.index_buffer)
    assert a.shader_group.embedded_textures.keys()==b.shader_group.embedded_textures.keys()
    for k,t in a.shader_group.embedded_textures.items():assert t.data.read_bytes()==b.shader_group.embedded_textures[k].data.read_bytes()
    assert equal(a.shader_group.shaders,b.shader_group.shaders)
def triangles(b):
    if isinstance(b,AssetBoundComposite):return sum(triangles(c) for c in b.children if c)
    if isinstance(b,AssetBoundBvh):return len(b.geometry_primitives)
    return 0
def collision_equal(a,b):
    assert type(a)==type(b)
    if isinstance(a,AssetBoundComposite):
        assert len(a.children)==len(b.children)
        for x,y in zip(a.children,b.children):
            if x is not None:collision_equal(x,y)
            else:assert y is None
    elif isinstance(a,AssetBoundBvh):
        def surfaces(bound):
            out=Counter()
            for tri in bound.geometry_primitives:
                assert len(tri.vertices)==3
                points=tuple(tuple(round(float(v),4) for v in bound.geometry_vertices[i].co) for i in tri.vertices)
                # Allow cyclic indexing changes, preserve triangle winding.
                points=min(points,points[1:]+points[:1],points[2:]+points[:2])
                mat=tuple(getattr(tri.material,f.name) for f in fields(tri.material))
                out[(points,mat)]+=1
            return out
        assert surfaces(a)==surfaces(b),'Collision surfaces, winding or materials changed'
    for f in fields(a):
        if f.name in ['user_metadata','children','geometry_vertices','geometry_primitives']:continue
        assert equal(getattr(a,f.name),getattr(b,f.name)),f'Bound property changed: {f.name}'
def differences(a,b,path='',limit=8):
    if equal(a,b):return []
    if is_dataclass(a):
        out=[]
        for f in fields(a):
            if f.name=='user_metadata':continue
            out+=differences(getattr(a,f.name),getattr(b,f.name),path+'.'+f.name)
            if len(out)>=limit:break
        return out[:limit]
    if isinstance(a,(tuple,list)) and len(a)==len(b):
        out=[]
        for i,(x,y) in enumerate(zip(a,b)):
            out+=differences(x,y,path+f'[{i}]')
            if len(out)>=limit:break
        return out[:limit]
    return [dict(field=path,after=repr(a)[:250],before=repr(b)[:250])]

removed=['clima_client.lua','clima_shared.lua','clima_interior.json','clima_interior.xml','stream/mansao_teto.ybn']
restored=['stream/'+n for n in ['cidade_mansao.ymap','cidade_mansao.ytyp','mansao_paredes.ydr','mansao_pisos.ydr','mansao_escada.ydr']]
changed=restored+['stream/mansao_teto.ydr','fxmanifest.lua','README.md']
baseline={f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()}
if (P/'baseline.json').exists():
    previous=json.loads((P/'baseline.json').read_text())
    conflicts=[rel for rel in changed+removed if previous.get(rel)!=baseline.get(rel)]
    # Other chat added an independent wine cabinet while this package was staged.
    # Accept only appended manifest lines; never replace a changed native asset.
    if conflicts:
        assert conflicts==['fxmanifest.lua'],f'Concurrent edits to rollback targets: {conflicts}'
        saved=(P/'backup_before_removal/fxmanifest.lua').read_text(encoding='utf-8').rstrip()
        assert (D/'fxmanifest.lua').read_text(encoding='utf-8').startswith(saved)
        revision=P/'backup_before_removal/fxmanifest_before_wine_cabinet.lua'
        if not revision.exists():shutil.copy2(P/'backup_before_removal/fxmanifest.lua',revision)
        shutil.copy2(D/'fxmanifest.lua',P/'backup_before_removal/fxmanifest.lua')
(P/'baseline.json').write_text(json.dumps(baseline,indent=2))
backup=P/'backup_before_removal'
for rel in changed+removed:
    dst=backup/rel;dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():shutil.copy2(D/rel,dst)
    assert sha(dst)==baseline[rel]

current_map=try_load_asset(D/'stream/cidade_mansao.ymap')
old_map=try_load_asset(B/'stream/cidade_mansao.ymap')
assert len(current_map.entities)==len(old_map.entities)==6
for a,b in zip(current_map.entities,old_map.entities):
    for f in fields(b):assert equal(getattr(a,f.name),getattr(b,f.name)),f'Newer map entity field differs: {f.name}'
assert isinstance(next(e for e in current_map.entities if str(e.archetype_name)=='mansao_teto'),EntityMloInstance)

current_typ=try_load_asset(D/'stream/cidade_mansao.ytyp')
old_typ=try_load_asset(B/'stream/cidade_mansao.ytyp')
assert len(current_typ.archetypes)==len(old_typ.archetypes)
for a,b in zip(current_typ.archetypes,old_typ.archetypes):
    if str(a.name)!='mansao_teto':assert equal(a,b),'Newer archetype differs'

for rel in restored:
    dst=O/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/rel,dst)
roof=try_load_asset(D/'stream/mansao_teto.ydr')
old_roof=try_load_asset(B/'stream/mansao_teto.ydr')
assert roof.bounds is None and old_roof.bounds is not None
assert len(roof.lights)==68,'Unexpected lighting revision; inspect before restoring'
roof.bounds=old_roof.bounds
# Preserve native shader hashes and all other current drawable fields directly.
# A high-level re-export can hash unresolved shader names a second time.
for name in ['mansao_paredes','mansao_pisos','mansao_escada','mansao_teto']:
    now=pmg8.Drawable.import_rsc(D/'stream'/f'{name}.ydr').result
    reference=pmg8.Drawable.import_rsc(B/'stream'/f'{name}.ydr').result
    assert now.bound is None and reference.bound is not None
    now.bound=reference.bound
    pmg8.Drawable.export_rsc(now,O/'stream'/f'{name}.ydr')

fx=(D/'fxmanifest.lua').read_text(encoding='utf-8')
climate_block="""-- Local indoor climate: real MLO rooms and structural collision, no global weather override.
files { 'clima_interior.json', 'clima_interior.xml' }
data_file 'TIMECYCLEMOD_FILE' 'clima_interior.xml'
client_script 'clima_shared.lua'
client_script 'clima_client.lua'
"""
assert fx.count(climate_block)==1
fx=fx.replace(climate_block,'-- Climate protection postponed: standard map entities and embedded structural collision.\n')
assert 'clima_' not in fx and 'TIMECYCLEMOD_FILE' not in fx
(O/'fxmanifest.lua').write_text(fx,encoding='utf-8')
readme=(D/'README.md').read_text(encoding='utf-8')
start=readme.index('## Proteção contra chuva e névoa — 08/10/2026')
end=readme.index('## Iluminação permanente de todos os ambientes — 08/10/2026',start)
readme=readme[:start]+'''## Proteção climática removida — 08/10/2026

A pedido do usuário, a proteção contra chuva e névoa foi retirada para investigar o crash ao entrar/aproximar-se da mansão. O teto voltou a ser uma entidade BASE, sem salas ou portais MLO. A colisão original de paredes, pisos, escada e teto foi restaurada nos drawables. O YBN local do MLO e os scripts/configurações de clima foram retirados do recurso; suas cópias permanecem no backup desta revisão.

A proteção climática fica para uma revisão futura. A iluminação permanente, móveis, bar, portas e posições salvas no editor permanecem preservados. Recarregue o recurso no servidor, feche completamente o FiveM e conecte novamente antes de testar `mansao` no F8. A confirmação de estabilidade no jogo ainda está pendente.

Pacote, backup e verificações: `casa_vinewood/remover_clima_20261008/`.

'''+readme[end:]
readme=readme.replace('O teto MLO agora contém 68 luzes nativas constantes','O drawable do teto contém 68 luzes nativas constantes')
readme=readme.replace('colisões e proteção climática. Avaliação','colisões da revisão de iluminação. A proteção climática foi removida posteriormente conforme a seção acima. Avaliação')
(O/'README.md').write_text(readme,encoding='utf-8')

collision={}
for name in ['mansao_paredes','mansao_pisos','mansao_escada','mansao_teto']:
    before=try_load_asset(D/'stream'/f'{name}.ydr')
    reference=try_load_asset(B/'stream'/f'{name}.ydr')
    after=try_load_asset(O/'stream'/f'{name}.ydr')
    graphics(before,after)
    collision_equal(after.bounds,reference.bounds)
    assert equal(after.lights,before.lights),f'Lights changed: {name}'
    collision[name]=triangles(after.bounds)
assert sum(collision.values())==14928
assert all(a.type!=ArchetypeType.MLO for a in try_load_asset(O/'stream/cidade_mansao.ytyp').archetypes)
assert all(not isinstance(e,EntityMloInstance) for e in try_load_asset(O/'stream/cidade_mansao.ymap').entities)
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from luaparser import ast
ast.parse(fx)
report={'changed':changed,'removed':removed,'collision_triangles':collision,'native_lights_preserved':68,
    'map_and_archetypes_restored_byte_for_byte':True,'native_mlo_removed':True,'mesh_materials_textures_preserved':True,
    'embedded_collision_matches_pre_climate_backup':True,'manifest_syntax_valid':True,'in_game_verified':False}
(P/'verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
