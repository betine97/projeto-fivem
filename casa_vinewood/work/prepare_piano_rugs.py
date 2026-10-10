import sys,json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=W/'source_assets/piano_tapetes';D.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work')]
import numpy as np
from PIL import Image,ImageFilter,ImageDraw
from dds_mipmaps import save_dds_mips
refs={'piano':'a08d451c-1ab4-4f49-aea5-f522ebdd2acb','bear':'c2da52f1-641f-4ca3-9b7d-008102e45433','carpet':'ad678d23-5899-4863-bb3e-a77d9b112cf1'};info={}
for n,key in refs.items():
 src=Path('C:/Users/erons/AppData/Local/Temp')/('codex-clipboard-'+key+'.png');shutil.copy2(src,D/(n+'_reference.png'));im=Image.open(src);info[n]={'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'size':im.size};print(n,im.size,flush=True)
def material(name,im,spec=15,relief=0):
 im=im.convert('RGBA');im.putalpha(255);save_dds_mips(im,D/(name+'_d.dds'))
 if relief:
  gray=im.convert('L');h=np.array(gray,np.float32)/255-np.array(gray.filter(ImageFilter.GaussianBlur(2)),np.float32)/255;dy,dx=np.gradient(h);n=np.stack([-dx*relief,dy*relief,np.ones_like(dx)],2);n/=np.linalg.norm(n,axis=2,keepdims=True);ar=np.concatenate([np.uint8(np.clip((n+1)*127.5,0,255)),np.full((*h.shape,1),255,np.uint8)],2);normal=Image.fromarray(ar)
 else:normal=Image.new('RGBA',(64,64),(128,128,255,255))
 save_dds_mips(normal,D/(name+'_n.dds'),True);save_dds_mips(Image.new('RGBA',(64,64),(spec,)*3+(255,)),D/(name+'_s.dds'))
colors={'black':((9,10,12),235),'gold':((169,119,45),205),'ivory':((238,233,217),70),'felt':((105,9,10),6),'leather':((17,16,15),25),'nose':((9,8,7),110),'fur_edge':((77,49,32),15)}
for n,(rgb,spec) in colors.items():material(n,Image.new('RGB',(128,128),rgb),spec)
rng=np.random.default_rng(813);yy,xx=np.mgrid[:512,:1024];noise=rng.normal(0,1.1,(512,1024));grain=np.sin(yy*.55+np.sin(xx*.009)*2)+np.sin(yy*1.7+xx*.011)*.3
wood=np.zeros((512,1024,4),np.uint8)
for k,b in enumerate((105,65,28)):wood[:,:,k]=np.clip(b+grain*7+noise,0,255)
wood[:,:,3]=255;material('wood',Image.fromarray(wood),50,.25)
bear=Image.open(D/'bear_reference.png').convert('RGB');ar=np.array(bear);mask=(ar[:,:,0].astype(int)+ar[:,:,1]+ar[:,:,2]>55)&(ar[:,:,1]>12)&(ar[:,:,0]<ar[:,:,1].astype(int)*5)
mask=Image.fromarray(np.uint8(mask)*255).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3));ImageDraw.floodfill(mask,(0,0),128,thresh=0)
mask=Image.fromarray(np.uint8(np.array(mask)!=128)*255);bounds=mask.getbbox();mask=mask.crop(bounds);mask.save(D/'bear_mask.png');bear=bear.crop(bounds)
# UV bleed padding: replace the source cutout's red/yellow fringe with neighbouring fur.
rgb=np.array(bear).astype(np.float32);valid=(np.array(mask)>127)&(rgb[:,:,0]<rgb[:,:,1]*1.8+8)&(rgb[:,:,1]<rgb[:,:,0]*1.25+6)&(rgb[:,:,2]>rgb[:,:,1]*.38)
for _ in range(18):
 total=np.zeros_like(rgb);weight=np.zeros(valid.shape,np.float32)
 for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
  nv=np.roll(valid,(dy,dx),(0,1));nr=np.roll(rgb,(dy,dx),(0,1));total+=nr*nv[:,:,None];weight+=nv
 extend=(~valid)&(weight>0);rgb[extend]=total[extend]/weight[extend,None];valid|=extend
rgb[~valid]=(77,49,32);bear=Image.fromarray(np.uint8(np.clip(rgb,0,255)));bear.save(D/'bear_albedo.png');material('bear',bear.resize((2048,2048),Image.Resampling.LANCZOS),15,2.4)
carpet=Image.open(D/'carpet_reference.png');cw,ch=carpet.size;crop=(round(cw*.093),round(ch*.012),round(cw*.907),round(ch*.985));carpet=carpet.crop(crop).convert('RGB');carpet.save(D/'carpet_albedo.png');material('carpet',carpet.resize((2048,2048),Image.Resampling.LANCZOS),12,2.1)
spec={'revision':'piano-tapetes-20261008','references':info,'bear_image_bounds':bounds,'bear_ratio':bear.height/bear.width,'carpet_ratio':carpet.height/carpet.width,'in_game_verified':False,'models':{'piano':{'name':'mansao_piano_cauda','position':[-5.45,-4.7,-.8],'heading':-np.pi/2,'keys':88},'bear':{'name':'mansao_tapete_urso','position':[-.65,-8.2,-.8],'heading':0,'width_m':2.50},'carpet':{'name':'mansao_tapete_classico','position':[7.4,.5,-.8],'heading':np.pi/2,'width_m':1.85}}}
(W/'piano_tapetes.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');print('PIANO_RUG_INPUTS_PREPARED',bounds,flush=True)
