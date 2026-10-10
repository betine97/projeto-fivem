from pathlib import Path
path=Path(__file__).with_name('verify_fit.py');scope={'__file__':str(path)}
exec(path.read_text().split("route('entrada_original'")[0],scope)
np=scope['np'];T=scope['T'];labels=scope['labels'];distance=scope['distance'];support=scope['support']
for foot in [(5.85,-12.9,-.8),(-.6,6.98,-.8),(.976,5.05,1.004),(.4,1.52,-.758),(-.514,2.05,2.808)]:
 p=np.array(foot);q=p+[0,0,.85];ds=distance(q,T)
 print('\nFOOT',foot,'support',support(p))
 for i in np.flatnonzero(ds<.301)[:6]:print('BLOCK',labels[i],'distance',ds[i],np.round(T[i],4).tolist())
 if not support(p):
  norm=scope['norm'];lo=scope['low'];hi=scope['high'];mask=(norm[:,2]>1e-6)&(lo[:,0]<p[0])&(hi[:,0]>p[0])&(lo[:,1]<p[1])&(hi[:,1]>p[1]);ix=np.flatnonzero(mask)
  ds=distance(p,T[ix]);best=ix[np.argsort(ds)[:4]]
  for i in best:print('SUPPORT?',labels[i],np.round(T[i],4).tolist())
