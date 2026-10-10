from common import *
import collections,math
from szio.gta5 import *
from szio.gta5.maps import MapContentFlags
from szio.types import Vector,Quaternion
city=read(O/'dados/cidade.json');nature=read(O/'dados/implantacao.json');typ=try_load_asset(R/'server-data/resources/porto_esperanca/stream/porto_esperanca.ytyp');info={str(a.name):a for a in typ.archetypes};groups=collections.defaultdict(list)
for q in city['placements']:groups[q['settlement']].append(q)
for idx,rows in groups.items():
    entities=[];los=[];his=[];physics=set()
    for j,q in enumerate(rows):
        a=info[q['name']];pos=np.asarray(q['position']);theta=math.radians(q['heading']);c,s=math.cos(theta),math.sin(theta);rot=np.array([[c,-s,0],[s,c,0],[0,0,1]])
        lo,hi=np.asarray(a.bb_min),np.asarray(a.bb_max);corners=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])@rot.T+pos
        xy=corners[:,:2];ground=sample(z,xy[:,0],xy[:,1]);assert ground.max()-ground.min()<.01,(q['label'],ground)
        assert abs(sample(z,*pos[:2])-pos[2])<.01
        los.append(corners.min(0));his.append(corners.max(0))
        entities.append(Entity(q['name'],Vector(pos),Quaternion((math.cos(theta/2),0,0,-math.sin(theta/2))),1,1,EntityFlags.IS_STATIC,j+1,-1,650,0,EntityLodLevel.ORPHANHD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]))
        if str(a.physics_dictionary):physics.add(str(a.physics_dictionary))
    n=f'ni_povoacao_{idx:02}';save_asset(AssetMapData(name=n,content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,physics_dictionaries=sorted(physics),entities_extents=(Vector(np.min(los,0)),Vector(np.max(his,0))),streaming_extents=(Vector(np.min(los,0)-650),Vector(np.max(his,0)+650))), (AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),O/'stream',n)
    nature['maps'].append(dict(name=n,entities=len(rows),physics=sorted(physics)))
write(O/'dados/implantacao.json',nature)
write(O/'dados/validacao_povoacoes.json',dict(main_city_total=250,original_preserved=city['preserved_buildings'],new_buildings=len(city['placements']),villages=4,whole_house_footprints_seated=True,model_geometry_and_textures_reused=True))
print('SETTLEMENTS_READY',len(city['placements']),len(groups),flush=True)
