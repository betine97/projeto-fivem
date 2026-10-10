from locate import *
import io,struct
from PIL import Image,ImageDraw,ImageFont,ImageFilter
for n in ['stream','textures','package/stream']:(P/n).mkdir(parents=True,exist_ok=True)
T=P/'textures';rng=np.random.default_rng(8842)
def dds(name,im):
 im.save(T/(name+'.png'));levels=[]
 while True:
  b=io.BytesIO();im.save(b,format='DDS',pixel_format='DXT5' if name=='hc_glass' else 'DXT1');levels.append(b.getvalue())
  if im.size==(1,1):break
  im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.LANCZOS)
 h=bytearray(levels[0][:128]);struct.pack_into('<I',h,8,struct.unpack_from('<I',h,8)[0]|0x20000);struct.pack_into('<I',h,28,len(levels));struct.pack_into('<I',h,108,0x1000|8|0x400000);(T/(name+'.dds')).write_bytes(bytes(h)+b''.join(q[128:] for q in levels))
colors={'stone':(223,217,198),'teal':(79,159,154),'gold':(173,144,83),'dark':(35,48,53),'white':(225,231,228),'rubber':(31,39,43),'fabric':(79,130,140),'red':(181,35,44),'wood':(117,87,53),'leaf':(45,99,57),'soil':(82,70,50),'led':(249,250,240),'screen':(15,55,58),'metal':(158,173,177),'glass':(146,191,192),'tile':(196,209,206),'road':(66,75,77)}
for name,col in colors.items():
 s=512 if name in ['stone','tile','wood','fabric'] else 64;n=rng.normal(0,1.35 if name=='stone' else .6,(s,s,1));v=np.clip(np.array(col)[None,None,:]+n,0,255).astype('uint8');im=Image.fromarray(v).convert('RGBA')
 if name=='glass':im.putalpha(66)
 if name=='tile':
  dr=ImageDraw.Draw(im)
  for x in range(0,s,128):dr.line((x,0,x,s),fill=(174,192,188,255),width=2);dr.line((0,x,s,x),fill=(174,192,188,255),width=2)
 if name=='wood':
  dr=ImageDraw.Draw(im)
  for x in range(0,s,6):dr.line((x,0,x+10,s),fill=(105+x%17,78,47,255),width=1)
 dds('hc_'+name,im)
dds('hc_normal',Image.new('RGBA',(64,64),(128,128,255,255)));dds('hc_spec',Image.new('RGBA',(32,32),(24,24,24,255)));dds('hc_specmetal',Image.new('RGBA',(32,32),(122,122,122,255)))
labels=['RECEPCAO','EMERGENCIA','TRIAGEM','CONSULTORIO 01','CONSULTORIO 02','RADIOLOGIA','TOMOGRAFIA','ULTRASSONOGRAFIA','LABORATORIO','FARMACIA','OBITOS','ENFERMARIA','CIRURGIA 01','CIRURGIA 02','ESTERILIZACAO','RECUPERACAO','UTI','REUNIAO MEDICA','CONVERSAS MEDICAS','DESCANSO','VESTIARIO','SANITARIOS','ADMINISTRACAO','PILLBOX','MEDICAL CENTER','ENTRADA','SAIDA','EXAMES','EQUIPE MEDICA']
im=Image.new('RGBA',(2048,2048),(221,232,228,255));dr=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',50);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',23)
for i,label in enumerate(labels):
 row,col=divmod(i,4);x=col*512;y=row*256;dr.rectangle((x+3,y+3,x+509,y+253),fill=(218,231,226,255));dr.rectangle((x+3,y+3,x+18,y+253),fill=(55,134,133,255));bbox=dr.textbbox((0,0),label,font=font);scale=min(1,460/max(1,bbox[2]));f=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',int(50*scale));dr.text((x+38,y+83),label,font=f,fill=(28,66,70,255));dr.text((x+38,y+155),'PILLBOX  /  CARCER WAY',font=small,fill=(85,122,120,255))
dds('hc_signs',im)
spec={'origin':[-475.,-322.,35.2],'models':['hc_exterior','hc_terreo','hc_superior','hc_mobiliario_0','hc_mobiliario_1','hc_jardins','hc_porta_clinica','hc_porta_entrada'],'collection':'HOSPITAL_CARCER_WAY','labels':labels,'colors':colors,'rooms':[],'doors':[],'lights':[],'in_game_verified':False}
(P/'spec.json').write_text(json.dumps(spec,indent=2));print('HOSPITAL_TEXTURES_READY',len(list(T.glob('*.dds'))))
