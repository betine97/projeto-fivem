exec(__import__('pathlib').Path(__file__).with_name('inspect_assets.py').read_text().split('sources=')[0])
from szio.gta5 import LodLevel
from collections import Counter
es=json.loads((W/'entities.json').read_text())
for name in ['bh1_45_plot4a_ter_dcs','bh1_45_plot4a_d2_1','bh1_45_plot4a_d2_2','bh1_45_plot4a_d2_3','bh1_45_plot4a_d_4','bh1_45_plot4a_d_5','bh1_45_em_c']:
 a=try_load_asset(N/(name+'.ydr'));pos=np.array(next(e['pos'] for e in es if e['name']==name))
 print('\nMODEL',name)
 for m in a.models[LodLevel.HIGH]:
  for i,g in enumerate(m.geometries):
   s=a.shader_group.shaders[g.shader_index];tex=next((str(p.value) for p in s.parameters if p.name.lower()=='diffusesampler'),'');v=g.vertex_buffer['Position']+pos;t=v[g.index_buffer.reshape(-1,3)]
   print(i,g.shader_index,tex,len(t),'lo',np.round(t.min((0,1)),2),'hi',np.round(t.max((0,1)),2))
print('\nCOLLISION')
for f in N.glob('*bh1_45_*.ybn'):
 a=try_load_asset(f)
 def walk(b,parent=np.eye(4),path=()):
  tx=np.asarray(b.composite_transform)@parent
  for j,c in enumerate(getattr(b,'children',[])):
   if c:walk(c,tx,path+(j,))
  if hasattr(b,'geometry_primitives'):
   v=np.array([q.co for q in b.geometry_vertices]);v=(np.c_[v,np.ones(len(v))]@tx)[:,:3]
   if np.all(v.max(0)>[-997,175,63]) and np.all(v.min(0)<[-915,237,84]):print(f.name,path,'lo',np.round(v.min(0),2),'hi',np.round(v.max(0),2),'prims',len(b.geometry_primitives),Counter(p.primitive_type.name for p in b.geometry_primitives))
 walk(a)
