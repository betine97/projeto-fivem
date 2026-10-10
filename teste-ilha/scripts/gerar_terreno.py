from pathlib import Path
import sys,json,math
P=Path(__file__).resolve().parents[1];R=P.parent
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps')]
import numpy as np
from PIL import Image,ImageDraw,ImageFont
for name in ['dados','texturas','previews','exportacoes']:(P/name).mkdir(exist_ok=True)
ref=json.loads((P/'referencia_tecnica/medicao_cayo.json').read_text());n=769;seed=90321;rng=np.random.default_rng(seed);u=np.linspace(-1.36,1.36,n);v=np.linspace(-1.44,1.44,n);U,V=np.meshgrid(u,v);X=U*1100;Y=V*1370
def smooth(a,b,t):
 z=np.clip((t-a)/(b-a),0,1);return z*z*(3-2*z)
def noise(cells):
 a=rng.random((cells+1,cells+1))*2-1;ix=np.linspace(0,cells-1e-5,n);I,J=np.meshgrid(ix,ix);i=I.astype(int);j=J.astype(int);fx=smooth(0,1,I-i);fy=smooth(0,1,J-j)
 return (a[j,i]*(1-fx)+a[j,i+1]*fx)*(1-fy)+(a[j+1,i]*(1-fx)+a[j+1,i+1]*fx)*fy
coarse=noise(8);rough=noise(32);fine=noise(96);micro=noise(250)
theta=np.arctan2(V,U);rho=np.sqrt(U*U+V*V);shore=1+.08*np.sin(3*theta+.7)+.06*np.cos(5*theta-.4)+.025*np.sin(11*theta)+.014*np.cos(19*theta)
shore-=.20*np.exp(-((np.angle(np.exp(1j*(theta+1.08))))/.29)**2)
distance=(shore-rho)*1100
H=np.where(distance>0,np.minimum(distance*.085,16),np.maximum(distance*.28,-65));inside=smooth(10,190,distance)
def hill(x,y,sx,sy,h):return h*np.exp(-((U-x)/sx)**2-((V-y)/sy)**2)
mountains=hill(.36,.36,.36,.46,290)+hill(-.30,.43,.28,.28,215)+hill(.05,.03,.29,.39,105)+hill(-.26,-.41,.35,.28,108)+hill(.57,-.19,.25,.24,65)
ridge=1-np.abs(coarse);H+=inside*(mountains+11+18*coarse+12*rough+5*fine+1.5*micro+25*ridge*np.clip(mountains/200,0,1))
# Talus redistribution breaks smooth procedural hills into natural weathered slopes.
for iteration in range(24):
 for axis in [0,1]:
  d=np.diff(H,axis=axis);limit=6.0;flow=np.maximum(np.abs(d)-limit,0)*.055*np.sign(d)
  if axis==0:H[:-1]+=flow;H[1:]-=flow
  else:H[:,:-1]+=flow;H[:,1:]-=flow
# The river centerline is a smooth Catmull-Rom spline, continuously descending to sea.
control=np.array([[-.08,.62],[-.08,.49],[.025,.30],[-.04,.15],[.13,-.07],[.04,-.25],[.23,-.42],[.19,-.58],[.40,-.74],[.52,-.88],[.62,-1.04],[.74,-1.21]])
pts=[]
for i in range(len(control)-1):
 p0=control[max(0,i-1)];p1=control[i];p2=control[i+1];p3=control[min(len(control)-1,i+2)]
 for t in np.linspace(0,1,36,endpoint=False):pts.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3))
pts=np.array(pts+[control[-1]])*np.array([1100,1370]);lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))];fraction=lengths/lengths[-1]
def sample(field,x,y):
 ix=np.clip((np.asarray(x)-X[0,0])/(X[0,-1]-X[0,0])*(n-1),0,n-1);iy=np.clip((np.asarray(y)-Y[0,0])/(Y[-1,0]-Y[0,0])*(n-1),0,n-1);a=np.minimum(ix.astype(int),n-2);b=np.minimum(iy.astype(int),n-2);tx=ix-a;ty=iy-b
 return (field[b,a]*(1-tx)+field[b,a+1]*tx)*(1-ty)+(field[b+1,a]*(1-tx)+field[b+1,a+1]*tx)*ty
raw=sample(H,pts[:,0],pts[:,1]);water=np.minimum.accumulate(np.maximum(raw-8,0));water=np.minimum(water,water[0]*(1-fraction)**1.20);water=np.maximum(water,0);water[fraction>.94]=0
for _ in range(8):water=np.convolve(np.pad(water,4,mode='edge'),np.ones(9)/9,mode='valid');water=np.minimum.accumulate(water)
coast_hits=np.flatnonzero(raw<-.3)
if len(coast_hits):
 coast_index=int(coast_hits[0]);end_fraction=fraction[coast_index]
 water=np.maximum(0,water-water[max(0,coast_index-1)]*smooth(max(0,end_fraction-.15),end_fraction,fraction));water[coast_index:]=0
water[-1]=0
nearest=np.full(H.shape,1e20);along=np.zeros(H.shape);riverZ=np.zeros(H.shape)
for i in range(len(pts)-1):
 a=pts[i];delta=pts[i+1]-a;w=np.clip(((X-a[0])*delta[0]+(Y-a[1])*delta[1])/(delta@delta),0,1);dist=(X-a[0]-w*delta[0])**2+(Y-a[1]-w*delta[1])**2;mask=dist<nearest
 nearest[mask]=dist[mask];along[mask]=fraction[i]+w[mask]*(fraction[i+1]-fraction[i]);riverZ[mask]=water[i]+w[mask]*(water[i+1]-water[i])
dist=np.sqrt(nearest);width=10+14*along+55*smooth(.79,1,along);valleywidth=width+110+20*along
valley=riverZ+((dist/valleywidth)**1.4)*100
H-=np.maximum(H-valley,0)*(1-smooth(valleywidth*.75,valleywidth*2.5,dist))
channel=riverZ-3.4+3.4*(dist/width)**2
H-=np.maximum(H-channel,0)*(1-smooth(width,width*1.8,dist))
# Broader, naturally low floodplain around the estuary; a small spring lake upstream.
lakecenter=pts[0].copy();lakeR=np.sqrt(((X-lakecenter[0])/75)**2+((Y-lakecenter[1])/100)**2)
H-=np.maximum(H-(water[0]-4+4*lakeR**2),0)*(1-smooth(1,1.9,lakeR))
# Keep a modest runway from the earlier request; the rest is undeveloped land.
runway={'center_normalized':[-.47,-.075],'length_base_m':810.,'width_base_m':36.,'level_m':18.,'heading_deg':0}
rx=X+.47*1100;ry=Y+.075*1370;runmask=np.maximum(np.abs(rx)-runway['length_base_m']/2,0)+np.maximum(np.abs(ry)-runway['width_base_m']/2,0);blend=1-smooth(8,180,runmask);H=H*(1-blend)+runway['level_m']*blend
H=np.where(distance<-220,-65,H)
def fractions(z):
 positive=z>0;k=positive.sum(-1);out=(k==3).astype(float)
 for index in range(3):
  a=z[...,index];b=z[...,(index+1)%3];c=z[...,(index+2)%3]
  ratio=np.divide(a,a-b,out=np.zeros_like(a),where=np.abs(a-b)>1e-10)*np.divide(a,a-c,out=np.zeros_like(a),where=np.abs(a-c)>1e-10)
  out=np.where((k==1)&(a>0),ratio,out);out=np.where((k==2)&(a<=0),1-ratio,out)
 return out
z1=np.stack([H[:-1,:-1],H[:-1,1:],H[1:,1:]],-1);z2=np.stack([H[:-1,:-1],H[1:,1:],H[1:,:-1]],-1);dx=X[0,1]-X[0,0];dy=Y[1,0]-Y[0,0];area=float((fractions(z1).sum()+fractions(z2).sum())*dx*dy/2);factor=math.sqrt(ref['target_area_m2']/area);X*=factor;Y*=factor;pts*=factor;lakecenter*=factor
width*=factor;riverwidth=(10+14*fraction+55*smooth(.79,1,fraction))*factor
sea_hits=np.flatnonzero(raw<-.3);visible_count=min(len(pts),int(sea_hits[0])+2) if len(sea_hits) else len(pts)
pts=pts[:visible_count];water=water[:visible_count];riverwidth=riverwidth[:visible_count]
gradY,gradX=np.gradient(H,float(dy*factor),float(dx*factor));slope=np.sqrt(gradX**2+gradY**2)
beach=1-smooth(2,20,H);stone=smooth(.42,.98,slope)*smooth(12,50,H);upland=smooth(160,310,H)*.55;wet=(1-smooth(1,1.8,dist/np.maximum(width/factor,1)))*smooth(0,8,H)
ground=np.array([.24,.34,.14]);sand=np.array([.72,.65,.46]);rock=np.array([.40,.39,.35]);uplandcol=np.array([.39,.39,.28]);color=np.broadcast_to(ground,H.shape+(3,)).copy();color=color*(1-beach[...,None])+sand*beach[...,None];color=color*(1-upland[...,None])+uplandcol*upland[...,None];color=color*(1-stone[...,None])+rock*stone[...,None];color*=1-.12*wet[...,None];color*=1+(fine*.06+micro*.035)[...,None];color=np.clip(color,0,1)
seacol=np.array([.06,.22,.27]);color=np.where((H<0)[...,None],seacol,color)
top=np.clip(color*255,0,255).astype('uint8');im=Image.fromarray(top[::-1]);im.resize((4096,4096),Image.Resampling.BICUBIC).save(P/'texturas/albedo_terreno.png')
height=np.rint((H+65)/(H.max()+65)*65535).astype(np.uint16);Image.fromarray(height[::-1]).save(P/'dados/altura_16bits.png')
terrain=np.stack([X,Y,H],-1).astype(np.float32);np.savez_compressed(P/'dados/terreno.npz',terrain=terrain,color=color.astype(np.float32),river_points=pts.astype(np.float32),river_z=water.astype(np.float32),river_halfwidth=riverwidth.astype(np.float32),lakecenter=lakecenter.astype(np.float32),lakeheight=np.float32(water[0]),lake_radii=np.array([75,100])*factor)
land=H>0;stats={'seed':seed,'grid_vertices_per_axis':n,'land_area_m2':area*factor*factor,'land_area_km2':area*factor*factor/1e6,'reference_land_area_km2_estimate':ref['reference_land_area_m2_estimate']/1e6,'area_ratio':3,'area_definition':'Projected island footprint above mean sea level; river and spring lake inside this footprint. Cayo reference is an estimate from installed native terrain, not an official area.','dimension_interpretation':'3x area, not 3x width and 3x length.','land_bounds_m':[float(X[land].min()),float(Y[land].min()),float(X[land].max()),float(Y[land].max())],'highest_peak_m':float(H.max()),'sea_level_m':0,'horizontal_cell_m':[float(dx*factor),float(dy*factor)],'river_length_m':float(lengths[-1]*factor),'river_source_height_m':float(water[0]),'river_mouth_height_m':0,'river_halfwidth_m':[float(riverwidth[0]),float(riverwidth[-1])],'runway':dict(length_m=810*factor,width_m=36*factor,level_m=18,center_m=[-.47*1100*factor,-.075*1370*factor],heading_deg=0),'tiles_per_axis':8,'native_city_geometry_in_asset':False,'trees':0,'buildings':0,'blender_generated':False,'in_game_verified':False}
stats['river_length_m']=float(lengths[visible_count-1]*factor)
(P/'dados/medidas.json').write_text(json.dumps(stats,indent=2));print('ISLAND_TERRAIN_READY',stats,flush=True)
