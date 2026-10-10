"""Exportar colisões GTA nativas separadas, sem instalar ou mudar o servidor."""
import sys,json,re
from pathlib import Path
P=Path(__file__).resolve().parents[1]
DEPS=Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work')
sys.path[:0]=[str(DEPS/'deps'),str(P.parents[1]/'laboratorio_fivem/work/pydeps')]
import numpy as np
from szio.gta5 import AssetTarget,AssetFormat,AssetVersion,save_asset,try_load_asset
from szio.gta5.bounds import AssetBoundBvh,AssetBoundComposite,BoundVertex,BoundPrimitive,CollisionFlags,CollisionMaterial
from szio.types import Vector
report=json.loads((P/'dados/preparacao_vegetacao_vento.json').read_text(encoding='utf8'))
OUT=P/'nativo/vegetacao_colisoes';OUT.mkdir(parents=True,exist_ok=True)
names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',(DEPS/'sollumz/Sollumz/ybn/collision_materials.py').read_text())
wood=next(n for n in ['WOOD_SOLID_LARGE','WOOD_SOLID_MEDIUM','WOOD_SOLID_SMALL'] if n in names)
mat=CollisionMaterial.from_packed(names.index(wood));targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),);rows=[]
def bounds(b,lo,hi):
    b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)*.5);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)*.5)
for row in report['colisoes']:
    key=row['id'];raw=np.load(P/'dados/colisoes_vegetacao'/(key+'.npz'));v=raw['vertices'];tri=raw['triangulos']
    area=np.linalg.norm(np.cross(v[tri[:,1]]-v[tri[:,0]],v[tri[:,2]]-v[tri[:,0]]),axis=1);tri=tri[area>1e-10]
    b=AssetBoundBvh();b.margin=.003;b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_VEHICLE|CollisionFlags.MAP_TYPE_COVER
    b.composite_collision_include_flags=CollisionFlags(0xffffffff);b.geometry_vertices=[BoundVertex(Vector(p),None) for p in v]
    b.geometry_primitives=[BoundPrimitive.new_triangle(*(int(i) for i in t),mat) for t in tri]
    lo=v.min(0);hi=v.max(0);bounds(b,lo,hi);c=AssetBoundComposite(children=[b]);bounds(c,lo,hi)
    name='pe_veg_'+key;save_asset(c,targets,OUT,name);check=try_load_asset(OUT/(name+'.ybn'))
    assert check and len(check.children)==1 and len(check.children[0].geometry_primitives)==len(tri)
    assert check.children[0].composite_collision_type_flags==b.composite_collision_type_flags
    rows.append(dict(modelo=key,arquivo=(OUT/(name+'.ybn')).relative_to(P).as_posix(),vertices=len(v),triangulos=len(tri),material=wood,reaberto=True,flags_contato=int(b.composite_collision_type_flags),folhas_colidem=False))
    print('YBN_REABERTO',name,len(tri),flush=True)
(P/'dados/colisoes_vegetacao_nativas.json').write_text(json.dumps(dict(arquivos=rows,quantidade=len(rows),instalado=False,validacao_no_jogo=False,observacao='Dicionários de colisão por modelo. Precisam ser associados aos drawables/archetypes e instâncias na integração; este diretório sozinho não é um resource instalável.'),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
