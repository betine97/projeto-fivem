"""Read rendered pixels to check actual frame compositing, not CSS declarations."""
from pathlib import Path
import sys,json
O=Path(__file__).resolve().parents[1];R=O.parent.parent
sys.path.insert(0,str(R/'laboratorio_fivem/work/pydeps'))
from PIL import Image
results={}
for name,color in [('antes',(18,18,18)),('depois',(238,0,238)),('fechado',(238,0,238))]:
    image=Image.open(O/'dados'/('nui_adm_'+name+'.png')).convert('RGB')
    samples=[image.getpixel(p) for p in [(100,100),(800,450),(1500,800)]]
    assert all(c==color for c in samples),(name,samples)
    results[name]=samples
image=Image.open(O/'dados/nui_adm_aberto.png').convert('RGB')
assert image.getpixel((800,450)) not in [(238,0,238),(18,18,18)]
results['aberto']=image.getpixel((800,450))
(O/'dados/teste_nui_pixels.json').write_text(json.dumps({'passed':True,'pixels':results,'in_game_verified':False},indent=2))
print('NUI_COMPOSITING_PIXELS_PASSED; before opaque, after transparent, ADM opens/closes')
