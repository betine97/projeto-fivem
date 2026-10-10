"""Regrade the airport shoulder and upstream channel; preserve buildings/coast."""
from common import *
import xml.etree.ElementTree as ET
baseline=O/'backups/relevo-20261010-004220/dados'
old=np.load(baseline/'terreno.npz')['terrain'][...,2].copy();F=dict(np.load(baseline/'biomas.npz'));plan=read(baseline/'plano.json')
def blur(v,sigma):
    r=int(sigma*3);k=np.exp(-np.arange(-r,r+1,dtype=float)**2/(2*sigma*sigma));k/=k.sum()
    for axis in [0,1]:v=np.apply_along_axis(lambda a:np.convolve(np.pad(a,(r,r),mode='edge'),k,mode='valid'),axis,v)
    return v
tree=ET.parse(baseline/'water.xml');near=np.full(z.shape,np.inf);change=np.zeros_like(z);level=np.zeros_like(z);signed=np.full(z.shape,np.inf)
changed=[]
for q in tree.getroot().find('WaterQuads'):
    a,b,c,d,h=[float(q.find(k).get('value')) for k in ['minX','maxX','minY','maxY','z']]
    if a>1500 or h<=20.5:continue
    nh=27.0 if h>=50.9 else 20.5+6.5*np.clip(((c+d)*.5+74)/818,0,1)
    q.find('z').set('value',f'{nh:.4f}')
    dist=np.hypot(np.maximum(np.maximum(a-x,x-b),0),np.maximum(np.maximum(c-y,y-d),0))
    take=dist<near;change[take]=nh-h;level[take]=nh;near[take]=dist[take]
    inside=(x>=a)&(x<=b)&(y>=c)&(y<=d)
    signed=np.minimum(signed,np.where(inside,-np.minimum.reduce([x-a,b-x,y-c,d-y]),dist))
    changed.append([a,b,c,d,h,float(nh)])
work=old+change*(1-smooth(0,140,near))
# Gaussian regrading removes the old hard protection threshold at 30/40 metres.
smooth_z=blur(work,7)
airport=np.hypot(np.maximum(np.maximum(-890-x,x+15),0),np.maximum(np.maximum(-210-y,y-40),0))
region=np.maximum(1-smooth(0,100,airport),1-smooth(0,170,near))
protection=smooth(0,20,old)  # keep the coastline and underwater floor stable
port=(x>-380)&(x<880)&(y<-190)&(y>-1160)
protection[port]=0
protection[(x>65)&(x<685)&(y>100)&(y<570)]=0
for q in plan['settlements'][1:]:
    cx,cy,_=q['center'];protection[(abs(x-cx)<80)&(abs(y-cy)<80)]=0
# Exact house footprints, including the 250-house city and four villages.
houses=read(P/'porto_construido/dados/posicoes_nativas.json')+read(O/'dados/cidade.json')['placements']
for q in houses:
    if not q['name'].startswith('pe_estrutura_'):continue
    xx,yy,_=q['position'];protection*=smooth(16,35,np.hypot(x-xx,y-yy))
new=old+(smooth_z-old)*region*protection
# Runway is only 31m wide. Its previous 180m exclusion left a bare artificial ridge.
run_dist=np.hypot(np.maximum(np.maximum(-792-x,x+91),0),np.maximum(np.maximum(-107-y,y+68),0))
run_weight=(1-smooth(0,70,run_dist))*(old>0)
new=new*(1-run_weight)+18*run_weight
# Seat a continuous low upstream river with a bank above its water surface.
bed=level+np.where(signed<0,-1.35*smooth(0,5,-signed),.85)
w=(1-smooth(0,24,near))*protection
new=new*(1-w)+bed*w
z[:]=new;grid[...,2]=new
np.savez_compressed(O/'dados/terreno.npz',terrain=grid)
gy,gx=np.gradient(new,dy,dx);slope=np.hypot(gx,gy);norm=np.stack([-gx,-gy,np.ones_like(new)],-1);norm/=np.linalg.norm(norm,axis=-1,keepdims=True)
tangent=np.stack([np.ones_like(new),np.zeros_like(new),gx],-1);tangent-=norm*(norm*tangent).sum(-1,keepdims=True);tangent/=np.linalg.norm(tangent,axis=-1,keepdims=True)
F['normals']=norm.astype('f4');F['tangents']=tangent.astype('f4');F['slope']=slope
runway=(x>-800)&(x<-83)&(y>-115)&(y<-60)
F['eligible']|=(region>.2)&(new>3)&(slope<.65)&~F['water']&(F['clearance']>19)&(F['road_distance']>4)&~runway&~port
F['eligible']&=~runway&(slope<.65)
# Replace old rock masks on regraded slopes with the existing Cayo grassy palette.
oldrock=smooth(.42,.95,np.hypot(*np.gradient(old,dy,dx)))
rock=smooth(.42,.95,slope);take=(abs(new-old)>.01)&(F['road_distance']>3)
F['mask'][...,1]=np.where(take,np.maximum(.09,rock)*255,F['mask'][...,1]).astype('u1')
F['mask'][...,2]=np.where(take,rock*255,F['mask'][...,2]).astype('u1')
np.savez_compressed(O/'dados/biomas.npz',**F)
tree.write(O/'dados/water.xml',encoding='UTF-8',xml_declaration=True)
for route in plan['routes']:
    for p in route['points']:p[2]=float(sample(z,p[0],p[1]))
plan['revision']='cayo-encostas-fauna-20261010-2';write(O/'dados/plano.json',plan)
write(O/'dados/correcao_encostas.json',dict(changed_vertices=int((abs(new-old)>.01).sum()),water_quads=changed,runway_clear_bounds=[-800,-83,-115,-60],max_before=float(np.hypot(*np.gradient(old,dy,dx)).max()),max_after=float(slope.max()),in_game_visual_verified=False))
print('ENCOSTAS_REGRADADAS',int((abs(new-old)>.01).sum()),'AGUA',len(changed),flush=True)
