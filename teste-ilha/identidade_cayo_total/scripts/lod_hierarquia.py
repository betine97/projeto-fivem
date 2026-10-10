"""Cayo-style HD -> batched canopy LOD -> SLOD2/3/4, with all plants represented."""
from common import *
import copy,collections,math,io
from PIL import Image
from szio.gta5 import *
from szio.gta5.drawables import Geometry,Model,ShaderGroup,VertexDataType
from szio.gta5.maps import MapContentFlags,MapFlags
from szio.gta5.entities import *
from szio.types import Vector,Quaternion,DataSource
S=O/'stream';target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
nature=read(O/'dados/implantacao.json');qs=read(O/'dados/posicoes.json');info=nature['models'];atlas=read(O/'atlas/models.json')
slots={};tex=Image.new('RGBA',(4096,4096))
for i,row in enumerate(atlas):
    for j,key in enumerate(['front','side','top']):
        slot=i*3+j;cx,cy=slot%16,slot//16
        tex.paste(Image.open(O/'atlas'/(row['name']+'_'+key+'.png')),(cx*256,cy*256))
        slots[(row['name'],key)]=(cx/16,cy/16,(cx+1)/16,(cy+1)/16)
meta={q['name']:q for q in atlas};tex.save(O/'atlas/ni_canopy_atlas.png')
buf=io.BytesIO();tex.save(buf,format='DDS',pixel_format='DXT5');dds=buf.getvalue()
save_asset(AssetTextureDictionary(textures={'ni_canopy_atlas':EmbeddedTexture('ni_canopy_atlas',4096,4096,DataSource.create(dds,name='ni_canopy_atlas.dds'))}),target,S,'ni_canopy_atlas')
prototype=try_load_asset(P/'cayo_perico/originais/assets/h4_mph4_isl_lod_ne_placement_ipl_00_slod4.ydr')
shader=copy.deepcopy(prototype.shader_group.shaders[0])
for p in shader.parameters:
    if str(p.name).lower()=='diffusesampler':p.value='ni_canopy_atlas'
    if str(p.name).lower()=='selfshadowing':p.value=Vector((.3,0,0,0))
types=try_load_asset(S/'natureza_integrada.ytyp');base=copy.deepcopy(types.archetypes[0]);added=[]
dtype=np.dtype([('Position','f4',3),('Normal','f4',3),('Colour0','u1',4),('Colour1','u1',4),('TexCoord0','f4',2)])
def billboard(q):
    m=meta[q['name']];w=m['width']*q['scale'];c=np.asarray(m['center'])*q['scale'];h=math.radians(q['heading']);rot=np.array([[math.cos(h),-math.sin(h),0],[math.sin(h),math.cos(h),0],[0,0,1]]);verts=[];norm=[];uv=[]
    for key,pts,n in [
        ('front',[[-.5,0,-.5],[.5,0,-.5],[.5,0,.5],[-.5,0,.5]],[0,-1,0]),
        ('side',[[0,-.5,-.5],[0,.5,-.5],[0,.5,.5],[0,-.5,.5]],[1,0,0]),
        ('top',[[-.5,-.5,0],[.5,-.5,0],[.5,.5,0],[-.5,.5,0]],[0,0,1])]:
        v=(np.asarray(pts)*w+c)@rot.T+np.asarray(q['position']);verts.extend(v);norm.extend([np.asarray(n)@rot.T]*4)
        u0,v0,u1,v1=slots[(q['name'],key)];pad=.5/4096;u0+=pad;v0+=pad;u1-=pad;v1-=pad
        uv.extend([[u0,v1],[u1,v1],[u1,v0],[u0,v0]])
    v=np.zeros(12,dtype=dtype);v['Position']=verts;v['Normal']=norm;v['Colour0']=[255,29,0,255];v['Colour1']=[0,0,0,0];v['TexCoord0']=uv
    return v
def mesh(name,rows):
    arrays=[billboard(q) for q in rows];v=np.concatenate(arrays);lo=v['Position'].min(0);hi=v['Position'].max(0);origin=(lo+hi)/2;v['Position']-=origin
    geos=[]
    # RAGE geometry uses 16-bit indices. Chunk before a vertex offset can overflow.
    for start in range(0,len(v),60000):
        chunk=v[start:start+60000];idx=np.tile(np.array([0,1,2,0,2,3],dtype=np.uint16),(len(chunk)//4,1))+np.arange(0,len(chunk),4,dtype=np.uint16)[:,None]
        geos.append(Geometry(VertexDataType.DEFAULT,chunk,idx.ravel(),np.array([],dtype=np.uint16),0))
    a=AssetDrawable(name=name,shader_group=ShaderGroup([shader],{}),models={LodLevel.HIGH:[Model(0,geos,253,False,0,0)]},lod_thresholds={level:9998. for level in LodLevel})
    save_asset(a,target,S,name)
    t=copy.deepcopy(base);t.name=name;t.asset_name=name;t.texture_dictionary='ni_canopy_atlas';t.physics_dictionary='';t.drawable_dictionary='';t.extensions=[];t.lod_dist=8000;t.hd_texture_dist=500;t.flags=0;t.bb_min=Vector(lo-origin);t.bb_max=Vector(hi-origin);t.bs_center=Vector((0,0,0));t.bs_radius=float(np.linalg.norm(hi-lo)/2);added.append(t)
    return origin,lo,hi
shadow=EntityFlags.CAST_STATIC_SHADOWS|EntityFlags.CAST_DYNAMIC_SHADOWS
def ent(name,pos,level,lod,child,children,parent,external=False):
    flags=shadow|(EntityFlags.LOD_IN_PARENT_MAP if external else EntityFlags(0))
    return Entity(name,Vector(pos),Quaternion((1,0,0,0)),1,1,flags,0,parent,lod,child,level,EntityPriorityLevel.REQUIRED,children,255,255,0,[])
def extent(rows):
    los=[];his=[]
    for q in rows:
        v=info[q['name']];th=math.radians(q['heading']);c,s=math.cos(th),math.sin(th);rot=np.array([[c,-s,0],[s,c,0],[0,0,1]])
        corners=np.array([[a,b,c] for a in [v['bb_min'][0],v['bb_max'][0]] for b in [v['bb_min'][1],v['bb_max'][1]] for c in [v['bb_min'][2],v['bb_max'][2]]])*q['scale'];corners=corners@rot.T+q['position'];los.append(corners.min(0));his.append(corners.max(0))
    return np.min(los,0),np.max(his,0)
groups=collections.defaultdict(list)
for q in qs:groups[(math.floor(q['position'][0]/192),math.floor(q['position'][1]/192))].append(q)
maps=[];represented=0;links=0
for i,(cell,rows) in enumerate(sorted(groups.items())):
    hdname=f'ni_natureza_{i:02}';lodname=f'ni_canopy_lod_{i:02}';slodname=f'ni_canopy_slod_{i:02}'
    canopy=[q for q in rows if q['family'] in ['tree','subcanopy','bush']]
    assert all(q['name'] in meta for q in canopy)
    sub=collections.defaultdict(list)
    for q in canopy:sub[(math.floor(q['position'][0]/48),math.floor(q['position'][1]/48),q['family'])].append(q)
    hd=[];lod=[];physics=set()
    for j,(key,small) in enumerate(sorted(sub.items())):
        name=f'ni_canopy_{i:02}_{j:02}';pos,lo,hi=mesh(name,small);band={'tree':560,'subcanopy':420,'bush':260}[key[2]]
        lod.append(ent(name,pos,EntityLodLevel.LOD,1800,band,len(small),2,True))
        for q in small:
            th=math.radians(q['heading']);e=ent(q['alias'],q['position'],EntityLodLevel.HD,band,0,0,j,True);e.scale_xy=q['scale'];e.scale_z=q['scale'];e.rotation=Quaternion((math.cos(th/2),0,0,-math.sin(th/2)));e.guid=len(hd)+1;hd.append(e);links+=1
            if (S/(q['alias']+'.ybn')).exists():physics.add(q['alias'])
    for q in rows:
        if q['family'] in ['tree','subcanopy','bush']:continue
        th=math.radians(q['heading']);e=ent(q['alias'],q['position'],EntityLodLevel.ORPHANHD,info[q['name']]['lod'],0,0,-1);e.scale_xy=q['scale'];e.scale_z=q['scale'];e.rotation=Quaternion((math.cos(th/2),0,0,-math.sin(th/2)));e.guid=len(hd)+1;hd.append(e)
        if (S/(q['alias']+'.ybn')).exists():physics.add(q['alias'])
    lo,hi=extent(rows)
    save_asset(AssetMapData(name=hdname,parent_name=lodname,flags=MapFlags.SCRIPTED,content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS|MapContentFlags.HAS_ENTITIES_CRITICAL,entities=hd,physics_dictionaries=sorted(physics),entities_extents=(Vector(lo),Vector(hi)),streaming_extents=(Vector(lo-900),Vector(hi+900))),target,S,hdname)
    farname=f'ni_canopy_far_{i:02}';origin,blo,bhi=mesh(farname,canopy)
    save_asset(AssetMapData(name=lodname,parent_name=slodname,flags=MapFlags.SCRIPTED|MapFlags.IS_PARENT,content_flags=MapContentFlags.HAS_ENTITIES_LOD,entities=lod,entities_extents=(Vector(blo),Vector(bhi)),streaming_extents=(Vector(blo-2400),Vector(bhi+2400))),target,S,lodname)
    slod=[ent(farname,origin,EntityLodLevel.SLOD4,8000,4000,1,-1),ent(farname,origin,EntityLodLevel.SLOD3,4000,1800,1,0),ent(farname,origin,EntityLodLevel.SLOD2,1800,1800,len(lod),1)]
    # SLOD2's children are in the LOD map at the same 1.8 km transition;
    # extend SLOD2 to 2.4 km so no threshold equals its children distance.
    slod[2].lod_dist=2400;slod[1].child_lod_dist=2400
    for e in lod:e.lod_dist=2400
    # Persist adjusted parent distances after building the complete chain.
    save_asset(AssetMapData(name=lodname,parent_name=slodname,flags=MapFlags.SCRIPTED|MapFlags.IS_PARENT,content_flags=MapContentFlags.HAS_ENTITIES_LOD,entities=lod,entities_extents=(Vector(blo),Vector(bhi)),streaming_extents=(Vector(blo-3000),Vector(bhi+3000))),target,S,lodname)
    slod[2].child_lod_dist=2400;slod[2].lod_dist=4000;slod[1].child_lod_dist=4000;slod[1].lod_dist=6000;slod[0].child_lod_dist=6000
    save_asset(AssetMapData(name=slodname,flags=MapFlags.SCRIPTED|MapFlags.IS_PARENT,content_flags=MapContentFlags.HAS_ENTITIES_CONTAINER_LOD,entities=slod,entities_extents=(Vector(blo),Vector(bhi)),streaming_extents=(Vector(blo-8500),Vector(bhi+8500))),target,S,slodname)
    maps.extend([dict(name=hdname,entities=len(hd),physics=sorted(physics),parent=lodname),dict(name=lodname,entities=len(lod),physics=[],parent=slodname,lod=True),dict(name=slodname,entities=3,physics=[],slod=True)])
    represented+=len(canopy);print('CANOPY_CELL',i,'plants',len(canopy),'groups',len(lod),flush=True)
types.archetypes=[t for t in types.archetypes if not str(t.name).startswith('ni_canopy_')]+added
save_asset(types,target,S,'natureza_integrada')
# Old unparented duplicate maps are superseded, not requested together.
for path in S.glob('ni_natureza_lod_*.ymap'):
    assert path.parent.resolve()==S.resolve();path.unlink()
nature['maps']=maps+[m for m in nature['maps'] if m['name'].startswith('ni_povoacao_')]
nature['revision']='cayo-hierarquia-vegetacao-20261009-3';nature['distant_canopy']=dict(plants=represented,hd_parent_links=links,cluster_drawables=len(added),far_distance_m=8000,levels=['HD','LOD','SLOD2','SLOD3','SLOD4'],all_canopy_placements_represented=True,atlas_native_render=True)
write(O/'dados/implantacao.json',nature)
plan=read(O/'dados/plano.json');plan['revision']=nature['revision'];write(O/'dados/plano.json',plan)
write(O/'dados/lod_hierarquia.json',nature['distant_canopy'])
print('CANOPY_HIERARCHY_COMPLETE',nature['distant_canopy'],flush=True)
