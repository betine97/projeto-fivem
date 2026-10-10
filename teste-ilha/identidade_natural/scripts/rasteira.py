from common import *
import copy,collections
from szio.gta5 import *
from szio.gta5.maps import MapContentFlags
from szio.types import Vector
F=dict(np.load(O/'dados/biomas.npz'));plan=read(O/'dados/plano.json');D=read(O/'dados/densidade_cayo.json')
templates={};samples=collections.defaultdict(list);counts=collections.Counter();rng=np.random.default_rng(71950)
# Grass batches are GPU instances, counted separately from individual trees/shrubs.
for path in (P/'cayo_perico/originais/mapas').glob('*grass*.ymap'):
    if path.name not in read(P/'cayo_perico/mapas_selecionados.json'):continue
    a=try_load_asset(path)
    for batch in a.grass_instance_lists:
        n=str(batch.archetype_name);templates.setdefault(n,batch);counts[n]+=len(batch.instances)
        samples[n].append(batch.instances.copy())
area=D['area_m2_estimate']
g,b=F['mask'][...,1]/255,F['mask'][...,2]/255
eligible=F['eligible'] & ((1-g)*(1-b)>.12) & (F['road_distance']>3)
jj,ii=np.where(eligible);groups=collections.defaultdict(list);target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
for n,total in counts.items():
    amount=round(total*plan['cayo_area_m2']/area)
    k=rng.integers(0,len(ii),amount);xx=x[jj[k],ii[k]]+rng.uniform(-dx*.35,dx*.35,amount);yy=y[jj[k],ii[k]]+rng.uniform(-dy*.35,dy*.35,amount)
    hh=sample(z,xx,yy)-.015;points=np.stack([xx,yy,hh],1);cx=np.floor(xx/96).astype(int);cy=np.floor(yy/96).astype(int)
    native=np.concatenate(samples[n]);ins=native[rng.integers(0,len(native),amount)].copy()
    ins['Normal'][:,0]=np.clip((sample(F['normals'][...,0],xx,yy)*.5+.5)*255,0,255).astype('u1')
    ins['Normal'][:,1]=np.clip((sample(F['normals'][...,1],xx,yy)*.5+.5)*255,0,255).astype('u1')
    for cell in np.unique(np.stack([cx,cy],1),axis=0):
        select=(cx==cell[0]) & (cy==cell[1]);p=points[select];lo=p.min(0)-.1;hi=p.max(0)+.1
        batch=copy.copy(templates[n]);batch.extents=(Vector(lo),Vector(hi));batch.instances=ins[select].copy()
        batch.instances['Position']=np.round((p-lo)/(hi-lo)*65535).astype('<u2');groups[tuple(cell)].append(batch)
    print('NATIVE_GRASS',n,amount,flush=True)
maps=[]
for i,(cell,batches) in enumerate(sorted(groups.items())):
    lo=np.min([b.extents[0] for b in batches],0);hi=np.max([b.extents[1] for b in batches],0);n=f'ni_rasteira_{i:03}'
    a=AssetMapData(name=n,content_flags=MapContentFlags.HAS_INSTANCED_DATA,grass_instance_lists=batches,entities_extents=(Vector(lo),Vector(hi)),streaming_extents=(Vector(lo-125),Vector(hi+125)))
    save_asset(a,target,O/'stream',n);maps.append(dict(name=n,instances=sum(len(b.instances) for b in batches)))
write(O/'dados/rasteira.json',dict(source_counts=dict(counts),density_per_m2=sum(counts.values())/area,counts=sum(m['instances'] for m in maps),maps=maps,method='Native selected Cayo grass batches; native scales/colors/AO/LOD, terrain normals and reprojected roots. Separate from tree counts.'))
print('GRASS_COMPLETE',sum(m['instances'] for m in maps),len(maps),flush=True)

