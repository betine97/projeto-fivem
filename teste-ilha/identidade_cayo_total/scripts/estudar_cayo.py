from common import *
import csv,collections
from szio.gta5 import LodLevel
OLD=P/'identidade_natural';C=O/'referencia_cache';C.mkdir(exist_ok=True)
rows=list(csv.DictReader((OLD/'dados/entidades_cayo.tsv').open(),delimiter='\t'))
names=set(read(P/'referencia_tecnica/medicao_cayo.json')['source_models'])
unique={}
for q in rows:
    if q['name'] in names and q['lod'] in ['LODTYPES_DEPTH_HD','LODTYPES_DEPTH_ORPHANHD']:
        unique[(q['name'],q['x'],q['y'],q['z'])]=q
models=[];heights=[];areas=[];slopes=[];shadercounts=collections.Counter()
for key,q in unique.items():
    n=q['name'];a=try_load_asset(P/'referencia_tecnica'/(n+'.ydr'));arrays={};geos=[]
    for model in a.models[LodLevel.HIGH]:
        for g in model.geometries:
            k=len(geos);arrays['v'+str(k)]=g.vertex_buffer;arrays['i'+str(k)]=g.index_buffer;geos.append(g.shader_index)
            v=g.vertex_buffer['Position']*np.array([float(q['sx']),float(q['sx']),float(q['sz'])])+np.array([float(q[c]) for c in ['x','y','z']]);t=v[g.index_buffer.reshape(-1,3)]
            cross=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);valid=(cross[:,2]>1e-5)&(t[:,:,2].mean(1)>0);cross=cross[valid];t=t[valid]
            heights.extend(t[:,:,2].mean(1));areas.extend(cross[:,2]/2);slopes.extend(np.hypot(cross[:,0],cross[:,1])/cross[:,2])
            shadercounts[a.shader_group.shaders[g.shader_index].preset_filename]+=len(t)
    np.savez_compressed(C/(n+'.npz'),**arrays)
    models.append(dict(name=n,position=[float(q[c]) for c in ['x','y','z']],scale=[float(q['sx']),float(q['sx']),float(q['sz'])],geometries=geos,shaders=[dict(preset=s.preset_filename,parameters={str(p.name):str(p.value) for p in s.parameters}) for s in a.shader_group.shaders]))
h=np.asarray(heights);area=np.asarray(areas);s=np.asarray(slopes)
def weighted(v,percent):
    order=np.argsort(v);cdf=np.cumsum(area[order])/area.sum();return [float(v[order[min(len(order)-1,np.searchsorted(cdf,p/100))]]) for p in percent]
report=dict(source='Actual installed GTA V mpheist4 HIGH ground triangles at original positions; area-weighted projected samples, excluding underwater triangles.',terrain_models=len(models),height_percentiles_m=dict(zip(['p10','p25','p50','p75','p90','p95','p99'],weighted(h,[10,25,50,75,90,95,99]))),maximum_triangle_centroid_m=float(h.max()),slope_percentiles=dict(zip(['p25','p50','p75','p90','p95'],weighted(s,[25,50,75,90,95]))),native_shaders=dict(shadercounts),components=collections.Counter(q['name'] for q in rows if q['lod'] in ['LODTYPES_DEPTH_HD','LODTYPES_DEPTH_ORPHANHD']),interpretation=['Broad low coastal ground and inland rising ridges, rather than a single alpine cone.','Sandy coves and rocky promontories alternate along the shoreline.','Grass, red mud, dirt tracks and rock share native layered materials.','Dense mixed tropical groves are interrupted by airstrip, docks, roads and settlement clearings.'],density_reference=str(OLD/'dados/densidade_cayo.json'))
write(O/'dados/geografia_cayo.json',report);write(C/'terreno.json',models)
print('CAYO_GEOGRAPHY', {k:v for k,v in report.items() if k not in ['components','interpretation']},flush=True)
