from pathlib import Path
import sys,io,struct,json
P=Path(__file__).resolve().parents[1];R=P.parent
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from PIL import Image
from szio.rpf import open_rpf
for f in ['fivem/stream','fivem/data','nativo/texturas','nativo/ydr','backup_ativacao']:(P/f).mkdir(parents=True,exist_ok=True)
def dds(name,im):
 levels=[]
 while True:
  b=io.BytesIO();im.save(b,format='DDS',pixel_format='DXT1');levels.append(b.getvalue())
  if im.size==(1,1):break
  im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.LANCZOS)
 header=bytearray(levels[0][:128]);struct.pack_into('<I',header,8,struct.unpack_from('<I',header,8)[0]|0x20000);struct.pack_into('<I',header,28,len(levels));struct.pack_into('<I',header,108,0x1000|8|0x400000)
 (P/'nativo/texturas'/f'{name}.dds').write_bytes(header+b''.join(v[128:] for v in levels))
meta=json.loads((P/'dados/medidas.json').read_text());im=Image.open(P/'texturas/albedo_terreno.png').convert('RGBA')
for tile in meta['tiles']:
 ix,iy=int(tile['name'][-2:]),int(tile['name'][-5:-3]);crop=im.crop((ix*512,(7-iy)*512,(ix+1)*512,(8-iy)*512));dds(tile['name'],crop)
dds('ti_asfalto',Image.new('RGBA',(32,32),(39,43,44,255)));dds('ti_faixas',Image.new('RGBA',(8,8),(205,208,200,255)))
# Read the stock level schema for provenance. Its original world archives will
# be omitted from the custom level, retaining only non-map gameplay data.
game=Path(r'C:/Program Files (x86)/Steam/steamapps/common/Grand Theft Auto V')
for archive,path in [('common.rpf','data/levels/gta5/gta5.meta'),('update/update.rpf','common/data/levels/gta5/gta5.meta'),('common.rpf','data/levels/gta5/water.xml')]:
 try:
  b=open_rpf(game/archive).read_bytes(path);(P/'referencia_tecnica'/('base_'+Path(path).name)).write_bytes(b);print('LEVEL_REFERENCE',archive,path,len(b))
 except Exception as e:print('LEVEL_REFERENCE_NOTE',archive,path,str(e)[:160])
print('PREPARED_FIVEM_TEXTURES',len(meta['tiles']),flush=True)
