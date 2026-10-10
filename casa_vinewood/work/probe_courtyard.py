from pathlib import Path
exec(Path(__file__).with_name('verify_fit.py').read_text().split('routes={}')[0])
for label in ['ch2_09b_3.ybn:1673','hi@ch2_09b_3.ybn:5217']:
 for i,value in enumerate(labels):
  if value==label:print('BLOCKING_GEOMETRY',label,T[i].tolist())
for y in [6.6,6.9,7.0,7.1,7.5,7.7,7.9,8.1]:
 for x in [.4,.9,1.2,1.5]:
  hits=blockers(np.array([x,y,-.8]))
  if hits:print('COURTYARD_OBSTACLE',x,y,hits)
for x,y in [(2.3,8.1),(2.3,7.9),(2.3,7.34),(2.3,6.98),(.1,6.98),(-.4,6.98),(-1.1,6.98),(-2.2,6.98)]:
 mask=(norm[:,2]>1e-7)&(low[:,0]<=x)&(high[:,0]>=x)&(low[:,1]<=y)&(high[:,1]>=y);ix=np.flatnonzero(mask);ns=norm[ix];ts=T[ix]
 zs=ts[:,0,2]-(ns[:,0]*(x-ts[:,0,0])+ns[:,1]*(y-ts[:,0,1]))/ns[:,2];found=[]
 for i,z in zip(ix,zs):
  if -1.2<z<.1 and distance(np.array([x,y,z]),T[i:i+1])[0]<.005:found.append((round(z,4),labels[i]))
 print('GROUND',x,y,sorted(set(found)))
 print('BLOCKED_AT_MINUS_08',blockers(np.array([x,y,-.8])))
