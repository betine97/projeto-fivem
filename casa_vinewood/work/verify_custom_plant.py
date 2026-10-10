import sys,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';PLANTOUT=W/'vaso_fivem'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work/pydeps'),str(W/'work'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
import numpy as np
from szio.gta5 import try_load_asset
custom=json.loads((W/'vaso_planta_autoral.json').read_text());drawable=try_load_asset(PLANTOUT/(custom['model']+'.ydr'));assert drawable and drawable.bounds
geos=[g for lod in drawable.models.values() for m in lod for g in m.geometries];count=0
for g in geos:
 vb=g.vertex_buffer
 for field in ('Position','Normal','Tangent','TexCoord0'):assert np.isfinite(vb[field]).all(),field
 assert np.min(np.linalg.norm(vb['Normal'],axis=1))>.8
 assert np.min(np.linalg.norm(vb['Tangent'][:,:3],axis=1))>.5
 tris=vb['Position'][g.index_buffer.reshape(-1,3)];area=np.linalg.norm(np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]),axis=1)/2
 assert np.min(area)>1e-11,np.min(area);count+=len(tris)
assert count==custom['triangles'];assert len(drawable.shader_group.embedded_textures)==12
for name,tex in drawable.shader_group.embedded_textures.items():
 data=tex.data.read_bytes();assert data[:4]==b'DDS ';height,width=struct.unpack_from('<II',data,12);mips=struct.unpack_from('<I',data,28)[0]
 assert width&(width-1)==0 and height&(height-1)==0 and mips>=int(np.log2(max(width,height)))-1,(name,width,height,mips)
mp=try_load_asset(PLANTOUT/'mansao_vasos_autorais.ymap');typ=try_load_asset(PLANTOUT/'mansao_vasos_autorais.ytyp');assert len(mp.entities)==2 and len(typ.archetypes)==1
for row,entity in zip(custom['instances'],mp.entities):
 assert str(entity.archetype_name)==custom['model'];assert np.max(abs(np.array(entity.position)-custom['origin']-np.array(row['position'])))<.0001
 assert np.max(abs(np.array(entity.rotation)-row['quaternion']))<.0001
 assert row['wall_clearance_m']>.2 and row['position'][2]==-.8
 assert row['door_swing_clear']
# Include all previously installed architecture, native pots and paintings in the route checks.
source=(W/'work/verify_decor_lighting.py').read_text();exec(source.split('# Exercise the actual Lua loop')[0])
for row in custom['instances']:
 h=row['heading'];c=np.cos(h);s=np.sin(h);tx=np.eye(4);tx[:3,:3]=np.array([[c,s,0],[-s,c,0],[0,0,1]])
 visit(drawable.bounds,parent=tx,offset=np.array(row['position']),label='custom_pot_'+row['name'])
T=np.array(faces);low=T.min(1);high=T.max(1);norm=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);SL=np.array([ps.min(0)-pad for kind,ps,pad,label in smooth]);SH=np.array([ps.max(0)+pad for kind,ps,pad,label in smooth])
source=(W/'work/verify_fit.py').read_text();exec('routes={}\n'+source.split('routes={}')[1].split('fit=json.loads')[0])
route('Passagem entre sofa e jantar',[(-.5,-10.85,-.8),(.8,-10.85,-.8),(4.5,-10.85,-.8)])
route('Passagem cozinha',[(8.85,-11.05,-.8),(11.35,-11.05,-.8),(11.35,-6.95,-.8)])
route('Volta completa da mesa',[(.8,-10.85,-.8),(4.5,-10.85,-.8),(4.5,-5.8,-.8),(.8,-5.8,-.8),(.8,-10.85,-.8)])
route('Entre jantar e cozinha',[(4.5,-8.3,-.8),(8.85,-8.3,-.8)])
route('Circulacao sala ao lado do vaso',[(-8.4,-3.55,-.8),(-6.8,-3.55,-.8),(-3.5,-3.55,-.8)])
route('Circulacao hall escada ao lado do vaso',[(3.5,1.65,-.8),(5.1,1.65,-.8),(6.1,1.65,-.8)])
assert all(q['passed'] for q in routes.values()),{k:v for k,v in routes.items() if not v['passed']}
for row in custom['instances']:
 p=np.array(row['position']);assert support(p)
 assert any(x.startswith('custom_pot_') for x in blockers(p)),'Pot collision must be present'
 assert not any(x.startswith('custom_pot_') for x in blockers(p+np.array([.70,0,0]))),'Leaves must not block the player'
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in PLANTOUT.iterdir() if p.suffix in ('.ydr','.ymap','.ytyp')}
report=dict(passed=True,revision=custom['revision'],model=custom['model'],instances=2,leaves=custom['leaves'],triangles=count,material_textures=12,native_roundtrip=True,geometry_finite=True,texture_mipmaps=True,pot_collision_only=True,walking_routes=routes,placements=custom['instances'],files=hashes,in_game_verified=False)
(W/'verificacao_vasos_autorais.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('CUSTOM_PLANTS_VERIFIED',len(routes),'routes;',count,'triangles; 12 mipmapped textures',flush=True)
