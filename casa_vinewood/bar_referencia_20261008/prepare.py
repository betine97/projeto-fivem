import sys,json,shutil,hashlib,io,struct
from pathlib import Path
P=Path(__file__).resolve().parent; W=P.parent; R=W.parent
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps')]
from PIL import Image,ImageDraw,ImageFilter
import numpy as np
T=P/'textures'; T.mkdir(exist_ok=True)
def dds(im,name,normal=False):
 im=im.convert('RGBA'); levels=[]
 while True:
  b=io.BytesIO();im.save(b,format='DDS',pixel_format='DXT5' if normal or im.getextrema()[3][0]<255 else 'DXT1');levels.append(b.getvalue())
  if im.size==(1,1):break
  im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.BOX)
  if normal:
   a=np.array(im,np.float32);n=a[:,:,:3]/127.5-1;n/=np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-8);a[:,:,:3]=np.clip((n+1)*127.5,0,255);im=Image.fromarray(a.astype(np.uint8))
 h=bytearray(levels[0][:128]);struct.pack_into('<I',h,8,struct.unpack_from('<I',h,8)[0]|0x20000);struct.pack_into('<I',h,28,len(levels));struct.pack_into('<I',h,108,0x1000|8|0x400000)
 (T/(name+'.dds')).write_bytes(bytes(h)+b''.join(x[128:] for x in levels))
refs={}
for k,n in [('game','759ecd2b-7d08-4d89-946b-9c5382b8444d'),('reference','fcf76649-25af-4d34-a57d-b0340952bf1a')]:
 f=Path('C:/Users/erons/AppData/Local/Temp')/('codex-clipboard-'+n+'.png');shutil.copy2(f,P/(k+'.png'));refs[k]={'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
im=Image.open(P/'reference.png').convert('RGB')
# Rectify only the supplied artwork, excluding its frame and red annotation.
canvas=im.transform((768,1024),Image.Transform.QUAD,(646,233,647,412,806,416,806,227),Image.Resampling.BICUBIC)
canvas.save(T/'arte_canvas.png');dds(canvas.resize((1024,2048),Image.Resampling.LANCZOS),'bar_arte')
if (T/'arte_restaurada.png').exists():dds(Image.open(T/'arte_restaurada.png').resize((1024,2048),Image.Resampling.LANCZOS),'bar_arte')
dds(Image.open(W/'source_assets/cozinha_completa/wood_d.dds'),'bar_madeira')
shutil.copy2(W/'source_assets/cozinha_completa/wood_n.dds',T/'bar_madeira_n.dds')
for name,rgb in [('bar_preto',(13,13,12)),('bar_bronze',(91,66,38)),('bar_creme',(211,197,166)),('bar_ceramica',(178,162,136)),('bar_vidro',(48,45,32)),('bar_vinho',(46,31,18)),('bar_rotulo',(202,181,142)),('bar_folha',(42,59,20)),('bar_led',(255,218,162)),('bar_normal',(128,128,255)),('bar_spec',(80,80,80)),('bar_spec_fosco',(18,18,18)),('bar_spec_metal',(150,150,150))]:dds(Image.new('RGB',(4,4),rgb),name,normal=name=='bar_normal')
# Procedural stone veins are a material texture, not a photo pasted on shelving.
N=1024;rng=np.random.default_rng(876);y,x=np.mgrid[:N,:N];base=rng.normal(0,.8,(N,N));stone=np.zeros((N,N,3),np.float32)
for i,c in enumerate((30,27,22)):stone[:,:,i]=c+base
veins=Image.new('L',(N,N));draw=ImageDraw.Draw(veins)
for k in range(16):
 sx=float(rng.uniform(-N*.4,N*1.2));sy=float(rng.uniform(-N*.2,N));theta=rng.uniform(-.7,.9);pts=[]
 for j in range(50):
  xx=sx+j*22*np.cos(theta)+18*np.sin(j*.5+k);yy=sy+j*22*np.sin(theta)+26*np.sin(j*.23+k*2);pts.append((xx,yy))
 draw.line(pts,fill=int(rng.integers(90,170)),width=int(rng.integers(1,3)))
 for j in range(5,46,9):
  a,b=pts[j];draw.line([(a,b),(a+30,b-18),(a+57,b-42),(a+80,b-110)],fill=65,width=1)
a=np.array(veins.filter(ImageFilter.GaussianBlur(.55)),np.float32)/255
for i,c in enumerate((140,111,61)):stone[:,:,i]+=a*c
marble=Image.fromarray(np.uint8(np.clip(stone,0,255)));marble.save(T/'marmore_preto.png');dds(marble,'bar_marmore')
dds(Image.new('RGBA',(4,4),(193,185,155,68)),'bar_vidro_transparente')
spec={'revision':'bar-parede-referencia-20261008','model':'mansao_bar_referencia','origin':json.loads((W/'medidas_estudo.json').read_text())['native_origin'],
 'references':refs,'wall_front_y':-14.241,'model_wall_y':-14.225,'design_start_x':13.35,'floor_z':-.8,'cabinet_width_m':2.52,'cabinet_height_m':3.12,'cabinet_depth_m':.535,
 'art_canvas_width_m':1.62,'art_canvas_height_m':1.95,'in_game_verified':False}
(P/'spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('BAR_MATERIALS_READY',sum(f.stat().st_size for f in T.glob('*.dds')),flush=True)
