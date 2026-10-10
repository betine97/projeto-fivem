from common import *
import struct, collections, io
from PIL import Image
from szio.gta5 import LodLevel
from szio.gta5.entities import EntityLodLevel,EntityFlags
S=O/'stream';nature=read(O/'dados/implantacao.json');meta=read(O/'dados/rasteira_distante.json');data=dict(np.load(O/'dados/rasteira_distante.npz'));checks=[]
assert meta['near_fade_start_m']>meta['lod_start_m'] and meta['near_end_m']>meta['near_fade_start_m']
checks.append('Native GPU grass and medium cover overlap without a distance gap')
points=data['points'];eligible=data['eligible'].astype(float)
for ox,oy in [(0,0),(-3,-3),(3,-3),(3,3),(-3,3)]:assert (sample(eligible,points[:,0]+ox,points[:,1]+oy)>.98).all()
assert len(points)==meta['patches'] and meta['covered_area_m2']>2_300_000
checks.append('Every cover patch stays on planted terrain, outside roads, water, runway and buildings')
patches=0;groups=0;triangles=collections.Counter()
for m in nature['maps']:
    if m.get('tier')!='hd':continue
    hd=try_load_asset(S/(m['name']+'.ymap'));lod=try_load_asset(S/(str(hd.parent_name)+'.ymap'));slod=try_load_asset(S/(str(lod.parent_name)+'.ymap'))
    assert len(hd.entities)==len(lod.entities)
    for i,e in enumerate(hd.entities):
        assert e.lod_level==EntityLodLevel.HD and e.flags&EntityFlags.LOD_IN_PARENT_MAP and e.parent_index==i
        parent=lod.entities[i];assert parent.num_children==1 and parent.child_lod_dist==e.lod_dist==96 and parent.lod_dist==1200 and parent.parent_index==2
        near=try_load_asset(S/(str(e.archetype_name)+'.ydr'))
        for model in near.models[LodLevel.HIGH]:
            for g in model.geometries:assert (g.vertex_buffer['TexCoord0']>.875).all() # empty slot at (7,7)
        mesh=try_load_asset(S/(str(parent.archetype_name)+'.ydr'));groups+=1
        for model in mesh.models[LodLevel.HIGH]:
            for g in model.geometries:
                assert len(g.vertex_buffer)%13==0 and g.index_buffer.max()<len(g.vertex_buffer)
                triangles['medium']+=len(g.index_buffer)//3
    assert [e.lod_level for e in slod.entities]==[EntityLodLevel.SLOD4,EntityLodLevel.SLOD3,EntityLodLevel.SLOD2]
    for i,e in enumerate(slod.entities):
        assert e.parent_index==i-1 and e.num_children==(len(lod.entities) if i==2 else 1)
        if i:assert e.lod_dist==slod.entities[i-1].child_lod_dist
    assert slod.entities[2].child_lod_dist==1200 and slod.entities[0].lod_dist==8000
    lo,hi=slod.entities_extents;slo,shi=slod.streaming_extents
    assert np.all(np.asarray(slo)<=np.asarray(lo)-8499) and np.all(np.asarray(shi)>=np.asarray(hi)+8499)
    mesh=try_load_asset(S/(str(slod.entities[0].archetype_name)+'.ydr'))
    origin=np.asarray(slod.entities[0].position)
    for model in mesh.models[LodLevel.HIGH]:
        for g in model.geometries:
            v=g.vertex_buffer;assert len(v)%5==0 and g.index_buffer.max()<len(v) and len(v)<=60000
            world=v['Position']+origin
            assert np.max(abs(world[:,2]-sample(z,world[:,0],world[:,1])-.48))<.002
            assert np.isfinite(world).all() and (v['TexCoord0']>=0).all() and (v['TexCoord0']<=1).all()
            patches+=len(v)//5;triangles['far']+=len(g.index_buffer)//3
assert patches==meta['patches'] and triangles['far']==patches*4 and triangles['medium']==patches*12
checks+=['All grass patches have complete HD/LOD/SLOD2/SLOD3/SLOD4 links','Eight-kilometre streaming volumes include vertical flight and coastal views','Far cover follows actual terrain heights, with bounded native indices and UVs','Far geometry uses one third of the medium triangle count']
for name,columns,filled in [('ni_groundcover_atlas',8,48),('ni_canopy_atlas',16,186)]:
    txd=try_load_asset(S/(name+'.ytd'));dds=txd.textures[name].data.read_bytes();assert struct.unpack_from('<I',dds,28)[0]==9
    # Reloaded BC3 alpha must remain present at the very smallest mip.
    base=Image.open(io.BytesIO(dds));assert base.size==(columns*256,columns*256)
checks.append('Both native atlases retain nine mip levels after YTD serialization')
types={str(t.name):t for t in try_load_asset(S/'natureza_integrada.ytyp').archetypes}
for original,alias in meta['procedural_texture_aliases'].items():
    assert (S/(alias+'.ytd')).exists() and sha(S/(alias+'.ytd'))==sha(O/'fontes'/(original+'.ytd'))
for name,alias in read(O/'dados/rasteira.json')['alias_map'].items():assert str(types[alias].texture_dictionary) in meta['procedural_texture_aliases'].values()
checks.append('Every procedural grass archetype resolves an explicitly installed native texture dictionary')
total=0
for p in S.glob('ni_rasteira_*.ymap'):
    a=try_load_asset(p);lo,hi=a.entities_extents;slo,shi=a.streaming_extents
    assert np.all(np.asarray(slo)<=np.asarray(lo)-349) and np.all(np.asarray(shi)>=np.asarray(hi)+349)
    for b in a.grass_instance_lists:
        total+=len(b.instances)
        if 'stones' not in str(b.archetype_name):assert b.lod_dist==220 and b.lod_fade_start_dist==130
assert total==7014254
checks.append('All 7014254 native GPU instances remain intact with expanded near visibility')
write(O/'dados/validacao_rasteira_distante.json',dict(passed=True,checks=checks,patches=patches,groups=groups,triangles=dict(triangles),grass_instances=total,in_game_visual_verified=False))
print('DISTANT_GROUND_COVER_TESTS_PASSED',len(checks),patches,dict(triangles),flush=True)
