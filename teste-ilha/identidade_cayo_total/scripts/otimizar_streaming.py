"""Reduce HD map residency without removing plants or weakening distant LODs."""
from common import *
import collections
from szio.gta5 import *
from szio.types import Vector
S=O/'stream';target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
nature=read(O/'dados/implantacao.json');positions=read(O/'dados/posicoes.json')
family={q['alias']:q['family'] for q in positions}
types={str(t.name):t for t in try_load_asset(S/'natureza_integrada.ytyp').archetypes}
changed=[];oldmaps=[];newmaps=[];original=collections.Counter();new=collections.Counter()
def volume(entities):
    points=[]
    for e in entities:
        t=types[str(e.archetype_name)];lo,hi=map(np.asarray,[t.bb_min,t.bb_max]);corners=np.array([[xx,yy,zz] for xx in [lo[0],hi[0]] for yy in [lo[1],hi[1]] for zz in [lo[2],hi[2]]])
        # szio exposes the GTA stored inverse XY quaternion in x,y,z,w order.
        q=np.asarray(e.rotation);theta=-2*np.arctan2(q[2],q[3]);c,s=np.cos(theta),np.sin(theta)
        rot=np.array([[c,-s,0],[s,c,0],[0,0,1]])
        points.append((corners*[e.scale_xy,e.scale_xy,e.scale_z])@rot.T+np.asarray(e.position))
    p=np.concatenate(points);return p.min(0),p.max(0)
for row in nature['maps']:
    if not row['name'].startswith('ni_natureza_'):continue
    source=S/(row['name']+'.ymap')
    if source.exists():m=try_load_asset(source)
    else:
        # Resume a staged build without using older, already installed LOD bands.
        previous=[try_load_asset(p) for p in S.glob(row['name']+'_*.ymap')]
        assert previous,row['name']
        m=previous[0];m.entities=[e for part in previous for e in part.entities]
        lo,hi=volume(m.entities);m.streaming_extents=(Vector(lo-900),Vector(hi+900))
    oldmaps.append((np.asarray(m.streaming_extents[0]),np.asarray(m.streaming_extents[1]),len(m.entities)))
    groups=collections.defaultdict(list)
    for e in m.entities:
        key=family[str(e.archetype_name)]
        if key=='bush':key+='_'+str(int(np.floor(e.position[0]/96)))+'_'+str(int(np.floor(e.position[1]/96)))
        groups[key].append(e);original[str(e.archetype_name)]+=1
    for key,entities in sorted(groups.items()):
        name=row['name']+'_'+key;lo,hi=volume(entities);padding=max(e.lod_dist for e in entities)+60
        physics=sorted({str(e.archetype_name) for e in entities if (S/(str(e.archetype_name)+'.ybn')).is_file()})
        a=AssetMapData(name=name,parent_name=str(m.parent_name),flags=m.flags,content_flags=m.content_flags,entities=entities,physics_dictionaries=physics,entities_extents=(Vector(lo),Vector(hi)),streaming_extents=(Vector(lo-padding),Vector(hi+padding)))
        save_asset(a,target,S,name);newmaps.append((lo-padding,hi+padding,len(entities)))
        changed.append(dict(name=name,entities=len(entities),physics=physics,parent=str(m.parent_name),family=key.split('_')[0],hd_streaming_padding_m=float(padding)))
        new.update(str(e.archetype_name) for e in entities)
    if source.exists():assert source.resolve().parent==S.resolve();source.unlink()
assert original==new, 'A reorganização do streaming alterou a população de vegetação.'
nature['maps']=[r for r in nature['maps'] if not r['name'].startswith('ni_natureza_')]+changed
gridpoints=np.array([(xx,yy,zz) for xx in range(-1350,1351,50) for yy in range(-1750,1751,50) for zz in [0,20,100,300,600,1000]])
def peak(maps):
    count=sum(n*((gridpoints>=lo).all(1)&(gridpoints<=hi).all(1)) for lo,hi,n in maps);i=count.argmax();return dict(entities=int(count[i]),camera=gridpoints[i].tolist())
before,after=peak(oldmaps),peak(newmaps)
assert after['entities']<30500 and after['entities']<before['entities']*.35,(before,after)
active={r['name'] for r in changed}
for p in S.glob('ni_natureza_*.ymap'):
    if p.stem not in active:assert p.resolve().parent==S.resolve();p.unlink()
meta=dict(passed=True,old_peak_hd_box_residency=before,new_peak_hd_box_residency=after,grid_cameras=len(gridpoints),placements_preserved=sum(new.values()),families_stream_independently=True,parent_indices_unchanged=True,native_building_pool_limit=65000,in_game_visual_verified=False)
nature['streaming_budget']=meta;write(O/'dados/implantacao.json',nature);write(O/'dados/validacao_streaming.json',meta)
print('HD_RESIDENCY_OPTIMIZED',before,after,'maps',len(changed),flush=True)
