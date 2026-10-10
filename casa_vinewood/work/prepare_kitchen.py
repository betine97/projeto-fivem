import sys,json,shutil,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=W/'source_assets/cozinha_completa';D.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work')]
from PIL import Image,ImageFilter
import numpy as np
from dds_mipmaps import save_dds_mips
refs={'overall':'3a2d5ff2-e460-4adb-8204-8c1527300a3c','microwave':'7c590d5a-2710-495e-bc20-594570840803','oven':'f4d0772d-61bf-4691-812f-e2b151f67bde','upper':'9a01321c-e844-4cf7-b651-e0eb87d29bda','placement':'ab95ff4c-aef5-4792-b55e-b2c38fee6405','counter':'2c5787d8-8d85-4e24-ac51-0d0e517bcc94'}
report={}
for name,key in refs.items():
 src=Path('C:/Users/erons/AppData/Local/Temp')/('codex-clipboard-'+key+'.png');shutil.copy2(src,D/(name+'.png'));im=Image.open(src)
 report[name]={'source':str(src),'size':im.size,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
def material(name,im,spec=25,relief=0):
 im=im.convert('RGBA');im.putalpha(255);save_dds_mips(im,D/(name+'_d.dds'))
 if relief:
  l=im.convert('L');h=np.asarray(l,np.float32)/255-np.asarray(l.filter(ImageFilter.GaussianBlur(4)),np.float32)/255;dy,dx=np.gradient(h);n=np.stack([-dx*relief,dy*relief,np.ones_like(dx)],2);n/=np.linalg.norm(n,axis=2,keepdims=True)
  ar=np.concatenate([np.uint8(np.clip((n+1)*127.5,0,255)),np.full((*h.shape,1),255,np.uint8)],2);normal=Image.fromarray(ar)
 else:normal=Image.new('RGBA',(64,64),(128,128,255,255))
 save_dds_mips(normal,D/(name+'_n.dds'),True);save_dds_mips(Image.new('RGBA',(64,64),(spec,spec,spec,255)),D/(name+'_s.dds'))
for n,rect in [('microwave',(39,299,1215,1006)),('oven',(35,100,1218,1150))]:
 im=Image.open(D/(n+'.png'));print(n,im.size,flush=True);material(n,im.crop(rect).resize((2048,2048),Image.Resampling.LANCZOS),55)
wood=Image.open(D/'upper.png');print('upper',wood.size,flush=True)
woodcrop=wood.crop((218,182,390,505)).resize((512,1024),Image.Resampling.LANCZOS)
woodcrop=Image.fromarray(np.uint8(np.asarray(woodcrop.convert('RGB'),np.float32)*.72))
material('wood',woodcrop,35,.6)
material('marble',Image.open(W/'source_assets/piso_marmore.png').resize((1024,1024),Image.Resampling.LANCZOS),50,.4)
rng=np.random.default_rng(32)
for n,rgb,spec in [('greige',(161,149,129),25),('black',(19,20,20),95),('steel',(146,148,146),180),('stone',(54,51,45),75),('darkwood',(76,43,22),35)]:
 ar=np.empty((512,512,4),np.uint8);noise=rng.normal(0,1.3,(512,512))
 if n=='steel':noise+=rng.normal(0,2.5,(512,1))
 for k,b in enumerate(rgb):ar[:,:,k]=np.clip(b+noise,0,255)
 ar[:,:,3]=255;material(n,Image.fromarray(ar),spec,.5 if n=='steel' else .12)
save_dds_mips(Image.new('RGBA',(64,64),(255,211,153,255)),D/'led_d.dds')
(W/'cozinha_completa.json').write_text(json.dumps({'revision':'cozinha-completa-20261008','model':'mansao_cozinha_parede','references':report,'local_to_house':{'front_x':13.534,'left_y':-6.6,'floor_z':-.8},'length_m':6.5,'depth_m':.64,'height_m':3.03,'counter_height_m':.91,'wall_gap_m':.012,'in_game_verified':False},indent=2),encoding='utf-8')
print('KITCHEN_INPUTS_PREPARED',flush=True)
