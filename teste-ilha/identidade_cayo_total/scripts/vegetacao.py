from common import *
import copy,math,collections,shutil,re
from szio.gta5 import *
from szio.gta5.entities import *
from szio.gta5.maps import MapContentFlags
from szio.gta5.bounds import AssetBoundBvh,AssetBoundComposite,BoundVertex,BoundPrimitive,CollisionFlags,CollisionMaterial
from szio.types import Vector,Quaternion
S=O/'stream';target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
D=read(O/'dados/densidade_cayo.json');plan=read(O/'dados/plano.json');fields=dict(np.load(O/'dados/biomas.npz'))
identity_float=fields['identity'].astype(float);water_float=fields['water'].astype(float)
info=D['models'];rng=np.random.default_rng(2026100950);cache={};aliases={n:'ni_'+n for n in info};archetypes=[]
index=(R/'laboratorio_fivem/work/assets_index.txt').read_text().splitlines();lookup={Path(q.split('|')[-1]).name:q for q in index};arcs={}
materials=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
def boundbox(b,v):
    lo=v.min(0);hi=v.max(0);b.bb_min=Vector(lo);b.bb_max=Vector(hi);b.centroid=Vector((lo+hi)/2);b.cg=b.centroid;b.radius_around_centroid=float(np.linalg.norm(hi-lo)/2)
def mesh_collision(a,family):
    vs=[];ts=[];start=0
    for m in a.models[LodLevel.HIGH]:
        for g in m.geometries:
            v=g.vertex_buffer['Position'];tri=g.index_buffer.reshape(-1,3);vs.append(v);ts.append(tri+start);start+=len(v)
    v=np.concatenate(vs);tri=np.concatenate(ts);t=v[tri];valid=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)>1e-7
    b=AssetBoundBvh();b.margin=.002;b.composite_collision_type_flags=CollisionFlags.MAP_TYPE_MOVER|CollisionFlags.MAP_TYPE_VEHICLE|CollisionFlags.MAP_TYPE_WEAPON|CollisionFlags.MAP_TYPE_COVER;b.composite_collision_include_flags=CollisionFlags(0xffffffff)
    b.geometry_vertices=[BoundVertex(Vector(p),None) for p in v];mat=CollisionMaterial.from_packed(materials.index('ROCK' if family=='rock' else 'METAL_SOLID_MEDIUM'))
    b.geometry_primitives=[BoundPrimitive.new_triangle(*(int(i) for i in t),mat) for t in tri[valid]];boundbox(b,v);root=AssetBoundComposite(children=[b]);boundbox(root,v);return root
for name,row in info.items():
    path=row['type_file']
    if path not in cache:cache[path]=try_load_asset(Path(path))
    archetype=copy.deepcopy(next(t for t in cache[path].archetypes if str(t.name)==name));alias=aliases[name]
    archetype.name=alias;archetype.asset_name=alias;archetype.drawable_dictionary='';archetype.physics_dictionary=''
    drawable=try_load_asset(Path(row['drawable_file']))
    # Keep native render geometry, texture references, wind data and intrinsic LODs byte-for-byte.
    shutil.copy2(row['drawable_file'],S/(alias+'.ydr'))
    if not row['embedded_collision'] and row['family'] in ['tree','rock','water_tower']:
        save_asset(mesh_collision(drawable,row['family']),target,S,alias);archetype.physics_dictionary=alias
    # Match the native Cayo streaming bands.  Required HD vegetation keeps a
    # readable island silhouette nearby; a separate LOD band below carries the
    # skyline when the camera is offshore or in the aircraft.
    lod={'tree':560,'subcanopy':420,'bush':260,'rock':320,'water_tower':850}[row['family']]
    archetype.lod_dist=lod;archetype.hd_texture_dist=lod;row['lod']=lod
    # Cayo's native dictionaries are already mounted by the adjacent resource.
    # For base-game props used in Cayo, retain the original TXD and copy its native dictionaries.
    source=lookup.get(Path(row['drawable_file']).name)
    if source and not name.startswith('h4_'):
        parts=source.split('|');key='|'.join(parts[:-1])
        if key not in arcs:
            arc=open_rpf(G/parts[0])
            for part in parts[1:-1]:arc=arc.open_nested(part)
            arcs[key]=arc
        for suffix in ['','+hi']:
            n=row['txd']+suffix+'.ytd'
            if n in arcs[key].list_dir(''):(S/n).write_bytes(arcs[key].read_bytes(n))
    archetypes.append(archetype)
save_asset(AssetMapTypes(name='natureza_integrada',archetypes=archetypes),target,S,'natureza_integrada')
palette={f:[n for n,v in info.items() if v['family']==f] for f in ['tree','subcanopy','bush','rock']}
def pick(f,xx,yy):
    names=palette[f];weights=np.array([info[n]['count'] for n in names],float)
    if f=='tree':
        shore=float(sample(fields['shore'],xx,yy))
        for i,n in enumerate(names):
            if 'palm' in n:weights[i]*=2.5 if shore<55 else .65
            if 'mgrv' in n:weights[i]*=2 if shore<35 else .35
    elif f=='bush':
        # Cayo's understory is not a single green blob.  Keep its measured
        # proportions as the baseline, then make the recognizable fern/cane,
        # flowering and broad-leaf groups survive the larger island sample.
        accents={
            'prop_plant_cane_02a':3.0,'prop_plant_cane_02b':2.2,
            'prop_plant_fern_01b':2.8,'prop_plant_fern_02a':2.4,
            'prop_plant_fern_02b':2.4,'prop_plant_fern_02c':2.4,
            'prop_plant_group_06a':2.8,'prop_plant_group_06b':2.8,
            'h4_prop_bush_buddleia_sml_01':5.0,
            'h4_prop_bush_olndr_white_lrg':3.0,
            'h4_prop_bush_olndr_white_sml':3.0,
            'h4_prop_bush_monstera_med_01':1.8,
        }
        for i,n in enumerate(names):weights[i]*=accents.get(n,1.0)
    elif f=='subcanopy':
        for i,n in enumerate(names):
            if 'palmeto' in n or 'areca' in n:weights[i]*=1.55
    return str(rng.choice(names,p=weights/weights.sum()))
placements=[];removed=[];portmaps=[]
for path in sorted((P/'identidade_natural/porto_base').glob('pe_bairro_*.ymap')):
    a=try_load_asset(path);kept=[]
    for e in a.entities:
        n=str(e.archetype_name);xx,yy,zz=map(float,e.position)
        replace=n.startswith(('pe_veg_','ti_n_rock_','ti_n_veg_grass_')) and bool(sample(identity_float,xx,yy)>.5)
        # Clear roots off newly painted dirt paths throughout the natural zone.
        clear=n.startswith(('pe_veg_','ti_n_veg_grass_','ti_n_rock_')) and (float(sample(fields['road_distance'],xx,yy))<3 or float(sample(fields['clearance'],xx,yy))<18)
        clear=clear or (n.startswith(('pe_veg_','ti_n_veg_grass_','ti_n_rock_')) and -805<xx<-78 and -120<yy<-55)
        if not replace and not clear:kept.append(e);continue
        removed.append(dict(map=path.stem,name=n,position=[xx,yy,zz]))
        if clear:continue
        f='rock' if 'rock' in n else 'bush' if any(t in n for t in ['veg_14_','veg_18_','veg_grass_']) else 'tree'
        model=pick(f,xx,yy) if f!='rock' else str(rng.choice([n for n in palette['rock'] if max(np.asarray(info[n]['bb_max'])[:2]-np.asarray(info[n]['bb_min'])[:2])<4]));scale=float(rng.uniform(.92,1.08));ground=float(sample(z,xx,yy));base=ground-.08-(info[model]['bb_min'][2]*scale if f=='rock' else 0)
        placements.append(dict(name=model,alias=aliases[model],family=f,position=[xx,yy,base],heading=float(rng.uniform(0,360)),scale=scale,ground_z=ground,source='existing authored planting location'))
    if len(kept)!=len(a.entities):
        a.entities=kept;dest=O/'porto_filtrado';dest.mkdir(exist_ok=True);save_asset(a,target,dest,path.stem);portmaps.append(path.stem)

# Match the measured Cayo count per total biome area; town plantings count toward the total.
area=plan['cayo_area_m2'];counts=collections.Counter(q['family'] for q in placements)
targets={f:max(counts[f],round(area*D['density_per_m2'][f])) for f in palette}
eligible=fields['eligible'].astype(float);jj,ii=np.where(eligible);density=.35+.65*(.5+.5*np.sin(x[jj,ii]/65+np.sin(y[jj,ii]/110)))
prob=np.cumsum(density.astype(float));prob/=prob[-1];prob[-1]=1.;trees=collections.defaultdict(list);solid=collections.defaultdict(list)
def near(space,xx,yy,radius):
    cell=(math.floor(xx/10),math.floor(yy/10));k=math.ceil(radius/10)
    return any((xx-p[0])**2+(yy-p[1])**2<radius**2 for a in range(cell[0]-k,cell[0]+k+1) for b in range(cell[1]-k,cell[1]+k+1) for p in space[(a,b)])
def occupy(space,xx,yy):space[(math.floor(xx/10),math.floor(yy/10))].append((xx,yy))
for q in placements:
    if q['family']=='tree':occupy(trees,*q['position'][:2])
    if q['family'] in ['tree','rock']:occupy(solid,*q['position'][:2])
for family in ['tree','rock','subcanopy','bush']:
    needed=targets[family]-counts[family];added=0;attempts=0
    while added<needed and attempts<needed*200+1000:
        attempts+=1;k=int(np.searchsorted(prob,rng.random()));xx=float(x[jj[k],ii[k]]+rng.uniform(-dx/2,dx/2));yy=float(y[jj[k],ii[k]]+rng.uniform(-dy/2,dy/2))
        if float(sample(eligible,xx,yy))<.99:continue
        spacing=4.2 if family=='tree' else 2.7 if family=='rock' else .65
        if family=='tree' and near(trees,xx,yy,spacing):continue
        if family!='tree' and near(solid,xx,yy,spacing):continue
        model=pick(family,xx,yy);scale=float(rng.uniform(.85,1.12));ground=float(sample(z,xx,yy));base=ground-.07
        if family=='rock':
            radius=max(np.linalg.norm(np.asarray(info[model]['bb_min'])[:2]),np.linalg.norm(np.asarray(info[model]['bb_max'])[:2]))*scale
            if sample(fields['road_distance'],xx,yy)<radius+2 or sample(fields['clearance'],xx,yy)<radius+10:continue
            base-=info[model]['bb_min'][2]*scale+.2+min(1.,radius*float(sample(fields['slope'],xx,yy))*.45)
        placements.append(dict(name=model,alias=aliases[model],family=family,position=[xx,yy,base],heading=float(rng.uniform(0,360)),scale=scale,ground_z=ground,source='Cayo species proportions and density'))
        if family=='tree':occupy(trees,xx,yy)
        if family in ['tree','rock']:occupy(solid,xx,yy)
        added+=1
    assert added==needed,(family,needed,added)
    print('NATIVE_NATURE_PLACED',family,targets[family],flush=True)

# Reservoirs serve roads and settlements. Use complete tank meshes, not auxiliary pipes.
towers=['h4_mph4_dock_maindock_watertower','h4_mph4_wtowers_watert_02','h4_mph4_wtowers_watert_03','h4_mph4_wtowers_watert_04','prop_air_watertank1']
tower_count=round(area*D['density_per_m2']['water_tower']);selected=[]
for route in plan['routes']:
    points=np.asarray(route['points'])
    for k in np.linspace(0,len(points)-1,4).astype(int):
        xx,yy=points[k,:2]
        for ox,oy in [(23,17),(-23,17),(23,-17),(-23,-17)]:
            tx,ty=xx+ox,yy+oy;sl=float(sample(fields['slope'],tx,ty));gz=float(sample(z,tx,ty))
            if gz<4 or sl>.20 or float(sample(fields['clearance'],tx,ty))<30 or float(sample(water_float,tx,ty))>.01:continue
            if any(math.hypot(tx-q[0],ty-q[1])<100 for q in selected):continue
            n=towers[len(selected)%len(towers)];selected.append((tx,ty));scale=1.;bz=gz-info[n]['bb_min'][2]-.07
            placements.append(dict(name=n,alias=aliases[n],family='water_tower',position=[tx,ty,bz],heading=float(rng.uniform(0,360)),scale=scale,ground_z=gz,source='Roadside reservoir; native Cayo mesh and exact mesh collision'));break
        if len(selected)>=tower_count:break
    if len(selected)>=tower_count:break

# Seat reservoirs on genuinely flat terrain across their whole footprint.
seated=[]
for q in placements:
    if q['family']!='water_tower':continue
    row=info[q['name']];lo=np.array(row['bb_min']);hi=np.array(row['bb_max'])
    corners=np.array([[a,b] for a in [lo[0],0,hi[0]] for b in [lo[1],0,hi[1]]]);radius=max(np.linalg.norm(lo[:2]),np.linalg.norm(hi[:2]))
    candidates=[]
    for ox in range(-100,101,10):
        for oy in range(-100,101,10):
            xx,yy=np.asarray(q['position'][:2])+[ox,oy];points=corners+[xx,yy];h=sample(z,points[:,0],points[:,1])
            if h.min()<4 or h.max()-h.min()>.35:continue
            if sample(fields['road_distance'],xx,yy)<radius+3 or sample(fields['clearance'],xx,yy)<radius+15:continue
            if sample(water_float,xx,yy)>.01 or sample(identity_float,xx,yy)<.99:continue
            if any(np.linalg.norm(np.asarray(t['position'][:2])-[xx,yy])<65 for t in seated):continue
            candidates.append((ox*ox+oy*oy,xx,yy,float(h.max())))
    if not candidates:continue
    _,xx,yy,gz=min(candidates);q['heading']=0.;q['ground_z']=gz;q['position']=[float(xx),float(yy),gz-float(lo[2])-.09];seated.append(q)
placements=[q for q in placements if q['family']!='water_tower']+seated
selected=[q['position'][:2] for q in seated]

groups=collections.defaultdict(list)
for q in placements:groups[(math.floor(q['position'][0]/192),math.floor(q['position'][1]/192))].append(q)
maps=[]
for i,(cell,rows) in enumerate(sorted(groups.items())):
    entities=[];los=[];his=[];sl=[];sh=[];physics=set()
    for j,q in enumerate(rows):
        name=q['name'];v=info[name];theta=math.radians(q['heading']);sc=q['scale'];pos=np.array(q['position']);c,s=math.cos(theta),math.sin(theta);rot=np.array([[c,-s,0],[s,c,0],[0,0,1]])
        corners=np.array([[a,b,c] for a in [v['bb_min'][0],v['bb_max'][0]] for b in [v['bb_min'][1],v['bb_max'][1]] for c in [v['bb_min'][2],v['bb_max'][2]]])*sc;corners=corners@rot.T+pos;lo=corners.min(0);hi=corners.max(0);los.append(lo);his.append(hi);sl.append(lo-v['lod']);sh.append(hi+v['lod'])
        priority=EntityPriorityLevel.REQUIRED if q['family'] in ['tree','subcanopy','bush','water_tower'] else EntityPriorityLevel.OPTIONAL_HIGH
        level=EntityLodLevel.HD if q['family'] in ['tree','subcanopy','bush'] else EntityLodLevel.ORPHANHD
        entities.append(Entity(q['alias'],Vector(pos),Quaternion((math.cos(theta/2),0,0,-math.sin(theta/2))),sc,sc,EntityFlags.IS_STATIC,j+1,-1,v['lod'],0,level,priority,0,255,255,0,[]))
        if (S/(q['alias']+'.ybn')).exists():physics.add(q['alias'])
    n=f'ni_natureza_{i:02}';save_asset(AssetMapData(name=n,content_flags=MapContentFlags.HAS_ENTITIES_HD|MapContentFlags.HAS_PHYSICS,entities=entities,physics_dictionaries=sorted(physics),entities_extents=(Vector(np.min(los,0)),Vector(np.max(his,0))),streaming_extents=(Vector(np.min(sl,0)),Vector(np.max(sh,0)))),target,S,n)
    maps.append(dict(name=n,entities=len(rows),physics=sorted(physics)))

# Cayo also ships a small set of LOD entities in broad streaming cells.  They
# are the reason the island reads as wooded from a boat instead of becoming a
# flat green silhouette.  Reuse the same native drawables and placements, but
# keep only one in eight canopy plants and put them in a physics-free LOD map.
lod_groups=collections.defaultdict(list)
for idx,q in enumerate(placements):
    if q['family'] not in ['tree','subcanopy'] or idx%8:continue
    lod_groups[(math.floor(q['position'][0]/256),math.floor(q['position'][1]/256))].append(q)
lod_maps=[]
for i,(cell,rows) in enumerate(sorted(lod_groups.items())):
    entities=[];los=[];his=[]
    for j,q in enumerate(rows):
        v=info[q['name']];pos=np.asarray(q['position']);sc=q['scale'];theta=math.radians(q['heading']);lo=np.asarray(v['bb_min'])*sc;hi=np.asarray(v['bb_max'])*sc
        corners=np.array([[a,b,c] for a in [lo[0],hi[0]] for b in [lo[1],hi[1]] for c in [lo[2],hi[2]]]);rot=np.array([[math.cos(theta),-math.sin(theta),0],[math.sin(theta),math.cos(theta),0],[0,0,1]]);corners=corners@rot.T+pos;los.append(corners.min(0));his.append(corners.max(0))
        entities.append(Entity(q['alias'],Vector(pos),Quaternion((math.cos(theta/2),0,0,-math.sin(theta/2))),sc,sc,EntityFlags.IS_STATIC,j+1,-1,1600 if q['family']=='tree' else 1200,0,EntityLodLevel.LOD,EntityPriorityLevel.REQUIRED,0,255,255,0,[]))
    n=f'ni_natureza_lod_{i:02}';lo=np.min(los,0);hi=np.max(his,0);save_asset(AssetMapData(name=n,content_flags=MapContentFlags.HAS_ENTITIES_LOD,entities=entities,entities_extents=(Vector(lo),Vector(hi)),streaming_extents=(Vector(lo-2100),Vector(hi+2100))),target,S,n);lod_maps.append(dict(name=n,entities=len(rows),physics=[],lod=True))
maps.extend(lod_maps)
write(O/'dados/implantacao.json',dict(revision=plan['revision'],maps=maps,counts=dict(collections.Counter(q['family'] for q in placements)),targets=targets,filtered_port_maps=portmaps,removed_old_entities=len(removed),models=info,alias_map=aliases,original_drawables_sha256={aliases[n]:sha(v['drawable_file']) for n,v in info.items()},client_visual_verified=False))
write(O/'dados/posicoes.json',placements);write(O/'dados/substituicoes.json',removed)
print('NATURE_READY',len(placements),'entities',len(maps),'lod_entities',sum(m['entities'] for m in lod_maps),'maps',len(selected),'water towers',flush=True)
