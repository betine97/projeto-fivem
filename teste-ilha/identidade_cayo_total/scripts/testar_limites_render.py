"""Check geometry against every terrain culling volume after regrading."""
from common import *
from szio.gta5 import *
T=O/'terreno';typ=try_load_asset(T/'teste_ilha.ytyp');types={str(t.name):t for t in typ.archetypes}
checks=[]
for row in read(O/'dados/solo.json')['sectors']:
    name=row['name'];d=try_load_asset(T/(name+'.ydr'));t=types[name]
    p=np.concatenate([g.vertex_buffer['Position'] for models in d.models.values() for model in models for g in model.geometries])
    lo,hi=np.asarray(t.bb_min),np.asarray(t.bb_max)
    assert np.all(p>=lo-.005) and np.all(p<=hi+.005),name
    assert np.max(np.linalg.norm(p-np.asarray(t.bs_center),axis=1))<=t.bs_radius+.005,name
    m=try_load_asset(T/(name+'_map.ymap'));elo,ehi=map(np.asarray,m.entities_extents);slo,shi=map(np.asarray,m.streaming_extents)
    for e in m.entities:
        assert np.allclose(e.rotation,(0,0,0,1)),name
        world=p+np.asarray(e.position)
        assert np.all(world>=elo-.005) and np.all(world<=ehi+.005),name
        assert e.lod_dist==8500,name
    assert np.all(slo<=elo-8799) and np.all(shi>=ehi+8799),name
    assert t.lod_dist==8500 and d.lod_thresholds[LodLevel.VERYLOW]==8500,name
checks.extend(['All 43 terrain sectors contain their full geometry in archetype boxes and spheres','All terrain entity volumes follow the regraded world geometry','Horizontal and vertical streaming volumes include an 8.8 km margin','Terrain uses its lowest geometry level at distance instead of disappearing'])
write(O/'dados/validacao_limites_render.json',dict(passed=True,checks=checks,sectors=43,in_game_visual_verified=False))
print('TERRAIN_RENDER_LIMITS_PASSED',len(checks),flush=True)
