"""Native GEN8 export with LODs, original texture dictionaries and actual collision."""
from pathlib import Path
import sys,json,copy,math,re,struct,subprocess,hashlib,shutil
O=Path(__file__).resolve().parents[1];P=O.parent;R=P.parent;F=O/'fivem';S=F/'stream';S.mkdir(parents=True,exist_ok=True)
D=Path('C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work');sys.path[:0]=[str(D/'deps'),str(R/'laboratorio_fivem/work/pydeps')]
import numpy as np
from PIL import Image
from szio.gta5 import *
from szio.gta5.drawables import Geometry,Model,ShaderGroup,ShaderInst,ShaderParameter,VertexDataType,RenderBucket
from szio.gta5.bounds import *
from szio.gta5.maps import *
from szio.gta5.entities import *
from szio.gta5.shader import ShaderManager,ShaderParameterType
from szio.types import Vector,Quaternion,DataSource
targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),);textures={};archetypes=[];stats=[];models={};texture_groups={}
terrain_only='--terreno-only' in sys.argv
assets_only='--assets-only' in sys.argv
selected_names=set(sys.argv[sys.argv.index('--names')+1].split(',')) if '--names' in sys.argv else None
default=try_load_asset(P/'fivem/stream/ti_pista.ydr').shader_group.shaders[0]
stock=try_load_asset(P/'amostra_natural/fontes/prop_tree_eucalip_01.ydr')
wind=copy.deepcopy(next(s for s in stock.shader_group.shaders if s.preset_filename=='trees_normal_spec.sps'))
names=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',(D/'sollumz/Sollumz/ybn/collision_materials.py').read_text())
def boundbox(b,v):
    lo=v.min(0);hi=v.max(0);b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)*.5);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)*.5)
def collision(v,tri,material='CONCRETE'):
    b=AssetBoundBvh();b.margin=.002;b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_VEHICLE|CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_COVER;b.composite_collision_include_flags=CollisionFlags(0xffffffff)
    b.geometry_vertices=[BoundVertex(Vector(p),None) for p in v];mat=CollisionMaterial.from_packed(names.index(material))
    pol=v[tri];valid=np.linalg.norm(np.cross(pol[:,1]-pol[:,0],pol[:,2]-pol[:,0]),axis=1)>1e-8
    b.geometry_primitives=[BoundPrimitive.new_triangle(*(int(i) for i in t),mat) for t in tri[valid]];boundbox(b,v);c=AssetBoundComposite(children=[b]);boundbox(c,v);return c
def texture(info):
    if info.get('texture'):name=info['texture'];src=Path(info['file'])
    else:
        # New flat swatches are generated only for procedural materials, never from edits to source PNGs.
        # Blender uses linear BSDF colors. Encode flat authoring swatches in sRGB once.
        rgb=tuple(int(np.clip(v,0,1)**(1/2.2)*255) for v in info['color']);alpha=64 if info.get('transmission',0)>.5 else 255
        name='pe_cor_'+bytes((*rgb,alpha)).hex();src=O/'fontes'/(name+'.png')
        if not src.exists():Image.new('RGBA',(4,4),(*rgb,alpha)).save(src)
    if name in textures:return name
    if src.suffix.lower()=='.dds':path=src
    else:
        path=O/'fontes'/(name+'.dds')
        existing_size=struct.unpack_from('<II',path.read_bytes(),12) if path.exists() else (0,0)
        if not path.exists() or any(v&(v-1) for v in existing_size):
            p=subprocess.run([str(R/'.downloads/texconv.exe'),'-y','-pow2','-f','BC3_UNORM','-m','0','-o',str(O/'fontes'),str(src)],capture_output=True,text=True)
            if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    data=path.read_bytes();h,w=struct.unpack_from('<II',data,12);textures[name]=EmbeddedTexture(name,w,h,DataSource.create(data,name=name+'.dds'));return name
def texture_slot(info,slot):
    if info.get(slot+'_texture'):
        return texture(dict(texture=info[slot+'_texture'],file=info[slot+'_file']))
    # Neutral tangent-space normal and an authored dielectric specular swatch are numeric maps.
    value=(128,128,255,255) if slot=='normal' else (64,64,64,255)
    name='pe_'+slot+'_neutral';src=O/'fontes'/(name+'.png')
    if not src.exists():Image.new('RGBA',(4,4),value).save(src)
    return texture(dict(texture=name,file=str(src)))
def shader_preset(filename):
    definition=ShaderManager.find_shader(filename)
    if not definition:raise RuntimeError('Unknown native shader '+filename)
    params=[]
    for p in definition.parameters:
        val=None if p.type==ShaderParameterType.TEXTURE else Vector(tuple(float(getattr(p,c,None) or 0) for c in 'xyzw'))
        params.append(ShaderParameter(p.name,val))
    return ShaderInst(definition.base_name,filename,RenderBucket(definition.render_bucket),params)
def archetype(name,lo,hi,lod,txd='pe_texturas',flags=32):
    a=Archetype(name,ArchetypeType.BASE,flags,lod,0,lod,txd,'','',name,Vector(lo),Vector(hi),Vector((lo+hi)/2),float(np.linalg.norm(hi-lo)/2),'',ArchetypeAssetType.DRAWABLE,[]);archetypes.append(a);models[name]=dict(bb_min=lo.tolist(),bb_max=hi.tolist(),lod=lod);return a
def shader(info,iswind):
    transparent=info.get('transmission',0)>.5
    s=copy.deepcopy(wind) if iswind else shader_preset('normal_spec_alpha.sps' if transparent else 'normal_spec.sps')
    tx=texture({k:v for k,v in info.items() if k not in ('texture','file')} if transparent else info)
    normal=texture_slot(info,'normal');spec=texture_slot(info,'spec')
    roughness=float(np.clip(info.get('roughness',.8),.08,.98));metallic=float(np.clip(info.get('metallic',0),0,1))
    for p in s.parameters:
        if str(p.name).lower()=='diffusesampler':p.value=tx
        if str(p.name).lower()=='bumpsampler':p.value=normal
        if str(p.name).lower()=='specsampler':p.value=spec
        if str(p.name).lower()=='windglobalparams':p.value=Vector((.20,1.65,1.65,1))
        if str(p.name).lower()=='umglobalparams':p.value=Vector((.025,.02,1,.5))
        if str(p.name).lower()=='bumpiness':p.value=Vector((1,0,0,0))
        if str(p.name).lower()=='specularintensitymult':p.value=Vector((.20 if iswind else .3+metallic*.7,0,0,0))
        if str(p.name).lower()=='specularfalloffmult':p.value=Vector((float(np.clip(2/(roughness*roughness)-2,2,300)),0,0,0))
        if str(p.name).lower()=='specularfresnel':p.value=Vector((.3 if iswind else .75,0,0,0))
    return s
def tangent_vectors(position,normal,uv):
    # Compute in final native UV space (V flipped), including mirrored islands and degenerate UVs.
    pp=position.reshape(-1,3,3);tt=uv.reshape(-1,3,2);e1=pp[:,1]-pp[:,0];e2=pp[:,2]-pp[:,0]
    d1=tt[:,1]-tt[:,0];d2=tt[:,2]-tt[:,0];den=d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0]
    inverse=np.divide(1,den,out=np.zeros_like(den),where=np.abs(den)>1e-9)
    t=(e1*d2[:,1,None]-e2*d1[:,1,None])*inverse[:,None];b=(e2*d1[:,0,None]-e1*d2[:,0,None])*inverse[:,None]
    t=np.repeat(t,3,axis=0);b=np.repeat(b,3,axis=0);t-=normal*np.sum(t*normal,axis=1,keepdims=True)
    lengths=np.linalg.norm(t,axis=1);bad=lengths<1e-8
    fallback=np.cross(normal,np.where((np.abs(normal[:,2])<.9)[:,None],np.array([0,0,1]),np.array([0,1,0])))
    t[bad]=fallback[bad];t/=np.maximum(np.linalg.norm(t,axis=1,keepdims=True),1e-8)
    sign=np.where(np.sum(np.cross(normal,t)*b,axis=1)<0,-1,1)
    return np.c_[t,sign].astype(np.float32)
def geometry(cache,ids,si,iswind):
    dt=np.dtype([('Position','<f4',3),('Normal','<f4',3),('Colour0','u1',4)]+([('Colour1','u1',4)] if iswind else [])+[('TexCoord0','<f4',2),('Tangent','<f4',4)])
    v=np.zeros(len(ids),dt);v['Position']=cache['position'][ids];v['Normal']=cache['normal'][ids];v['TexCoord0']=cache['uv'][ids];v['Colour0']=255
    ao=np.clip(cache.get('ao',np.ones(len(cache['position'])))[ids],0,1);ambient=np.rint(ao*255).astype(np.uint8)
    v['Colour0'][:,0]=ambient;v['Colour0'][:,2]=ambient
    v['Tangent']=tangent_vectors(v['Position'],v['Normal'],v['TexCoord0'])
    if iswind:
        v['Colour0'][:,0]=np.rint(np.clip(cache['weight'][ids],0,1)*128);v['Colour0'][:,1]=np.rint(np.mod(cache['phase'][ids]/math.tau,1)*255);v['Colour0'][:,2]=0
        # Stock leaves reserve Colour0 for wind; Colour1 blue stores ambient occlusion.
        # Filling red/green/alpha white here incorrectly adds artificial lighting to every leaf.
        v['Colour1']=0;v['Colour1'][:,2]=ambient
    geometries=[]
    for start in range(0,len(v),60000):
        part=v[start:start+60000];unique,inv=np.unique(part,return_inverse=True);geometries.append(Geometry(VertexDataType.DEFAULT,unique,inv.astype(np.uint16),np.array([],np.uint16),si))
    return geometries
def native(row,center=None,terrain=False):
    name=row['name'];tree=row.get('tree',False);c=np.load(O/'cache'/(name+'_1.npz' if terrain else name+'.npz'));ca={k:c[k].copy() for k in c.files}
    if center is not None and not terrain:ca['position']-=center
    shaders=[];wmat=[]
    txdname='pe_solo' if terrain else 'pe_porto_texturas' if name.startswith('pe_porto') else name+'_tx'
    group=texture_groups.setdefault(txdname,set())
    for i,info in enumerate(row['materials']):
        iswind=tree and bool(np.any(ca['weight'][ca['material']==i]>.001));shaders.append(shader(info,iswind));wmat.append(iswind)
        group.update(str(p.value) for p in shaders[-1].parameters if isinstance(p.value,str))
    a=AssetDrawable(name=name,shader_group=ShaderGroup(shaders,{}));lods=[LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW];counts={}
    for li,lod in enumerate(lods):
        cc=ca
        if terrain:
            tmp=np.load(O/'cache'/f'{name}_{[1,2,4,8][li]}.npz');cc={k:tmp[k] for k in tmp.files}
        elif name.startswith('pe_estrutura') and li>0:
            tmp=np.load(O/'cache'/f'{name}_LOD{li}.npz');cc={k:tmp[k] for k in tmp.files}
        ge=[]
        for i,info in enumerate(row['materials']):
            tr=np.arange(len(cc['position'])//3).reshape(-1);mask=(cc['material'].reshape(-1,3)[:,0]==i)
            if not terrain and not tree and li>0 and not name.startswith('pe_estrutura'):mask&=cc['exterior'].reshape(-1,3).max(1)>0
            tr=tr[mask]
            if tree and wmat[i]:
                # Preserve complete four-triangle broad leaves; other foliage uses segment groups.
                step=[1,2,4,8][li];groups=np.arange(len(tr))//4;tr=tr[(groups%step)==0]
            if len(tr):ge.extend(geometry(cc,(tr[:,None]*3+np.arange(3)).ravel(),i,wmat[i]))
        mask=sum(1<<b for b in {int(s.render_bucket) for s in shaders});a.models[lod]=[Model(0,ge,mask,False,0,0)];counts[lod.name]=sum(len(g.index_buffer)//3 for g in ge)
    if tree:
        src=P/'porto_esperanca/nativo/vegetacao_colisoes'/(name+'.ybn');a.bounds=try_load_asset(src);dist=[110,230,420,750] if ca['position'][:,2].max()>5 else [55,110,180,260]
    elif terrain:a.bounds=None;dist=[420,850,1800,6500]
    else:
        v=ca.get('collision_vertices');tri=ca.get('collision_triangles')
        if terrain:pass
        elif v is not None and len(v)>0:a.bounds=collision(v,tri)
        else:
            v=ca['position'];tri=np.arange(len(v)).reshape(-1,3);a.bounds=collision(v,tri)
        dist=[180,350,600,1000] if name.startswith('pe_estrutura') else [500,900,1800,4000]
    a.lod_thresholds=dict(zip(lods,dist));save_asset(a,targets,S,name)
    lo=ca['position'].min(0);hi=ca['position'].max(0)
    if not terrain:archetype(name,lo,hi,dist[-1],txdname);models[name]['center']=center.tolist() if center is not None else [0,0,0]
    else:
        worldv=c['collision_vertices'];tri=c['collision_triangles'];save_asset(collision(worldv,tri,'GRASS'),targets,S,name)
    check=try_load_asset(S/(name+'.ydr'));assert all(check.models[l] for l in lods)
    if not terrain:assert check.bounds
    stats.append(dict(name=name,lod_triangles=counts,collision=bool(check.bounds) or terrain,wind_shaders=sum(wmat),texture_dictionary=txdname,texture_names=sorted(set(str(p.value) for s in shaders for p in s.parameters if isinstance(p.value,str))),bb_min=lo.tolist(),bb_max=hi.tolist()))
    print('NATIVE_READY',name,counts,flush=True)
    return lo,hi

houses=json.loads((O/'dados/casas.json').read_text());trees=json.loads((O/'dados/arvores.json').read_text());port=json.loads((O/'dados/porto.json').read_text());sectors=json.loads((O/'dados/setores_alterados.json').read_text())
# The bake is deliberately kept separate from the cached geometry metadata.  Refresh
# only the material sampler fields here so a new bake resolution cannot leave stale
# 2K maps referenced by an otherwise current native export.
baked_manifest_path=O/'dados/materiais_baked.json'
if baked_manifest_path.exists():
    baked_manifest=json.loads(baked_manifest_path.read_text())
    for row in houses+trees:
        for info in row.get('materials',[]):
            key=info.get('source_name',info.get('name'))
            metadata=baked_manifest.get(row['name'],{}).get(key)
            if metadata:
                info.update(metadata)
if selected_names is not None:
    houses=[r for r in houses if r['name'] in selected_names];trees=[r for r in trees if r['name'] in selected_names];port=[r for r in port if r['name'] in selected_names]
if not assets_only and selected_names is None:
    for file in S.glob('pe_porto_*.ydr'):
        if file.stem not in {r['name'] for r in port}:file.unlink()
if terrain_only:
    for row in houses+trees+port:
        for info in row['materials']:texture(info)
for row in ([] if terrain_only else houses+trees):native(row)
for row in ([] if terrain_only else port):
    center=(np.array(row['bb_min'])+np.array(row['bb_max']))/2;center[2]=0;native(row,center)
if assets_only:
    for name,keys in texture_groups.items():save_asset(AssetTextureDictionary(textures={k:textures[k] for k in keys}),targets,S,name)
    (O/'dados/qualidade_materiais_nativos.json').write_text(json.dumps(dict(models=stats,textures=len(textures),texture_dictionaries={k:sorted(v) for k,v in texture_groups.items()},in_game_verified=False),indent=2))
    print('MATERIAL_ASSETS_READY',len(stats),len(textures),flush=True);sys.exit(0)
# All unchanged island files remain in the original resource. Replacement sectors go there at installation.
typ=try_load_asset(P/'fivem/stream/teste_ilha.ytyp')
for row in sectors:
    lo,hi=native(row,np.array(row['center']),True);arch=next(t for t in typ.archetypes if str(t.name)==row['name']);arch.bb_min=Vector(lo);arch.bb_max=Vector(hi);arch.bs_center=Vector((lo+hi)/2);arch.bs_radius=float(np.linalg.norm(hi-lo)/2);arch.texture_dictionary='pe_solo'
save_asset(typ,targets,S,'teste_ilha')
for name,keys in texture_groups.items():save_asset(AssetTextureDictionary(textures={k:textures[k] for k in keys}),targets,S,name)
if (S/'pe_texturas.ytd').exists():(S/'pe_texturas.ytd').unlink()
if terrain_only:
    rep=json.loads((O/'dados/pacote_nativo.json').read_text());rep['models']=[s for s in rep['models'] if not s['name'].startswith('ti_terreno')]+stats;rep['textures']=len(textures)
    (O/'dados/pacote_nativo.json').write_text(json.dumps(rep,indent=2));print('TERRAIN_REFINED',len(stats),flush=True);sys.exit(0)
save_asset(AssetMapTypes(name='porto_esperanca',archetypes=archetypes),targets,S,'porto_esperanca')
# Native ground plants and rocks retain their existing self-contained shader / physics assets.
pilot=json.loads((P/'amostra_natural/config.json').read_text());stocktyp=try_load_asset(P/'fivem/stream/ti_nature.ytyp')
for t in stocktyp.archetypes:models[str(t.name)]=dict(bb_min=list(t.bb_min),bb_max=list(t.bb_max),lod=t.lod_dist)
placements=json.loads((O/'dados/implantacao_casas.json').read_text());offset=np.array([250,-850,0.]);grid=np.load(O/'dados/terreno.npz')['terrain']
forest=json.loads((O/'dados/floresta.json').read_text()) if (O/'dados/floresta.json').exists() else []
def ground(x,y):
    ix=(x-grid[0,0,0])/(grid[0,1,0]-grid[0,0,0]);iy=(y-grid[0,0,1])/(grid[1,0,1]-grid[0,0,1]);i,j=int(ix),int(iy);u,v=ix-i,iy-j
    return float((1-u)*(1-v)*grid[j,i,2]+u*(1-v)*grid[j,i+1,2]+(1-u)*v*grid[j+1,i,2]+u*v*grid[j+1,i+1,2])
foliage=json.loads((P/'porto_esperanca/dados/vegetacao_posicoes.json').read_text());counts={'casas':len(placements),'arvores':0,'vegetacao_rasteira':0,'pedras':0}
placements.extend(forest);counts['arvores']+=len(forest)
for i,row in enumerate(foliage):
    key=row['modelo'];pos=np.array([row['x'],row['y'],0.])+offset;z=ground(*pos[:2]);sc=row['escala']
    # Trees are rooted in the actual exported mesh, including transition areas.
    if z<.5:continue
    name='pe_veg_'+key
    if name not in models:
        if key in ['capim','24_vegetacao_baixa']:name='ti_n_veg_grass_01_'+(['a','b','c'][i%3]);sc*=1.1;counts['vegetacao_rasteira']+=1
        elif key in ['19_oiti','20_figueira','23_jasmim_manga']:name='pe_veg_11_mangueira';counts['arvores']+=1
        else:name='pe_veg_01_coqueiro';sc*=.65;counts['arvores']+=1
    elif key in ['14_arbusto_costeiro','18_cerca_viva']:counts['vegetacao_rasteira']+=1
    else:counts['arvores']+=1
    pos[2]=z-.025;placements.append(dict(name=name,position=pos.tolist(),heading=(i*137.508)%360,scale=sc))
rocks=json.loads((P/'porto_esperanca/dados/pedras_posicoes.json').read_text())
for i,row in enumerate(rocks):
    p=np.array([row['x'],row['y'],0.])+offset;p[2]=ground(*p[:2])-.2;name=['ti_n_rock_1_a','ti_n_rock_2_a','ti_n_rock_4_c'][i%3];placements.append(dict(name=name,position=p.tolist(),heading=(i*97.3)%360,scale=max(.35,row['raio']*.6)));counts['pedras']+=1
for row in port:placements.append(dict(name=row['name'],position=models[row['name']]['center'],heading=0,scale=1))
groups={}
for row in placements:
    p=row['position'];k=(math.floor(p[0]/256),math.floor(p[1]/256));groups.setdefault(k,[]).append(row)
mapreport=[]
for i,(key,rows) in enumerate(sorted(groups.items())):
    entities=[];los=[];his=[];slos=[];shis=[]
    for j,row in enumerate(rows):
        name=row['name'];info=models[name];theta=math.radians(row['heading']);sc=row['scale'];p=np.array(row['position']);c,s=math.cos(theta),math.sin(theta);rot=np.array([[c,-s,0],[s,c,0],[0,0,1]])
        corners=np.array([[x,y,z] for x in [info['bb_min'][0],info['bb_max'][0]] for y in [info['bb_min'][1],info['bb_max'][1]] for z in [info['bb_min'][2],info['bb_max'][2]]])*sc;corners=corners@rot.T+p;lo=corners.min(0);hi=corners.max(0);dist=info['lod'];los.append(lo);his.append(hi);slos.append(lo-dist);shis.append(hi+dist)
        entities.append(Entity(name,Vector(p),Quaternion((math.cos(theta/2),0,0,-math.sin(theta/2))),sc,sc,EntityFlags.IS_STATIC,j+1,-1,dist,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]))
    name=f'pe_bairro_{i:02}';save_asset(AssetMapData(name=name,content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,physics_dictionaries=[],entities_extents=(Vector(np.min(los,0)),Vector(np.max(his,0))),streaming_extents=(Vector(np.min(slos,0)),Vector(np.max(shis,0)))),targets,S,name);mapreport.append(dict(name=name,entities=len(rows)))
(O/'dados/pacote_nativo.json').write_text(json.dumps(dict(models=stats,maps=mapreport,counts=counts,textures=len(textures),texture_dictionaries={k:sorted(v) for k,v in texture_groups.items()},in_game_verified=False),indent=2))
for file in S.glob('pe_bairro_*.ymap'):
    if file.stem not in {r['name'] for r in mapreport}:file.unlink()
(O/'dados/posicoes_nativas.json').write_text(json.dumps(placements,indent=2))
print('NATIVE_PORT_READY',counts,len(mapreport),flush=True)
