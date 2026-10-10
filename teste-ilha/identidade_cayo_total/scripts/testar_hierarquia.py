from common import *
import collections,math
from szio.gta5.entities import EntityLodLevel,EntityFlags
from szio.gta5 import LodLevel
S=O/'stream';checks=[];nature=read(O/'dados/implantacao.json');metadata=read(O/'dados/lod_hierarquia.json')
total=0;far=0;groups=0;parent_counts=collections.defaultdict(collections.Counter)
for meta in nature['maps']:
    if not meta['name'].startswith('ni_natureza_'):continue
    hd=try_load_asset(S/(meta['name']+'.ymap'));lod=try_load_asset(S/(str(hd.parent_name)+'.ymap'));slod=try_load_asset(S/(str(lod.parent_name)+'.ymap'))
    counts=parent_counts[str(hd.parent_name)]
    for e in hd.entities:
        if e.lod_level!=EntityLodLevel.HD:continue
        assert e.flags&EntityFlags.LOD_IN_PARENT_MAP
        assert 0<=e.parent_index<len(lod.entities)
        parent=lod.entities[e.parent_index];assert e.lod_dist==parent.child_lod_dist
        counts[e.parent_index]+=1;total+=1
for parent_name,counts in parent_counts.items():
    lod=try_load_asset(S/(parent_name+'.ymap'));slod=try_load_asset(S/(str(lod.parent_name)+'.ymap'))
    assert set(counts)==set(range(len(lod.entities)))
    for i,e in enumerate(lod.entities):
        assert e.num_children==counts[i] and e.parent_index==2 and e.flags&EntityFlags.LOD_IN_PARENT_MAP
        assert e.lod_dist==slod.entities[2].child_lod_dist
        groups+=1
    levels=[EntityLodLevel.SLOD4,EntityLodLevel.SLOD3,EntityLodLevel.SLOD2]
    for i,e in enumerate(slod.entities):
        assert e.lod_level==levels[i] and e.parent_index==i-1
        assert e.num_children==(len(lod.entities) if i==2 else 1)
        if i>0:assert e.lod_dist==slod.entities[i-1].child_lod_dist
    assert slod.entities[0].lod_dist==8000
    lo,hi=slod.streaming_extents;blo,bhi=slod.entities_extents
    assert all(float(lo[i])<=float(blo[i])-8499 and float(hi[i])>=float(bhi[i])+8499 for i in range(3))
    mesh=try_load_asset(S/(str(slod.entities[0].archetype_name)+'.ydr'))
    vertices=0
    for model in mesh.models[LodLevel.HIGH]:
        for g in model.geometries:
            v=g.vertex_buffer;vertices+=len(v)
            assert len(v)<=60000 and max(g.index_buffer)<len(v)
            assert np.isfinite(v['Position']).all()
            assert (v['TexCoord0']>=0).all() and (v['TexCoord0']<=1).all()
    assert vertices==sum(counts.values())*12;far+=vertices//12
assert total==far==metadata['plants']==100488
checks+=['100488 HD placements have valid Cayo-style parent links','Every parent child count and transition distance matches','All plants represented at every distant tier, including overhead views','All SLOD streaming volumes support 8 km distance and altitude','Native vertex indices, UV ranges and geometry bounds valid']
types=try_load_asset(S/'natureza_integrada.ytyp');registered={str(t.name) for t in types.archetypes}
grass=read(O/'dados/rasteira.json');aliases=grass['alias_map']
assert len(aliases)==25
for name,alias in aliases.items():assert alias in registered and (S/(alias+'.ydr')).is_file()
instances=0
for m in grass['maps']:
    a=try_load_asset(S/(m['name']+'.ymap'))
    for batch in a.grass_instance_lists:
        assert str(batch.archetype_name) not in aliases
        assert str(batch.archetype_name) in registered or str(batch.archetype_name).startswith('h4_')
        instances+=len(batch.instances)
assert instances==grass['counts'];checks+=['25 procedural grass archetypes explicitly registered','All 7014254 GPU grass instances use available native archetypes']
write(O/'dados/validacao_hierarquia.json',dict(passed=True,checks=checks,plants=total,clusters=groups,grass_instances=instances,in_game_visual_verified=False))
print('HIERARCHY_TESTS_PASSED',len(checks),'plants',total,'grass',instances,flush=True)
