from pathlib import Path
import sys
O=Path(__file__).resolve().parents[1];sys.path.insert(0,str(O.parent.parent/'laboratorio_fivem/work/pydeps'))
import numpy as np
from PIL import Image
# A newly authored tiling turf texture; no supplied raster is edited.
r=np.random.default_rng(20261009);a=r.normal(0,1,(1024,1024));b=r.normal(0,1,(128,128));coarse=np.repeat(np.repeat(b,8,0),8,1);v=.85+.08*a+.10*coarse
rgb=np.clip(np.array([70,92,40])[None,None,:]*v[:,:,None]+r.uniform(-5,5,(1024,1024,3)),0,255).astype(np.uint8)
Image.fromarray(rgb).save(O/'fontes/pe_solo_grama.png')
# Newly authored rock grain, with no large photographic motifs repeating on cliffs.
n=512;fine=r.normal(0,1,(n,n));grain=r.normal(0,1,(64,64));grain=np.repeat(np.repeat(grain,8,0),8,1)
v=1+.045*fine+.065*grain
rgb=np.clip(np.array([111,108,91])[None,None,:]*v[:,:,None]+r.normal(0,2,(n,n,3)),0,255).astype(np.uint8)
Image.fromarray(rgb).save(O/'fontes/pe_solo_rocha.png')
