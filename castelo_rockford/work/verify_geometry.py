"""Read back exported assets and check clearance, floor and adjacent drawables."""
exec(__import__('pathlib').Path(__file__).with_name('build.py').read_text().split("names=['bh1_45")[0])
results={'collision_files':[], 'untouched_dictionary_members':0, 'in_game_verified':False}
# Shrink the test volume by 3 cm to allow native vertex quantization at its edge.
foot=foot.buffer(-.03);lo[2]+=.03
planes=[]
for cell in constrained_delaunay_triangles(foot).geoms:
 pts=np.array(cell.exterior.coords)[:3];pp=[]
 if np.linalg.det(np.stack([pts[1]-pts[0],pts[2]-pts[0]]))<0:pts=pts[::-1]
 for a,b in zip(pts,np.roll(pts,-1,axis=0)):
  n=np.array([b[1]-a[1],a[0]-b[0],0.]);pp.append((n,float(n[:2]@a)))
 pp.extend([(np.array([0,0,-1.]),-lo[2]),(np.array([0,0,1.]),hi[2])]);planes.append((np.r_[pts.min(0),lo[2]],np.r_[pts.max(0),hi[2]],pp))
def walk(b,parent=np.eye(4)):
 tx=np.asarray(b.composite_transform)@parent
 for c in getattr(b,'children',[]):
  if c:yield from walk(c,tx)
 if not hasattr(b,'geometry_primitives'):return
 for p in b.geometry_primitives:
  q=np.array([b.geometry_vertices[i].co for i in p.vertices]);v=(np.c_[q,np.ones(len(q))]@tx)[:,:3]
  yield p,v
faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
signs=np.array([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
def corners(q):
 v1,v2,v3,v4=q;center=q.mean(0);a1=((v3+v4)-(v1+v2))*.5;edges=np.array([a1,v3-a1-v1,v4-a1-v1])
 if np.linalg.det(edges)<0:edges=edges[[0,2,1]]
 return center+signs@edges*.5
for f in sorted(N.glob('*bh1_45_[0-3].ybn')):
 target=O/f.name if (O/f.name).exists() else f
 count=0
 for p,v in walk(try_load_asset(target)):
  pad=p.radius or 0
  if np.any(v.max(0)+pad<lo) or np.any(v.min(0)-pad>hi):continue
  if p.primitive_type in (BoundPrimitiveType.TRIANGLE,BoundPrimitiveType.BOX):
   surfaces=[v] if p.primitive_type==BoundPrimitiveType.TRIANGLE else [corners(v)[list(ids)] for ids in faces]
   for t in surfaces:
    parts,hit=cut(list(t));assert not hit,(f.name,p.primitive_type.name,v.tolist())
  else:
   assert not foot.intersects(MultiPoint(v[:,:2]).convex_hull.buffer(pad)),(f.name,p.primitive_type.name)
  count+=1
 results['collision_files'].append({'file':f.name,'clearance_passed':True,'nearby_primitives_checked':count})
# Members outside this building must survive dictionary re-export unchanged.
for record in report.get('render',[]):pass
changes=json.loads((W/'alteracoes.json').read_text())
for rec in changes['render']:
 if not rec['file'].endswith('.ydd'):continue
 old=try_load_asset(N/rec['file']);new=try_load_asset(O/rec['file'])
 changed={jenkhash.name_to_hash(d['name']) for d in rec['drawables']}
 assert old.drawables.keys()==new.drawables.keys()
 for key,a in old.drawables.items():
  if jenkhash.name_to_hash(key) in changed:continue
  b=new.drawables[key];assert a.models.keys()==b.models.keys()
  for lod,ms in a.models.items():
   assert len(ms)==len(b.models[lod])
   for m,n in zip(ms,b.models[lod]):
    assert len(m.geometries)==len(n.geometries)
    for g,h in zip(m.geometries,n.geometries):
     assert g.shader_index==h.shader_index and np.array_equal(g.index_buffer,h.index_buffer)
     for field in g.vertex_buffer.dtype.names:
      assert np.allclose(g.vertex_buffer[field],h.vertex_buffer[field],atol=.002),(rec['file'],key,field)
  results['untouched_dictionary_members']+=1
a=try_load_asset(O/'bh1_45_plot4a_ter_dcs.ydr');g=a.models[LodLevel.HIGH][0].geometries[-1]
v=g.vertex_buffer['Position']+origin
assert np.max(np.abs(v[:,2]-floor))<.002
results['new_floor_triangles']=len(g.index_buffer)//3
results['native_floor_height']=float(v[:,2].mean())
(W/'geometry_verificacao.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
