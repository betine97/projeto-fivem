from pathlib import Path
import sys,json,csv,collections,hashlib,math
R=Path(__file__).resolve().parents[3];P=R/'teste-ilha';O=P/'identidade_natural'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset,LodLevel
from szio.rpf import open_rpf
G=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
F=O/'fontes';F.mkdir(exist_ok=True);(O/'texturas').mkdir(exist_ok=True)
index=(R/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines()
byname={Path(q.split('|')[-1]).name:q for q in index};arcs={};provenance=[]
def extract(name):
    q=byname[name];parts=q.split('|');key='|'.join(parts[:-1])
    if key not in arcs:
        a=open_rpf(G/parts[0])
        for part in parts[1:-1]:a=a.open_nested(part)
        arcs[key]=a
    data=arcs[key].read_bytes(parts[-1]);dest=F/name;dest.write_bytes(data)
    provenance.append(dict(name=name,archive=key,sha256=hashlib.sha256(data).hexdigest()))
    return dest

archetypes={};types={}
for f in (P/'cayo_perico/originais/assets').glob('*.ytyp'):
    a=try_load_asset(f)
    for t in a.archetypes:archetypes[str(t.name)]=(t,f)
rows=list(csv.DictReader((O/'dados/entidades_cayo.tsv').open(),delimiter='\t'))
hd=[q for q in rows if q['lod'] in ['LODTYPES_DEPTH_HD','LODTYPES_DEPTH_ORPHANHD']]
def family(name):
    if name.startswith(('h4_prop_tree_','prop_tree_','prop_palm_')) and not any(w in name for w in ['log','fallen']):
        return 'subcanopy' if ('sap_' in name or 'dracaena_sml' in name) else 'tree'
    if name.startswith('h4_prop_palmeto'):return 'subcanopy'
    if name.startswith(('h4_prop_bush_','prop_bush_','prop_plant_','prop_grass_')) and not any(w in name for w in ['coca','ivy']):return 'bush'
    if name.startswith(('h4_prop_rock_','csx_coastsmalrock','prop_rock_')):return 'rock'
    if 'watert_' in name or name in ['h4_mph4_dock_maindock_watertower','prop_air_watertank1','prop_air_watertank2','prop_storagetank_07a']:return 'water_tower'
    return None
names={q['name'] for q in hd if family(q['name'])}
for name in sorted(names):
    if name in archetypes:continue
    source=byname.get(name+'.ydr')
    if not source:continue
    parts=source.split('|');key='|'.join(parts[:-1]);extract(name+'.ydr');arc=arcs[key]
    for typname in arc.list_dir(''):
        if typname.endswith('.ytyp'):
            if typname not in types:
                # Some archive-local metadata names have duplicates: read this exact archive.
                f=F/typname;f.write_bytes(arc.read_bytes(typname));types[typname]=try_load_asset(f)
            for t in types[typname].archetypes:archetypes.setdefault(str(t.name),(t,F/typname))

# Recover the original raster origin from the same meshes used for its area estimate.
ref=json.loads((P/'referencia_tecnica/medicao_cayo.json').read_text())
source=set(ref['source_models']);mins=[]
for q in rows:
    if q['name'] not in source:continue
    e=dict(name=q['name'],rot=[1,0,0,0],pos=[float(q[k]) for k in ['x','y','z']],scale_xy=float(q['sx']),scale_z=float(q['sz']))
    a=try_load_asset(P/'referencia_tecnica'/(e['name']+'.ydr'))
    w,x,y,z=e['rot'];rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    for m in a.models[LodLevel.HIGH]:
        for g in m.geometries:
            v=(g.vertex_buffer['Position']*np.array([e['scale_xy'],e['scale_xy'],e['scale_z']]))@rot.T+e['pos'];t=v[g.index_buffer.reshape(-1,3)]
            n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);t=t[(n[:,2]>1e-8)&(t[:,:,2].max(1)>0)]
            if len(t):mins.append(t[:,:,:2].min((0,1)))
origin=np.array(mins).min(0);mask=np.asarray(Image.open(P/'referencia_tecnica/mascara_cayo.png').transpose(Image.Transpose.FLIP_TOP_BOTTOM))>0
def on_land(q):
    i,j=((np.array([float(q['x']),float(q['y'])])-origin)/2).astype(int)
    return 0<=j<len(mask) and 0<=i<mask.shape[1] and bool(mask[j,i])
unique={}
for q in hd:
    f=family(q['name'])
    if not f or not on_land(q):continue
    key=(q['name'],*(round(float(q[k]),2) for k in ['x','y','z']))
    q=dict(q,family=f);unique[key]=q
counts=collections.Counter(q['family'] for q in unique.values());area=ref['reference_land_area_m2_estimate']
models={}
for name in sorted({q['name'] for q in unique.values()}):
    if name not in archetypes:continue
    t,path=archetypes[name];assetname=str(t.asset_name);native=P/'cayo_perico/originais/assets'/(assetname+'.ydr')
    if not native.exists():native=F/(assetname+'.ydr')
    if not native.exists():
        if assetname+'.ydr' not in byname:continue
        native=extract(assetname+'.ydr')
    a=try_load_asset(native)
    models[name]=dict(family=family(name),bb_min=list(t.bb_min),bb_max=list(t.bb_max),txd=str(t.texture_dictionary),physics=str(t.physics_dictionary),type_file=str(path),drawable_file=str(native),embedded_collision=a.bounds is not None,count=sum(q['name']==name for q in unique.values()),wind_shaders=[s.preset_filename for s in a.shader_group.shaders if 'tree' in s.preset_filename or 'grass' in s.preset_filename or 'wind' in s.preset_filename])
result=dict(area_m2_estimate=area,raster_resolution_m=2,origin=origin.tolist(),method='Unique HD/ORPHANHD entity origins inside above-sea HIGH terrain union; excludes LOD duplicates, logs, potted plants and cocaine fields; instanced grass and combined geometry not counted as individual trees.',counts=dict(counts),density_per_m2={k:v/area for k,v in counts.items()},models=models)
(O/'dados/densidade_cayo.json').write_text(json.dumps(result,indent=2));(O/'dados/entidades_natureza.json').write_text(json.dumps(list(unique.values())))
print('CAYO_DENSITY',counts,{k:round(v/area*10000,2) for k,v in counts.items()},flush=True)

# Original Chiliad-labelled drawable provides an actual material reference.
mount=try_load_asset(extract('cs1_15_mnt_chiliad_hi.ydr'))
mount_ref=dict(name='cs1_15_mnt_chiliad_hi',shaders=[dict(name=s.preset_filename,parameters={str(p.name):str(p.value) for p in s.parameters}) for s in mount.shader_group.shaders])
(O/'dados/referencia_chiliad.json').write_text(json.dumps(mount_ref,indent=2))
print('CHILIAD_SHADERS',mount_ref,flush=True)
(O/'dados/proveniencia.json').write_text(json.dumps(provenance,indent=2))
