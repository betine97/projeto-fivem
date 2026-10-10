"""Reconcile terrain streaming/archetype volumes with the regraded geometry."""
from common import *
import collections
from szio.gta5 import *
from szio.types import Vector
T=O/'terreno';D=R/'server-data/resources/teste_ilha/stream';target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
typ=try_load_asset(T/'teste_ilha.ytyp');types={str(t.name):t for t in typ.archetypes};rep=[]
for row in read(O/'dados/solo.json')['sectors']:
    name=row['name'];a=try_load_asset(T/(name+'.ydr'));positions=np.concatenate([g.vertex_buffer['Position'] for models in a.models.values() for m in models for g in m.geometries]);lo=positions.min(0);hi=positions.max(0)
    t=types[name];oldlo=np.asarray(t.bb_min).copy();oldhi=np.asarray(t.bb_max).copy();outside=np.any(positions<oldlo-.01,axis=1)|np.any(positions>oldhi+.01,axis=1)
    t.bb_min=Vector(lo);t.bb_max=Vector(hi);t.bs_center=Vector((lo+hi)/2);t.bs_radius=float(np.linalg.norm(hi-lo)/2);t.lod_dist=8500
    a.lod_thresholds[LodLevel.VERYLOW]=8500;save_asset(a,target,T,name)
    mapname=name+'_map';m=try_load_asset(D/(mapname+'.ymap'));world=[]
    for e in m.entities:
        assert str(e.archetype_name)==name
        e.lod_dist=8500;world.extend([lo+np.asarray(e.position),hi+np.asarray(e.position)])
    wlo=np.min(world,0);whi=np.max(world,0);m.entities_extents=(Vector(wlo),Vector(whi));m.streaming_extents=(Vector(wlo-8800),Vector(whi+8800));save_asset(m,target,T,mapname)
    rep.append(dict(name=name,vertices_outside_previous_archetype=int(outside.sum()),old_bounds=[oldlo.tolist(),oldhi.tolist()],bounds=[lo.tolist(),hi.tolist()],map=mapname,far_distance_m=8500))
save_asset(typ,target,T,'teste_ilha')
write(O/'dados/limites_render.json',dict(passed=True,sectors=rep,corrected_sectors=sum(q['vertices_outside_previous_archetype']>0 for q in rep),streaming_distance_m=8800,in_game_visual_verified=False))
print('TERRAIN_RENDER_BOUNDS_REPAIRED',len(rep),'previously_incorrect',sum(q['vertices_outside_previous_archetype']>0 for q in rep),flush=True)
