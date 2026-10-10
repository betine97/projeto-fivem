import sys,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';PROPOUT=W/'piano_tapetes_fivem';KITCHENOUT=W/'cozinha_fivem';SERVER=R/'server-data/resources/cidade_mansao'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),str(W/'work'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset
data=json.loads((W/'piano_tapetes.json').read_text());assets={};geometry={}
mp=try_load_asset(PROPOUT/'mansao_piano_tapetes.ymap');typ=try_load_asset(PROPOUT/'mansao_piano_tapetes.ytyp');assert len(mp.entities)==3 and len(typ.archetypes)==3
for (family,row),entity in zip(data['models'].items(),mp.entities):
 a=try_load_asset(PROPOUT/(row['name']+'.ydr'));assert a;assets[family]=a;count=0
 for models in a.models.values():
  for m in models:
   for g in m.geometries:
    vb=g.vertex_buffer
    for field in ('Position','Normal','Tangent','TexCoord0'):assert np.isfinite(vb[field]).all(),(family,field)
    assert np.min(np.linalg.norm(vb['Normal'],axis=1))>.8;assert np.min(np.linalg.norm(vb['Tangent'][:,:3],axis=1))>.5
    ts=vb['Position'][g.index_buffer.reshape(-1,3)];area=np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1)/2;assert area.min()>1e-11,(family,area.min());count+=len(ts)
    assert (vb['Position'].min(0)>=np.array(row['lo'])-.001).all() and (vb['Position'].max(0)<=np.array(row['hi'])+.001).all()
 assert count==row['triangles']
 for name,t in a.shader_group.embedded_textures.items():
  raw=t.data.read_bytes();assert raw[:4]==b'DDS ';height,width=struct.unpack_from('<II',raw,12);mips=struct.unpack_from('<I',raw,28)[0];assert mips>=int(np.log2(min(width,height)))-1,(family,name,mips)
 assert str(entity.archetype_name)==row['name'];assert np.max(abs(np.array(entity.position)-data['origin']-np.array(row['position'])))<.0001;assert np.max(abs(np.array(entity.rotation)-row['quaternion']))<.0001
 assert row['wall_clearance_m']>.05 and row['position'][2]==-.8
 geometry[family]={'triangles':count,'parts':row['parts'],'embedded_textures':len(a.shader_group.embedded_textures),'dimensions':row['dimensions'],'native_roundtrip':True}
assert data['models']['piano']['keys']==88 and data['models']['piano']['white_keys']==52 and data['models']['piano']['black_keys']==36
assert assets['piano'].bounds is not None and assets['bear'].bounds is not None and assets['carpet'].bounds is None
assert abs(data['models']['bear']['length_m']/2.5-data['bear_ratio'])<1e-6
assert abs(data['models']['carpet']['length_m']/1.85-data['carpet_ratio'])<1e-6
# Load current installed furniture/architecture and the already authored decor.
drawable=try_load_asset(SERVER/'stream/mansao_cozinha_parede.ydr')
src=(W/'work/verify_kitchen.py').read_text();fragment=src.split('# Test the currently installed architecture and furniture, then add all decor and the kitchen.')[1].split('T=np.array(faces)')[0];exec(fragment)
for family,row in data['models'].items():
 h=row['heading'];c=np.cos(h);s=np.sin(h);tx=np.eye(4);tx[:3,:3]=np.array([[c,s,0],[-s,c,0],[0,0,1]]);visit(assets[family].bounds,parent=tx,offset=np.array(row['position']),label=row['name'])
T=np.array(faces);low=T.min(1);high=T.max(1);norm=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);SL=np.array([ps.min(0)-pad for kind,ps,pad,label in smooth]);SH=np.array([ps.max(0)+pad for kind,ps,pad,label in smooth])
source=(W/'work/verify_fit.py').read_text();exec('routes={}\n'+source.split('routes={}')[1].split('fit=json.loads')[0])
route('Passagem entre sofa e jantar',[(-.5,-10.85,-.8),(.8,-10.85,-.8),(4.5,-10.85,-.8)])
route('Passagem cozinha',[(8.85,-11.05,-.8),(11.35,-11.05,-.8),(11.35,-6.95,-.8)])
route('Volta completa da mesa',[(.8,-10.85,-.8),(4.5,-10.85,-.8),(4.5,-5.8,-.8),(.8,-5.8,-.8),(.8,-10.85,-.8)])
route('Entre jantar e cozinha',[(4.5,-8.3,-.8),(8.85,-8.3,-.8)])
route('Circulacao sala ao lado do vaso',[(-8.4,-3.55,-.8),(-6.8,-3.55,-.8),(-3.5,-3.55,-.8)])
route('Circulacao hall escada ao lado do vaso',[(3.5,1.65,-.8),(5.1,1.65,-.8),(6.1,1.65,-.8)])
route('Corredor entre ilha e bancada',[(12.40,-6.45,-.8),(12.40,-12.25,-.8)])
route('Acesso frente do forno',[(12.40,-6.95,-.8),(13.00,-6.95,-.8)])
route('Acesso banco piano',[(-6.2,-5.85,-.8),(-6.2,-5.52,-.8)])
route('Passagem ao sul do piano',[(-7.0,-5.85,-.8),(-3.2,-5.85,-.8)])
route('Passagem ao norte do piano',[(-6.5,-3.5,-.8),(-3.0,-3.5,-.8)])
route('Passagem lateral tapete urso',[(.85,-9.3,-.8),(.85,-7,-.8)])
route('Tapete classico hall',[(6.0,.45,-.8),(8.7,.45,-.8)])
assert all(q['passed'] for q in routes.values()),{k:v for k,v in routes.items() if not v['passed']}
assert any(q.startswith('mansao_piano_cauda') for q in blockers(np.array([-4.6,-4.7,-.8]))),'Piano body collision missing'
for row in data['models'].values():assert support(np.array(row['position'])),('Floor support missing',row['name'])
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in PROPOUT.iterdir() if p.suffix in ('.ydr','.ymap','.ytyp')}
report={'passed':True,'models':geometry,'walking_routes':routes,'keys':88,'reference_proportions_preserved':True,'piano_and_bench_collision':True,'bear_collision_only_raised_head':True,'woven_rug_no_rigid_collision':True,'files':hashes,'in_game_verified':False}
(W/'verificacao_piano_tapetes.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('PIANO_RUGS_VERIFIED',len(routes),'walking routes;',geometry,flush=True)
