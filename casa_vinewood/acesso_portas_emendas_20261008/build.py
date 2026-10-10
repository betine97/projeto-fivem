from diagnose import *
import copy,hashlib,shutil,math
import pymateria.gta5.gen8 as g8
from szio.types import Vector
O=P/'package';B=P/'backup';O.mkdir(exist_ok=True);(O/'stream').mkdir(exist_ok=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
if not (P/'baseline.json').exists():
 (P/'baseline.json').write_text(json.dumps({f.relative_to(D).as_posix():sha(f) for f in D.rglob('*') if f.is_file()},indent=2))
baseline=json.loads((P/'baseline.json').read_text())
target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
F=R/'casa_vinewood/fachada_garagem_20261008'
env={'__file__':str(F/'patch_site.py')};exec(compile((F/'patch_site.py').read_text().split('entities=json.loads')[0],str(F/'patch_site.py'),'exec'),env)
subtract=env['subtract_box'];box=(np.array([3.72,16.65,-3.5]),np.array([5.77,17.95,-.7]))
def upright_clip(poly,boxes):
 t=np.array(poly);normal=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);length=np.linalg.norm(normal)
 if length<1e-9 or abs(normal[2])/length>.30:return [poly],False
 return subtract(poly,*box)
env['clip']=upright_clip
report={'collisions':[], 'wall_caps':[], 'palm_removed':True,'in_game_verified':False}
for f in S.glob('*ch2_09b_0.ybn'):
 a=try_load_asset(f);n=env['cut_bound'](a,-origin,[box])
 if n:
  save_asset(a,target,O/'stream',f.stem);report['collisions'].append({'file':f.name,'upright_faces_clipped':n})
  # The new clipping does not touch any horizontal ground surface.
  after=np.array(physical(try_load_asset(O/'stream'/f.name),-origin))
  for x in [3.9,4.745,5.55]:
   edge=16.235+.173*x
   for z in [-2.65,-2.45,-2.2,-1.8]:
    assert not len(intersections([x,edge+.5,z],[x,edge-.20,z],after)),(f.name,x,z)
assert len(report['collisions'])>=3,report['collisions']
# The frontage deletion also deleted end caps at both T junctions. Replace
# only their exposed 10 cm halves; the perpendicular partitions remain.
f=S/'mansao_paredes.ydr';a=try_load_asset(f);raw=g8.Drawable.import_rsc(f).result
caps=[(2.6,2.25,2.35,1),(5.7,2.25,2.35,-1)]
for lod,models in a.models.items():
 for x,y0,y1,nx in caps:
  candidates=[g for m in models for g in m.geometries if len(g.index_buffer) and any(np.all(abs(t[:,:2]-[x,2.35])<.25) for t in g.vertex_buffer['Position'][g.index_buffer.reshape(-1,3)])]
  assert candidates,(lod,x)
  g=candidates[0];vb=g.vertex_buffer;rows=np.zeros(4,dtype=vb.dtype)
  # Duplicate a white plaster vertex to retain vertex colors/material layout.
  rows[:]=vb[0]
  rows['Position']=[[x,y0,-.81],[x,y1,-.81],[x,y1,2.358],[x,y0,2.358]]
  if 'Normal' in vb.dtype.names:rows['Normal']=[nx,0,0]
  if 'Tangent' in vb.dtype.names:rows['Tangent']=[0,1,0,1]
  for key in vb.dtype.names:
   if key.startswith('TexCoord'):rows[key]=[[y0*.5,-.405],[y1*.5,-.405],[y1*.5,1.179],[y0*.5,1.179]]
  off=len(vb);g.vertex_buffer=np.concatenate([vb,rows]);ids=[0,1,2,0,2,3] if nx>0 else [0,2,1,0,3,2]
  g.index_buffer=np.r_[g.index_buffer,np.array(ids,dtype=np.uint16)+off].astype(np.uint16)
 for x,y0,y1,nx in caps:report['wall_caps'].append({'lod':str(lod),'x':x,'y':[y0,y1],'z':[-.81,2.358]})
save_asset(a,target,O/'stream',f.stem)
new=g8.Drawable.import_rsc(O/'stream'/f.name).result
for n,o in zip(new.shader_group.shaders,raw.shader_group.shaders):n.basis_shader=o.basis_shader;n.basis_material=o.basis_material
new.lights=raw.lights;g8.Drawable.export_rsc(new,O/'stream'/f.name)
assert [(s.basis_shader.hash,s.basis_material.hash) for s in new.shader_group.shaders]==[(s.basis_shader.hash,s.basis_material.hash) for s in raw.shader_group.shaders]
# Every road map currently has the marked palm removed at both resolutions.
for f in S.glob('ch2_roads*.ymap'):
 for e in try_load_asset(f).entities:
  if str(e.archetype_name) in ['prop_palm_sm_01d','ch2_props_combo0126_11_lod']:
   assert np.linalg.norm((np.array(e.position)-origin)[:2]-[14.03,15.9])>.1
(P/'geometry_checks.json').write_text(json.dumps(report,indent=2));print('GEOMETRY_READY',len(report['collisions']),len(report['wall_caps']))
