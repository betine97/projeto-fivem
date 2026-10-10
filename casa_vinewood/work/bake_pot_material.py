"""Tileable ceramic microstructure matching the graphite reference, without baked studio highlights."""
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=W/'source_assets/vaso_planta';sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),str(W/'work')]
import numpy as np
from PIL import Image,ImageFilter
from dds_mipmaps import save_dds_mips
size=1024;rng=np.random.default_rng(75)
fine=rng.random((size,size));coarse=np.asarray(Image.fromarray(np.uint8(rng.random((32,32))*255)).resize((size,size),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(6)),float)/255
grain=(fine-.5)*15+(coarse-.5)*22
rgba=np.full((size,size,4),255,np.uint8)
for i,base in enumerate((61,59,54)):rgba[:,:,i]=np.clip(base+grain,0,255)
save_dds_mips(Image.fromarray(rgba),D/'pot_diffuse.dds')
dy,dx=np.gradient(fine*.08+coarse*.12);n=np.stack([-dx,dy,np.ones_like(dx)],2);n/=np.linalg.norm(n,axis=2,keepdims=True);rgba[:,:,:3]=np.uint8((n+1)*127.5)
save_dds_mips(Image.fromarray(rgba),D/'pot_normal.dds',True)
print('GRAPHITE_CERAMIC_MATERIAL_BAKED',flush=True)
