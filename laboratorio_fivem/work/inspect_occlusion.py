exec(open(__file__.replace('inspect_occlusion.py','audit_occlusion.py')).read().split('for p in')[0])
pd=json.loads((w.parent/'placement.json').read_text());basis=np.array(pd['basis'])
for p in (w/'base_assets').glob('*occl*.ymap'):
 a=try_load_asset(p)
 for i,b in enumerate(a.model_occluders):
  xyz=(b.vertices-origin)@basis
  for j,t in enumerate(b.indices):
   v=xyz[t]
   if np.all(v.max(0)>[-5,-9,-1]) and np.all(v.min(0)<[5,7,5]):print(p.name,i,j,np.round(v,2).tolist())
