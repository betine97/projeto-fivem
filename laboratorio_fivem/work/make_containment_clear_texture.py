"""Turn the Meshy color atlas into clear vinyl with opaque dark brackets."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0,r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\media_deps')
from PIL import Image

root=Path(__file__).resolve().parents[2]
folder=root/'laboratorio_fivem/containment_source'
rgb=np.asarray(Image.open(folder/'Image_0.png').convert('RGB').resize((2048,2048),Image.Resampling.LANCZOS),dtype=np.uint8)
luma=rgb.astype(np.float32).mean(axis=2)
# Meshy baked dozens of overlapping opaque vinyl surfaces into its dense mesh.
# Retain its dark rails/clips, then use a single clean vinyl layer built below.
alpha=np.interp(luma,[0,20,45,75,105,255],[255,250,180,25,0,0]).astype(np.uint8)
rgba=np.dstack((rgb,alpha))
Image.fromarray(rgba,'RGBA').save(folder/'containment_clear_rgba.png')

y,x=np.mgrid[:512,:256].astype(np.float32)
wave=3.0*np.sin(y*.035)+2.0*np.sin(y*.011)
fold=(35*np.exp(-((x-47-wave)/3.6)**2)+
      26*np.exp(-((x-136+wave)/5.5)**2)+
      18*np.exp(-((x-205-wave*.5)/2.8)**2))
edge=47*np.exp(-(x/6)**2)+47*np.exp(-((x-255)/6)**2)
faint=3*np.sin(x*.23+y*.016)
strip_alpha=np.clip(9+fold+edge+faint,4,82).astype(np.uint8)
shimmer=np.clip(205+fold*.7+edge*.6,0,250).astype(np.uint8)
vinyl=np.stack((shimmer, np.clip(shimmer.astype(np.int16)+4,0,255).astype(np.uint8),
                np.clip(shimmer.astype(np.int16)+8,0,255).astype(np.uint8),strip_alpha),axis=-1)
Image.fromarray(vinyl,'RGBA').save(folder/'vinyl_strip_clear_rgba.png')
print('CLEAR_TEXTURE_OK','alpha',int(alpha.min()),int(alpha.max()),
      'clear_fraction',round(float((alpha<32).mean()),3),
      'vinyl_alpha',int(strip_alpha.min()),int(strip_alpha.max()),flush=True)
