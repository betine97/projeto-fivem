import sys,shutil,io,struct,json
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent;R=W.parent;T=P/'textures'
sys.path.insert(0,str(R/'laboratorio_fivem/work/pydeps'))
from PIL import Image,ImageDraw,ImageFont
import numpy as np
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

shutil.copy2(Path('C:/Users/erons/.codex/generated_images/01a11c13-11ac-71c1-bf2a-b53244212f20/exec-4f93e368-51ee-4c51-a99d-dda6e6e72841.png'), T/'marmore_referencia.png')
dds(Image.open(T/'marmore_referencia.png').resize((1024,1024),Image.Resampling.LANCZOS),'adega_marmore')
dds(Image.open(W/'source_assets/cozinha_completa/wood_d.dds'),'adega_madeira')
shutil.copy2(W/'source_assets/cozinha_completa/wood_n.dds',T/'adega_madeira_n.dds')
for key,rgb in [('preto',(16,17,17)),('bronze',(132,96,40)),('creme',(220,209,187)),('ceramica',(196,184,158)),('vidro',(47,36,17)),('vinho',(49,24,10)),('vinho_escuro',(12,18,12)),('ambar',(104,44,5)),('rotulo',(221,204,177)),('led',(255,202,111)),('normal',(128,128,255)),('spec',(110,110,110)),('spec_fosco',(22,22,22)),('spec_metal',(180,180,180))]:
 dds(Image.new('RGB',(4,4),rgb),'adega_'+key,normal=key=='normal')
for key in ['vidro_transparente','cristal']:
 dds(Image.new('RGBA',(4,4),(222,227,217,70 if key=='cristal' else 32)),'adega_'+key)
for i in [1,2,3]:
 im=Image.new('RGB',(512,256),(221-i*9,213-i*10,187-i*9));draw=ImageDraw.Draw(im)
 ink=(63,42,22) if i<3 else (20,22,20)
 draw.rectangle((10,12,501,243),outline=ink,width=2)
 font=ImageFont.truetype('C:/Windows/Fonts/georgia.ttf',24)
 small=ImageFont.truetype('C:/Windows/Fonts/georgia.ttf',14)
 draw.text((256,48),['RESERVA','VINHO FINO','SELECAO'][i-1],font=font,fill=ink,anchor='mm')
 draw.line((200,85,312,85),fill=ink,width=2)
 draw.ellipse((236,95,276,125),outline=ink,width=2)
 for x in [241,250,259,268]:draw.line((x,112,x+8,94),fill=ink,width=1)
 draw.text((256,156),'VALE  |  SAFRA ESPECIAL',font=small,fill=ink,anchor='mm')
 draw.text((256,202),'750 ml',font=small,fill=ink,anchor='mm')
 dds(im,'adega_rotulo_'+str(i))
# Procedural leaf pigment and veins for the curved 3D leaf surfaces.
n=256;y,x=np.mgrid[:n,:n];vein=(abs(x-128)<2)|(abs((x-128)*.65-((y%33)-16))<1.5)
leaf=np.empty((n,n,3),np.uint8)
for i,c in enumerate([49,75,18]):leaf[:,:,i]=np.clip(c+11*np.sin(x/35)+7*np.sin(y/21)+vein*(8 if i!=1 else 18),0,255)
dds(Image.fromarray(leaf),'adega_folha')
dds(Image.open(W/'bar_referencia_20261008/textures/arte_restaurada.png').resize((256,512),Image.Resampling.LANCZOS),'adega_arte_mini')
dds(Image.new('RGB',(4,4),(220,207,176)),'adega_arte')
print('ADEGA_MATERIALS_READY',sum(p.stat().st_size for p in T.glob('*.dds')),flush=True)
