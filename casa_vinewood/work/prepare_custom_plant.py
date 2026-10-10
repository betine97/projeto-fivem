import sys,json,shutil,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=W/'source_assets/vaso_planta';D.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work')]
from PIL import Image,ImageFilter
import numpy as np
from dds_mipmaps import save_dds_mips
files={'reference':'29f03579-fb64-42f9-9ec8-161c133f2ba1','leaves':'c81e305f-676a-4e71-9c1f-0b19e6e1946a','bark':'298df031-7420-488a-bc7e-660b2213b2e5','pot':'cdf224ed-775e-4d79-aac6-a2bce68d2ea3'}
report={}
for family,key in files.items():
 src=Path('C:/Users/erons/AppData/Local/Temp')/('codex-clipboard-'+key+'.png');dest=D/(family+'.png');shutil.copy2(src,dest)
 report[family]=dict(source=str(src),path=str(dest),sha256=hashlib.sha256(src.read_bytes()).hexdigest())
 if family=='reference':continue
 im=Image.open(dest).convert('RGBA').resize((2048,2048),Image.Resampling.LANCZOS);im.putalpha(255)
 save_dds_mips(im,D/(family+'_diffuse.dds'))
 # Tangent-space micro-relief from the supplied material reference; the silhouette is geometry.
 lum=np.asarray(im.convert('L'),np.float32)/255;blur=np.asarray(im.convert('L').filter(ImageFilter.GaussianBlur(4)),np.float32)/255
 h=lum-blur;dy,dx=np.gradient(h);n=np.stack([-dx*2.5,dy*2.5,np.ones_like(dx)],2);n/=np.linalg.norm(n,axis=2,keepdims=True)
 rgba=np.concatenate([np.uint8(np.clip((n+1)*127.5,0,255)),np.full((*lum.shape,1),255,np.uint8)],2)
 save_dds_mips(Image.fromarray(rgba),D/(family+'_normal.dds'),normal=True)
 save_dds_mips(Image.new('RGBA',(128,128),(42 if family=='leaves' else 12,)*3+(255,)),D/(family+'_spec.dds'))
# Soil is a procedural material, not a flat pasted photograph.
rng=np.random.default_rng(31);noise=rng.random((512,512));c=np.zeros((512,512,4),np.uint8)
for k,base in enumerate((40,28,17)):c[:,:,k]=np.clip(base+(noise-.5)*28,0,255)
c[:,:,3]=255;save_dds_mips(Image.fromarray(c),D/'soil_diffuse.dds');save_dds_mips(Image.new('RGBA',(128,128),(128,128,255,255)),D/'soil_normal.dds',True);save_dds_mips(Image.new('RGBA',(128,128),(8,8,8,255)),D/'soil_spec.dds')
(W/'vaso_planta_autoral.json').write_text(json.dumps(dict(revision='vaso-autoral-2026-10-08',references=report,model='mansao_vaso_folhagem',in_game_verified=False),indent=2),encoding='utf-8')
print('PLANT_INPUTS_PREPARED',flush=True)
