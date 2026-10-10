from common import *
import heapq,math
F=dict(np.load(O/'dados/biomas.npz'));plan=read(O/'dados/plano.json')
gy,gx=np.gradient(z,dy,dx);sl=np.hypot(gx,gy)
step=2;xx=x[::step,::step];yy=y[::step,::step];zz=z[::step,::step];ss=sl[::step,::step];ny,nx=zz.shape
runway=(xx>-855)&(xx<-20)&(yy>-180)&(yy<0)
allowed=(zz>3)&(ss<.9)&~runway&~F['water'][::step,::step]&(F['clearance'][::step,::step]>13)
def nearest(p):
    jj,ii=np.where(allowed);k=np.argmin((xx[jj,ii]-p[0])**2+(yy[jj,ii]-p[1])**2);return int(jj[k]),int(ii[k])
def astar(start_xy,end_xy):
    start=nearest(start_xy);end=nearest(end_xy);queue=[(0.0,0.0,start)];cost={start:0.0};parent={}
    while queue:
        _,g,a=heapq.heappop(queue)
        if g>cost[a]+1e-6:continue
        if a==end:
            chain=[a]
            while a!=start:a=parent[a];chain.append(a)
            return [[float(xx[j,i]),float(yy[j,i])] for j,i in reversed(chain)]
        j,i=a
        for dj,di in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
            b=(j+dj,i+di);jj,ii=b
            if not(0<=jj<ny and 0<=ii<nx and allowed[b]):continue
            d=math.hypot(di*dx*step,dj*dy*step);grade=abs(float(zz[b]-zz[a]))/d
            if grade>.27:continue
            ng=g+d*(1+grade*7+float(ss[b])*2)
            if ng<cost.get(b,1e30):cost[b]=ng;parent[b]=a;heapq.heappush(queue,(ng+math.hypot(xx[b]-xx[end],yy[b]-yy[end]),ng,b))
    raise RuntimeError(f'Rota sem caminho acessivel: {start_xy} -> {end_xy}')
for route in plan['routes']:
    if not route['name'].startswith('Estrada '):continue
    settlement=next(q for q in plan['settlements'][1:] if route['name']=='Estrada '+q['name'])
    cx,cy,_=settlement['center'];start=(80,120) if cx<0 else (680,440);points=astar(start,(cx-65,cy))
    route['points']=[[px,py,float(sample(z,px,py))] for px,py in points]
# Refresh the dirt blend and exclusion distance from the newly graded routes.
road_distance=np.full_like(z,np.inf,dtype=float);dirt=np.zeros_like(z,dtype=float)
for route in plan['routes']:
    d=route_distance(x,y,np.asarray(route['points'],dtype=float));road_distance=np.minimum(road_distance,d-route['width']/2);dirt=np.maximum(dirt,1-smooth(route['width']/2-1,route['width']/2+3,d))
F['road_distance']=road_distance
F['mask'][...,1]=np.rint(np.maximum(F['mask'][...,1]/255,dirt*.97)*255).astype('u1')
F['mask'][...,2]=np.rint((F['mask'][...,2]/255)*(1-dirt)*255).astype('u1')
# Keep vegetation out of the city blocks and village house clearings.
runway_full=(x>-800)&(x<-83)&(y>-115)&(y<-60)
F['eligible']=F['eligible'] & (road_distance>4) & ~runway_full
length=sum(float(np.linalg.norm(np.diff(np.asarray(q['points'])[:,:2],axis=0),axis=1).sum()) for q in plan['routes'])
plan['new_road_length_m']=length;plan['revision']='cayo-encostas-fauna-20261010-3'
write(O/'dados/plano.json',plan);np.savez_compressed(O/'dados/biomas.npz',**F)
print('ROUTES_REPLANNED',[(q['name'],len(q['points'])) for q in plan['routes'] if q['name'].startswith('Estrada ')],round(length,1),flush=True)
