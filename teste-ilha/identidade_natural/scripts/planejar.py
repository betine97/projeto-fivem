from common import *
import importlib.util,heapq,math,collections
spec=importlib.util.spec_from_file_location('terrain_base',P/'porto_construido/scripts/terrain_quality.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
_,normals,tangents,oldmask,shore=base.fields()
land=z>0;area=float(land.sum()*dx*dy)
# A connected lowland biome; irregular contour follows elevation rather than a straight dividing wall.
score=z+.025*y+.018*x+5*np.sin(x/155+y/190)
threshold=float(np.median(score[land]));identity=(score<=threshold)&land
blend=1-smooth(threshold-12,threshold+12,score)
gy,gx=np.gradient(z,dy,dx);slope=np.hypot(gx,gy)
houses=[q for q in read(P/'porto_construido/dados/posicoes_nativas.json') if q['name'].startswith('pe_estrutura_')]
clearance=np.full(z.shape,np.inf)
for q in houses:
    xx,yy,_=q['position'];clearance=np.minimum(clearance,np.hypot(x-xx,y-yy))
runway=(x>-855)&(x<-20)&(y>-180)&(y<0)
old=np.load(P/'dados/terreno.npz')
rd,rz,rw=base.river_distance(x,y,old['river_points'],old['river_z'],old['river_halfwidth'])
water=(rd<rw+3)&(z<rz+2)
port=(x>-380)&(x<880)&(y>-1160)&(y<70)
water[port]=False
riverx=-35+32*np.sin((y+900)/125);water|=port&(y>-950)&(y<-55)&(abs(x-riverx)<16)

# Routes are traced on the current collision surface. Reject steep cuts and waterways.
step=2;xx=x[::step,::step];yy=y[::step,::step];zz=z[::step,::step];ss=slope[::step,::step]
allowed=(zz>3)&(ss<.52)&~runway[::step,::step]&~water[::step,::step]&(clearance[::step,::step]>25)
ny,nx=zz.shape
def cell(p):return (int(round((p[1]-y[0,0])/(dy*step))),int(round((p[0]-x[0,0])/(dx*step))))
def nearest(p):
    j,i=cell(p);jj,ii=np.where(allowed);k=np.argmin((xx[jj,ii]-p[0])**2+(yy[jj,ii]-p[1])**2);return int(jj[k]),int(ii[k])
def astar(start,end):
    start=nearest(start);end=nearest(end);queue=[(0,0,start)];cost={start:0};parent={}
    while queue:
        _,g,a=heapq.heappop(queue)
        if g>cost[a]+1e-6:continue
        if a==end:
            chain=[a]
            while a!=start:a=parent[a];chain.append(a)
            return [[float(xx[j,i]),float(yy[j,i]),float(zz[j,i])] for j,i in reversed(chain)]
        j,i=a
        for dj,di in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
            b=(j+dj,i+di);jj,ii=b
            if not(0<=jj<ny and 0<=ii<nx and allowed[b]):continue
            dist=math.hypot(di*dx*step,dj*dy*step);grade=abs(float(zz[b]-zz[a]))/dist
            if grade>.28:continue
            new=g+dist*(1+grade*7+float(ss[b])*3)
            if new<cost.get(b,1e30):
                cost[b]=new;parent[b]=a;h=math.hypot(xx[b]-xx[end],yy[b]-yy[end]);heapq.heappush(queue,(new+h,new,b))
    return None
routes=[]
for name,start,end,width in [('Estrada litoral leste',(800,-600),(950,-50),8),('Ramal do reservatorio',(780,-580),(650,-280),7),('Trilha da mata oeste',(-380,-280),(-580,-470),7),('Caminho do mangue',(-430,-430),(-520,-820),7),('Subida da serra',(-580,-470),(-650,500),6),('Estrada da costa sul',(80,-1100),(650,-1050),8),('Ramal da mata norte',(-650,500),(-450,820),6)]:
    points=astar(start,end)
    if points is None:print('ROUTE_UNREACHABLE',name,flush=True);continue
    # Remove only collinear grid steps; every original contour turn is retained.
    compact=[points[0]]
    for a,b,c in zip(points[:-2],points[1:-1],points[2:]):
        v=np.array(b[:2])-a[:2];w=np.array(c[:2])-b[:2]
        if abs(v[0]*w[1]-v[1]*w[0])>1e-5:compact.append(b)
    compact.append(points[-1]);routes.append(dict(name=name,points=compact,width=width,new=True))
plan=read(P/'porto_esperanca/dados/implantacao.json')
for q in plan['rotas']:
    if q['kind']=='terra':routes.append(dict(name='Trilha existente do rio',points=(np.asarray(q['points'])+np.array([250,-850])).tolist(),width=q['width'],new=False))
dirt=np.zeros_like(z);road_distance=np.full_like(z,np.inf)
for q in routes:
    d=route_distance(x,y,np.array(q['points']));road_distance=np.minimum(road_distance,d-q['width']/2)
    dirt=np.maximum(dirt,1-smooth(q['width']/2-1,q['width']/2+3,d))
g=oldmask[...,1].astype(float)/255;b=oldmask[...,2].astype(float)/255
# Cayo track has its own dirt layer; red mud remains along wet banks.
g=np.maximum(g,dirt*.97);b=np.where(dirt>.1,b*(1-dirt),b)
mountain=smooth(100,200,z)
rock=np.maximum(smooth(.35,.9,slope)*smooth(30,100,z),mountain*(.65+.20*np.sin(x/60+y/90)**2))
g=np.maximum(g,rock);b=np.maximum(b,rock)
mask=np.zeros(z.shape+(4,),np.uint8);mask[...,1]=np.rint(g*255);mask[...,2]=np.rint(b*255);mask[...,3]=255
eligible=identity&(z>3)&(slope<.63)&~runway&~water&(clearance>28)&(road_distance>4)
# Respect town circulation and yards, retaining the original authored plantings there.
eligible&=~((x>-275)&(x<800)&(y>-1030)&(y<-190))
np.savez_compressed(O/'dados/biomas.npz',identity=identity,blend=blend,mask=mask,normals=normals,tangents=tangents,shore=shore,slope=slope,eligible=eligible,road_distance=road_distance,water=water,clearance=clearance)
length=sum(float(np.linalg.norm(np.diff(np.asarray(q['points'])[:,:2],axis=0),axis=1).sum()) for q in routes if q['new'])
report=dict(revision='identidade-cayo-chiliad-20261009-1',land_area_m2=area,cayo_area_m2=float(identity.sum()*dx*dy),cayo_fraction=float(identity.sum()/land.sum()),threshold=threshold,selection='Contiguous lower terrain with irregular elevation contour; 50 percent of projected dry-land grid footprint. Remaining mountain surfaces reference Chiliad.',eligible_area_m2=float(eligible.sum()*dx*dy),new_road_length_m=length,routes=routes,terrain_geometry_unchanged=True,collision_surfaces_to_update=True)
write(O/'dados/plano.json',report)
print('IDENTITY_PLAN',{k:v for k,v in report.items() if k!='routes'},flush=True)
