"""Native GPU grass nearby, mixed plant patches at midrange, terrain-fit canopy far away.

GPU instance batches have no entity-parent field. Invisible HD containers only
control when their baked LOD takes over; the existing native batches draw the
plants in that near interval. The bands overlap to avoid an empty transition.
"""
from common import *
import copy, math, collections, shutil
from PIL import Image
from szio.gta5 import *
from szio.gta5.drawables import Geometry,Model,ShaderGroup,VertexDataType
from szio.gta5.maps import MapFlags,MapContentFlags
from szio.gta5.entities import *
from szio.types import Vector,Quaternion,DataSource
from lod_textures import atlas_dds
S=O/'stream';A=O/'atlas_rasteira';target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
nature=read(O/'dados/implantacao.json');grass=read(O/'dados/rasteira.json');F=dict(np.load(O/'dados/biomas.npz'))
types=try_load_asset(S/'natureza_integrada.ytyp');base=copy.deepcopy(types.archetypes[0]);added=[]
species=[r['name'] for r in read(A/'modelos.json')]
images=[Image.open(A/(f'patch_{i:02}_{key}.png')).convert('RGBA') for i in range(16) for key in ['top','front','side']]
dds,image,coverage=atlas_dds(images,8);image.save(A/'ni_groundcover_atlas.png')
save_asset(AssetTextureDictionary(textures={'ni_groundcover_atlas':EmbeddedTexture('ni_groundcover_atlas',2048,2048,DataSource.create(dds,name='ni_groundcover_atlas.dds'))}),target,S,'ni_groundcover_atlas')
# Correct the old canopy atlas too: a single mip level loses fine bush foliage
# when minified. Its full-resolution pixels and all native HD models stay intact.
oldatlas=read(O/'atlas/models.json');canopy_images=[Image.open(O/'atlas'/(r['name']+'_'+key+'.png')).convert('RGBA') for r in oldatlas for key in ['front','side','top']]
cdds,_,ccoverage=atlas_dds(canopy_images,16)
save_asset(AssetTextureDictionary(textures={'ni_canopy_atlas':EmbeddedTexture('ni_canopy_atlas',4096,4096,DataSource.create(cdds,name='ni_canopy_atlas.dds'))}),target,S,'ni_canopy_atlas')
prototype=try_load_asset(P/'cayo_perico/originais/assets/h4_mph4_isl_lod_ne_placement_ipl_00_slod4.ydr')
shader=copy.deepcopy(prototype.shader_group.shaders[0])
for p in shader.parameters:
    if str(p.name).lower()=='diffusesampler':p.value='ni_groundcover_atlas'
    if str(p.name).lower()=='selfshadowing':p.value=Vector((.15,0,0,0))
dtype=np.dtype([('Position','f4',3),('Normal','f4',3),('Colour0','u1',4),('Colour1','u1',4),('TexCoord0','f4',2)])
def uv(slot,points):
    points=np.asarray(points,float);x0=slot%8;y0=slot//8;pad=2/256
    return ((points*(1-2*pad)+pad)+[x0,y0])/8
def vertices(points,slots,view):
    n=len(points);v=np.zeros((n,13),dtype=dtype);px=points[:,0];py=points[:,1]
    # Centre subdivision follows crests and hollows instead of a floating flat
    # horizontal card. Sample the same triangular terrain as collision.
    offsets=np.array([[-3,-3],[3,-3],[3,3],[-3,3],[0,0]],float)
    xy=points[:,None,:2]+offsets[None,:,:];v['Position'][:,:5,:2]=xy
    v['Position'][:,:5,2]=sample(z,xy[...,0],xy[...,1])+.48
    v['Normal'][:,:5]=[0,0,1]
    for k,slot in enumerate(slots):v['TexCoord0'][k,:5]=uv(int(slot)*3,[[0,1],[1,1],[1,0],[0,0],[.5,.5]])
    for axis in [0,1]:
        start=5+axis*4;xy=points[:,None,:2]+(np.array([[-3,0],[3,0],[3,0],[-3,0]]) if axis==0 else np.array([[0,-3],[0,3],[0,3],[0,-3]]))
        v['Position'][:,start:start+4,:2]=xy;heights=sample(z,xy[...,0],xy[...,1]);v['Position'][:,start:start+4,2]=heights+np.array([.01,.01,1.61,1.61])
        v['Normal'][:,start:start+4]=[0,-1,0] if axis==0 else [1,0,0]
        for k,slot in enumerate(slots):v['TexCoord0'][k,start:start+4]=uv(int(slot)*3+axis+1,[[0,1],[1,1],[1,0],[0,0]])
    v['Colour0']=[255,29,0,255];v['Colour1']=0
    return v if view=='medium' else v[:,:5]
def drawable(name,vertices,faces,lo=None,hi=None):
    # Far slices are not contiguous; translate the array actually exported,
    # rather than a reshape copy that leaves world coordinates in the mesh.
    vertices=np.ascontiguousarray(vertices)
    v=vertices.reshape(-1);lo=v['Position'].min(0) if lo is None else lo;hi=v['Position'].max(0) if hi is None else hi;origin=(lo+hi)/2
    v['Position']-=origin;geos=[];nvert=vertices.shape[1]
    for start in range(0,len(vertices),4500):
        chunk=vertices[start:start+4500].reshape(-1);idx=(np.asarray(faces,np.uint16)[None,:,:]+np.arange(len(chunk)//nvert,dtype=np.uint16)[:,None,None]*nvert).ravel()
        geos.append(Geometry(VertexDataType.DEFAULT,chunk,idx,np.array([],np.uint16),0))
    a=AssetDrawable(name=name,shader_group=ShaderGroup([copy.deepcopy(shader)],{}),models={LodLevel.HIGH:[Model(0,geos,253,False,0,0)]},lod_thresholds={level:9998. for level in LodLevel})
    save_asset(a,target,S,name)
    t=copy.deepcopy(base);t.name=name;t.asset_name=name;t.texture_dictionary='ni_groundcover_atlas';t.drawable_dictionary='';t.physics_dictionary='';t.extensions=[];t.flags=0;t.lod_dist=8000;t.hd_texture_dist=500;t.bb_min=Vector(lo-origin);t.bb_max=Vector(hi-origin);t.bs_center=Vector((0,0,0));t.bs_radius=float(np.linalg.norm(hi-lo)/2);added.append(t)
    return origin,lo,hi
def ent(name,pos,level,lod,child,children,parent,external=False):
    flags=EntityFlags.LOD_IN_PARENT_MAP if external else EntityFlags(0)
    return Entity(name,Vector(pos),Quaternion((1,0,0,0)),1,1,flags,0,parent,lod,child,level,EntityPriorityLevel.REQUIRED,children,255,255,0,[])
def mapfile(name,parent,entities,lo,hi,padding,level):
    a=AssetMapData(name=name,parent_name=parent,flags=MapFlags.SCRIPTED|(MapFlags.IS_PARENT if level!='hd' else MapFlags(0)),content_flags={'hd':MapContentFlags.HAS_ENTITIES_HD,'lod':MapContentFlags.HAS_ENTITIES_LOD,'slod':MapContentFlags.HAS_ENTITIES_CONTAINER_LOD}[level],entities=entities,entities_extents=(Vector(lo),Vector(hi)),streaming_extents=(Vector(lo-padding),Vector(hi+padding)))
    save_asset(a,target,S,name)
    return dict(name=name,entities=len(entities),physics=[],parent=parent,groundcover=True,tier=level)
runway=(x>-800)&(x<-83)&(y>-115)&(y<-60);g,b=F['mask'][...,1]/255,F['mask'][...,2]/255
eligible=F['identity']&~F['water']&(z>1.5)&(F['slope']<1.3)&~runway&(F['road_distance']>4.5)&(F['clearance']>12.5)&(g*b<.90)
xx,yy=np.meshgrid(np.arange(float(x.min())+3,float(x.max())-3,6),np.arange(float(y.min())+3,float(y.max())-3,6))
px=xx.ravel();py=yy.ravel();ok=np.ones(len(px),bool)
for ox,oy in [(0,0),(-3,-3),(3,-3),(3,3),(-3,3)]:ok&=sample(eligible.astype(float),px+ox,py+oy)>.98
points=np.stack([px[ok],py[ok],sample(z,px[ok],py[ok])],1);rng=np.random.default_rng(20261010);slots=rng.integers(0,16,len(points))
cells=collections.defaultdict(list)
for i,p in enumerate(points):cells[(math.floor(p[0]/192),math.floor(p[1]/192))].append(i)
topfaces=[[0,1,4],[1,2,4],[2,3,4],[3,0,4]]
mediumfaces=topfaces+[[5,6,7],[5,7,8],[7,6,5],[8,7,5],[9,10,11],[9,11,12],[11,10,9],[12,11,9]]
maps=[];patches=0
for i,(cell,indices) in enumerate(sorted(cells.items())):
    smallgroups=collections.defaultdict(list)
    for k in indices:p=points[k];smallgroups[(math.floor(p[0]/48),math.floor(p[1]/48))].append(k)
    hd=[];lod=[];lows=[];highs=[]
    for j,(key,small) in enumerate(sorted(smallgroups.items())):
        v=vertices(points[small],slots[small],'medium');origin,lo,hi=drawable(f'ni_gc_mid_{i:03}_{j:02}',v,mediumfaces)
        lod.append(ent(f'ni_gc_mid_{i:03}_{j:02}',origin,EntityLodLevel.LOD,1200,96,1,2,True))
        # An empty atlas slot is the near container. Its full volume still has
        # valid geometry/bounds and is explicitly linked to its LOD parent.
        blank=np.zeros((1,4),dtype=dtype);blank['Position']=[[[lo[0],lo[1],lo[2]],[hi[0],lo[1],lo[2]],[hi[0],hi[1],hi[2]],[lo[0],hi[1],hi[2]]]];blank['Normal']=[0,0,1];blank['Colour0']=[255,29,0,255];blank['TexCoord0']=uv(63,[[0,1],[1,1],[1,0],[0,0]])
        pos,_,_=drawable(f'ni_gc_near_{i:03}_{j:02}',blank,[[0,1,2],[0,2,3]],lo,hi)
        hd.append(ent(f'ni_gc_near_{i:03}_{j:02}',pos,EntityLodLevel.HD,96,0,0,j,True));lows.append(lo);highs.append(hi)
    lo=np.min(lows,0);hi=np.max(highs,0);v=vertices(points[indices],slots[indices],'far');origin,_,_=drawable(f'ni_gc_far_{i:03}',v,topfaces)
    slod=[ent(f'ni_gc_far_{i:03}',origin,EntityLodLevel.SLOD4,8000,6000,1,-1),ent(f'ni_gc_far_{i:03}',origin,EntityLodLevel.SLOD3,6000,3500,1,0),ent(f'ni_gc_far_{i:03}',origin,EntityLodLevel.SLOD2,3500,1200,len(lod),1)]
    hn=f'ni_groundcover_hd_{i:03}';ln=f'ni_groundcover_lod_{i:03}';sn=f'ni_groundcover_slod_{i:03}'
    maps.extend([mapfile(hn,ln,hd,lo,hi,350,'hd'),mapfile(ln,sn,lod,lo,hi,1700,'lod'),mapfile(sn,'',slod,lo,hi,8500,'slod')]);patches+=len(indices)
    print('GROUND_COVER_CELL',i,'patches',len(indices),'groups',len(lod),flush=True)
# Explicit TXDs are required for the cloned procedural archetypes; the old
# model-only index did not include .ytd files, so those textures were skipped.
txdindex=read(O/'dados/indice_texturas_rasteira.json');txdaliases={}
for t in types.archetypes:
    if not str(t.name).startswith('ni_inst_'):continue
    name=str(t.texture_dictionary);name=name.removeprefix('ni_inst_')
    alias='ni_inst_'+name;txdaliases[name]=alias
    if not (O/'fontes'/(name+'.ytd')).exists():
        parts=txdindex[name+'.ytd'].split('|');arc=open_rpf(G/parts[0])
        for part in parts[1:-1]:arc=arc.open_nested(part)
        (O/'fontes'/(name+'.ytd')).write_bytes(arc.read_bytes(parts[-1]))
    shutil.copy2(O/'fontes'/(name+'.ytd'),S/(alias+'.ytd'));t.texture_dictionary=alias
types.archetypes=[t for t in types.archetypes if not str(t.name).startswith('ni_gc_')]
save_asset(types,target,S,'natureza_integrada')
save_asset(AssetMapTypes(name='ni_groundcover',archetypes=added),target,S,'ni_groundcover')
instances=0;gpu_before=[]
for m in grass['maps']:
    a=try_load_asset(S/(m['name']+'.ymap'))
    for batch in a.grass_instance_lists:
        gpu_before.append((str(batch.archetype_name),batch.lod_dist,batch.lod_fade_start_dist));stone='stones' in str(batch.archetype_name)
        batch.lod_dist=80 if stone else 220;batch.lod_fade_start_dist=45 if stone else 130
        instances+=len(batch.instances)
    lo,hi=a.entities_extents;a.streaming_extents=(Vector(np.asarray(lo)-350),Vector(np.asarray(hi)+350));a.flags|=MapFlags.SCRIPTED;save_asset(a,target,S,m['name'])
assert instances==grass['counts']
# Low shrubs need an earlier native-to-baked transition than the trees. Several
# source plants already reduce to two crossed cards at 60-120 m.
bush_aliases={q['alias'] for q in read(O/'dados/posicoes.json') if q['family']=='bush'}
bush_links=0
for m in nature['maps']:
    if not m['name'].startswith('ni_natureza_'):continue
    hd=try_load_asset(S/(m['name']+'.ymap'));lod=try_load_asset(S/(str(hd.parent_name)+'.ymap'));parents=set()
    for e in hd.entities:
        if str(e.archetype_name) in bush_aliases:e.lod_dist=120;parents.add(e.parent_index);bush_links+=1
    for parent in parents:lod.entities[parent].child_lod_dist=120
    save_asset(hd,target,S,m['name']);save_asset(lod,target,S,str(hd.parent_name))
metadata=dict(patches=patches,covered_area_m2=patches*36,source_species=species,near_end_m=220,near_fade_start_m=130,lod_start_m=96,lod_end_m=1200,far_distance_m=8000,maps=len(maps),drawables=len(added),mip_levels=9,atlas_cutout_coverage_per_mip=coverage,canopy_cutout_coverage_per_mip=ccoverage,terrain_fit=True,roads_runway_water_and_buildings_excluded=True,native_gpu_instances_preserved=instances,procedural_texture_aliases=txdaliases,all_low_plant_families_represented=True,in_game_visual_verified=False)
metadata['bush_transition_m']=120;metadata['bush_parent_links']=bush_links
nature['maps']=[m for m in nature['maps'] if not m.get('groundcover')]+maps;nature['distant_groundcover']=metadata;nature['revision']='cayo-rasteira-distante-20261010-1'
grass['distance_revision']=nature['revision'];grass['procedural_texture_aliases']=txdaliases;grass['near_lod_dist']=220;grass['near_fade_start_dist']=130
plan=read(O/'dados/plano.json');plan['revision']=nature['revision'];write(O/'dados/plano.json',plan);write(O/'dados/implantacao.json',nature);write(O/'dados/rasteira.json',grass);write(O/'dados/rasteira_distante.json',metadata)
np.savez_compressed(O/'dados/rasteira_distante.npz',points=points,slots=slots,eligible=eligible)
print('DISTANT_GROUND_COVER_COMPLETE',metadata,flush=True)
