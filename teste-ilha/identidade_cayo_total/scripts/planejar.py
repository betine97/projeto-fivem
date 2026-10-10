from common import *
import importlib.util,heapq,math,xml.etree.ElementTree as ET
spec=importlib.util.spec_from_file_location('terrain_base',P/'porto_construido/scripts/terrain_quality.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
original=np.load(P/'porto_construido/dados/terreno.npz')['terrain'];oldz=original[...,2];land=oldz>0
reference=read(O/'dados/geografia_cayo.json');percent=[0,10,25,50,75,90,95,99,100]
source=np.percentile(oldz[land],percent);target=[0]+list(reference['height_percentiles_m'].values())+[reference['maximum_triangle_centroid_m']]
new=np.where(land,np.interp(oldz,source,target),oldz)
# Preserve water channels, airstrip, the occupied port and its original buildings.
oldfields=dict(np.load(P/'identidade_natural/dados/biomas.npz'))
distance=base.distance_to_sea(oldz,dx,dy)
portdistance=np.hypot(np.maximum(np.maximum(-380-x,x-880),0),np.maximum(np.maximum(-1160-y,y+190),0))
airportdistance=np.hypot(np.maximum(np.maximum(-855-x,x+20),0),np.maximum(np.maximum(-180-y,y),0))
protection=np.minimum(smooth(0,65,portdistance),np.where(oldz<30,smooth(0,45,airportdistance),1))
protection=np.where(oldz>40,1,protection)
protection*=np.where(oldz<20,smooth(0,20,distance),1)
new=oldz*(1-protection)+new*protection
# Regrade river beds and banks together with their actual water quads. The port
# river stays unchanged; upstream water gently rises to 50.6m instead of 173m.
tree=ET.parse(R/'server-data/resources/teste_ilha/data/water.xml');near=np.full(z.shape,np.inf);oldlevel=np.zeros_like(z);newlevel=np.zeros_like(z);changed_water=0
for item in tree.getroot().find('WaterQuads'):
    level=float(item.find('z').get('value'));bounds=[float(item.find(k).get('value')) for k in ['minX','maxX','minY','maxY']]
    if level<=20.5 or bounds[0]>1500:continue
    nlevel=20.5+(level-20.5)*.2;item.find('z').set('value',str(nlevel));changed_water+=1
    a,b,c,d=bounds;dist=np.hypot(np.maximum(np.maximum(a-x,x-b),0),np.maximum(np.maximum(c-y,y-d),0));select=dist<near;near[select]=dist[select];oldlevel[select]=level;newlevel[select]=nlevel
weight=(1-smooth(0,40,near))*land;bed=newlevel+.3*(oldz-oldlevel);new=new*(1-weight)+bed*weight
tree.write(O/'dados/water.xml',encoding='UTF-8',xml_declaration=True)
houses=[q for q in read(P/'porto_construido/dados/posicoes_nativas.json') if q['name'].startswith('pe_estrutura_')]
newhouses=[];settlements=[]
def flatten_rectangle(cx,cy,half_x,half_y,height,margin):
    d=np.hypot(np.maximum(abs(x-cx)-half_x,0),np.maximum(abs(y-cy)-half_y,0));w=(1-smooth(0,margin,d))*land*~oldfields['water'];new[:]=new*(1-w)+height*w
# New city terrace lies beyond the airstrip, preserving the existing harbour neighbourhood.
flatten_rectangle(370,330,305,230,22,140)
settlements.append(dict(name='Cidade principal',center=[370,330,22],existing_buildings=len(houses),new_buildings=250-len(houses),urban_area_m2=610*460))
for row in range(10):
    for col in range(18):
        if len(newhouses)>=250-len(houses):break
        xx=96+32*col;yy=136+32*row
        if 305<xx<435 and 260<yy<365:continue # landscaped central square
        newhouses.append(dict(name=f'pe_estrutura_{1+(row*18+col)%10:02}',position=[xx,yy,22],heading=0 if row%2==0 else 180,scale=1,label='Cidade principal',settlement=0))
villages=[('Vila do Mangue',-600,230,12),('Vila das Palmeiras',-500,800,20),('Vila da Enseada',850,300,11),('Vila da Mata',100,850,25)]
for idx,(name,cx,cy,h) in enumerate(villages,1):
    j=int(round((cy-y[0,0])/dy));i=int(round((cx-x[0,0])/dx));assert land[j,i],name
    flatten_rectangle(cx,cy,65,65,h,100);settlements.append(dict(name=name,center=[cx,cy,h],houses=16,clearing_area_m2=130**2))
    for rr in range(4):
        for cc in range(4):
            xx=cx-48+32*cc;yy=cy-48+32*rr
            newhouses.append(dict(name=f'pe_estrutura_{1+(idx*7+rr*4+cc)%8:02}',position=[xx,yy,h],heading=0 if rr%2==0 else 180,scale=1,label=name,settlement=idx))
entrance_level=float(sample(oldz,250,-160));w=(1-smooth(7,32,abs(x-250)))*(1-smooth(0,40,np.maximum(np.maximum(-160-y,y-120),0)))*land
profile=entrance_level+(22-entrance_level)*np.clip((y+160)/280,0,1);new[:]=new*(1-w)+profile*w
grid[:]=original;grid[...,2]=new;z[:]=new
np.savez_compressed(O/'dados/terreno.npz',terrain=grid)
gy,gx=np.gradient(z,dy,dx);slope=np.hypot(gx,gy);normals=np.stack([-gx,-gy,np.ones_like(z)],-1);normals/=np.linalg.norm(normals,axis=-1,keepdims=True);tangents=np.stack([np.ones_like(z),np.zeros_like(z),gx],-1);tangents-=normals*(normals*tangents).sum(-1,keepdims=True);tangents/=np.linalg.norm(tangents,axis=-1,keepdims=True)
shore=base.distance_to_sea(z,dx,dy);clearance=np.full(z.shape,np.inf)
for q in houses+newhouses:
    xx,yy,_=q['position'];clearance=np.minimum(clearance,np.hypot(x-xx,y-yy))
runway=(x>-855)&(x<-20)&(y>-180)&(y<0);water=oldfields['water'];routes=[]
def route(name,points,width):routes.append(dict(name=name,points=[[float(a),float(b),float(sample(z,a,b))] for a,b in points],width=width,new=True))
for yy in range(120,505,64):route('Rua da cidade '+str(yy),[(80,yy),(680,yy)],9)
for xx in [80,272,464,680]:route('Travessa da cidade '+str(xx),[(xx,120),(xx,504)],9)
route('Ligacao ao porto',[(250,-160),(250,120),(272,120)],10)
for name,cx,cy,h in villages:
    for yy in [cy-64,cy,cy+64]:route(name+' rua '+str(yy),[(cx-65,yy),(cx+65,yy)],7)
    route(name+' travessa',[(cx-65,cy-64),(cx-65,cy+64)],7)
step=2;xx=x[::step,::step];yy=y[::step,::step];zz=z[::step,::step];ss=slope[::step,::step];ny,nx=zz.shape
allowed=(zz>3)&(ss<.9)&~runway[::step,::step]&~water[::step,::step]&(clearance[::step,::step]>13)
def nearest(p):
    jj,ii=np.where(allowed);k=np.argmin((xx[jj,ii]-p[0])**2+(yy[jj,ii]-p[1])**2);return int(jj[k]),int(ii[k])
def astar(start,end):
    start=nearest(start);end=nearest(end);queue=[(0,0,start)];cost={start:0};parent={}
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
    raise RuntimeError('Village road unreachable '+str((start,end)))
for name,cx,cy,h in villages:route('Estrada '+name,astar((80,120) if cx<0 else (680,440),(cx-65,cy)),8)
for q in read(P/'identidade_natural/dados/plano.json')['routes']:
    if not q['new']:route(q['name'],[p[:2] for p in q['points']],q['width'])
road_distance=np.full_like(z,np.inf);dirt=np.zeros_like(z)
for q in routes:
    d=route_distance(x,y,np.asarray(q['points']));road_distance=np.minimum(road_distance,d-q['width']/2);dirt=np.maximum(dirt,1-smooth(q['width']/2-1,q['width']/2+3,d))
patch=.5+.24*np.sin(x/29+.6*np.sin(y/57))+.16*np.sin(y/31-x/73)
sand=(1-smooth(7,28+9*np.sin(x/77+y/115),shore))*(1-smooth(8,18,z))*(1-smooth(.48,.80,slope));sand=np.where(z<=.3,1,sand)
mud=(.075+.11*patch)*(1-smooth(.4,.75,slope));mud=np.maximum(mud,(1-smooth(0,20,base.distance_to_sea(np.where(water,0,100),dx,dy)))*.8)*(1-sand)*smooth(.3,1.6,z)
rock=smooth(.42,.95,slope)*smooth(1,10,z);g=np.maximum(mud,rock);b=np.maximum(sand,rock);g=np.maximum(g,dirt*.97);b=np.where(dirt>.1,b*(1-dirt),b)
mask=np.zeros(z.shape+(4,),np.uint8);mask[...,1]=np.rint(g*255);mask[...,2]=np.rint(b*255);mask[...,3]=255
eligible=land&(z>3)&(slope<.65)&~runway&~water&(clearance>19)&(road_distance>4)
eligible&=~((x>65)&(x<685)&(y>100)&(y<570))
for _,cx,cy,_ in villages:eligible&=~((abs(x-cx)<80)&(abs(y-cy)<80))
eligible&=~((x>-275)&(x<800)&(y>-1030)&(y<-190))
np.savez_compressed(O/'dados/biomas.npz',identity=land,blend=land.astype(float),mask=mask,normals=normals.astype('f4'),tangents=tangents.astype('f4'),shore=shore,slope=slope,eligible=eligible,road_distance=road_distance,water=water,clearance=clearance)
area=float(land.sum()*dx*dy);length=sum(float(np.linalg.norm(np.diff(np.asarray(q['points'])[:,:2],axis=0),axis=1).sum()) for q in routes)
write(O/'dados/cidade.json',dict(main_city_buildings=250,preserved_buildings=len(houses),additional_city_buildings=250-len(houses),villages=4,village_buildings=64,settlements=settlements,placements=newhouses))
write(O/'dados/plano.json',dict(revision='identidade-cayo-total-20261009-1',land_area_m2=area,cayo_area_m2=area,cayo_fraction=1.0,selection='Whole-island Cayo palette and area-weighted relief adaptation, with protected harbour and airstrip; upstream river bed, bank and water regraded together; main city and four connected village clearings.',eligible_area_m2=float(eligible.sum()*dx*dy),new_road_length_m=length,routes=routes,terrain_geometry_unchanged=False,changed_water_quads=changed_water,original_height_max=float(oldz.max()),new_height_max=float(z.max()),settlements=settlements))
assert len(newhouses)==250-len(houses)+64
assert np.all(grid[...,2][~land]==original[...,2][~land])
for q in houses:assert abs(sample(z,*q['position'][:2])-sample(oldz,*q['position'][:2]))<.01,q
print('TOTAL_CAYO_PLAN',area,length,len(newhouses),'max_height',float(z.max()),flush=True)
