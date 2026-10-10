"""Reutilizar cinco casas prontas do projeto, com todas as texturas incorporadas."""
from pathlib import Path
import sys,json,copy,struct,re
P=Path(__file__).resolve().parents[2];R=P.parent;O=P/'porto_construido'
for d in ['fontes','exportados','dados','previews','scripts']:(O/d).mkdir(parents=True,exist_ok=True)
D=Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work');sys.path[:0]=[str(D/'deps'),str(R/'laboratorio_fivem/work/pydeps')]
import numpy as np
from szio.gta5 import *
from szio.gta5.bounds import *
from szio.types import Vector,DataSource
src=R/'casa_vinewood/work';tex={}
for path in (src/'textures').glob('*.dds'):tex[path.stem.lower()]=path.read_bytes()
for path in (src/'native').glob('*.ytd'):
    try:
        for name,t in try_load_asset(path).textures.items():tex.setdefault(str(name).lower(),t.data.read_bytes())
    except Exception:pass
keys=[('ch2_09b_hs05',-1.40,.78),('ch2_09c_hs12',-1.6,.76),('ch2_10_hs09',-4.0,.54),('ch2_12_house101',-5.0,.60),('ch2_12_house20',1.0,.53)]
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),);rows=[]
names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',(D/'sollumz/Sollumz/ybn/collision_materials.py').read_text());mat=CollisionMaterial.from_packed(names.index('CONCRETE'))
def bounds(b,lo,hi):
    b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)*.5);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)*.5)
for key,floor,scale in keys:
    a=try_load_asset(src/'native'/(key+'.ydr'));needed=set()
    for s in a.shader_group.shaders:
        s.name=Path(s.preset_filename).stem
        for p in s.parameters:
            if isinstance(p.value,(str,)) and str(p.value):needed.add(str(p.value))
    missing=[]
    for name in needed:
        if name in a.shader_group.embedded_textures:continue
        data=tex.get(name.lower())
        if not data:missing.append(name);continue
        h,w=struct.unpack_from('<II',data,12);a.shader_group.embedded_textures[name]=EmbeddedTexture(name,w,h,DataSource.create(data,name=name+'.dds'))
    if missing:raise RuntimeError('Texturas ausentes '+key+': '+repr(missing))
    v=[];tris=[]
    for m in a.models[LodLevel.HIGH]:
        for g in m.geometries:
            xyz=np.array(g.vertex_buffer['Position']);off=len(v);v.extend(xyz);tris.extend(g.index_buffer.reshape(-1,3)+off)
    v=np.array(v,np.float32);tri=np.array(tris,np.int32);pol=v[tri];area=np.linalg.norm(np.cross(pol[:,1]-pol[:,0],pol[:,2]-pol[:,0]),axis=1)
    tri=tri[(area>1e-8)&(pol[:,:,2].max(1)>floor-.3)]
    b=AssetBoundBvh();b.margin=.003;b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_VEHICLE|CollisionFlags.MAP_TYPE_WEAPON;b.composite_collision_include_flags=CollisionFlags(0xffffffff)
    b.geometry_vertices=[BoundVertex(Vector(p),None) for p in v];b.geometry_primitives=[BoundPrimitive.new_triangle(*(int(i) for i in t),mat) for t in tri]
    lo=v.min(0);hi=v.max(0);bounds(b,lo,hi);c=AssetBoundComposite(children=[b]);bounds(c,lo,hi);a.bounds=c
    a.lod_thresholds={LodLevel.HIGH:200,LodLevel.MEDIUM:450,LodLevel.LOW:850,LodLevel.VERYLOW:1500}
    alias='pe_casa_'+key;save_asset(a,targets,O/'exportados',alias);check=try_load_asset(O/'exportados'/(alias+'.ydr'));assert check.bounds
    for name,t in a.shader_group.embedded_textures.items():(O/'fontes'/(str(name).lower()+'.dds')).write_bytes(t.data.read_bytes())
    rows.append(dict(modelo=alias,original=key,arquivo_blender=str(src/(key+'.blend')),base_piso=floor,escala=scale,bb_min=lo.tolist(),bb_max=hi.tolist(),colisao_triangulos=len(tri),texturas_embutidas=len(a.shader_group.embedded_textures),textures_missing=missing))
    print('CASA_PRONTA_AUTOCONTIDA',key,flush=True)
(O/'dados/casas.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
