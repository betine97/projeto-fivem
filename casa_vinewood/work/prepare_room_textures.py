"""Preserve supplied albedo images and prepare power-of-two GTA textures."""
import sys,json,struct,io,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';S=W/'source_assets';D=W/'work/materiais';D.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps')]
from PIL import Image,ImageFilter
import numpy as np
settings={'marble':('piso_marmore.png','piso_marmore',1.2,.32,.08),'wall':('parede_reboco.png','parede_reboco',1.8,.87,.6),'brick':('parede_tijolo_tv.png','parede_tijolo_tv',1.6,.89,2.0),'metal':('corrimao_preto.png','corrimao_preto',.6,.55,.35)}
report={}
for key,(filename,name,tile,roughness,strength) in settings.items():
 im=Image.open(S/filename).convert('RGBA').resize((2048,2048),Image.Resampling.LANCZOS)
 color=D/(name+'.dds');im.save(color,pixel_format='DXT5')
 h=np.array(im.convert('L').filter(ImageFilter.GaussianBlur(1.1)),dtype=np.float32)/255
 # Periodic central differences prevent a derivative discontinuity at repeats.
 dx=(np.roll(h,-1,1)-np.roll(h,1,1))*strength;dy=(np.roll(h,-1,0)-np.roll(h,1,0))*strength
 # Source image rows point down. GTA's DirectX normal convention has the
 # opposite green channel to glTF/OpenGL tangent normals.
 n=np.stack((-dx,-dy,np.ones_like(h)),axis=2);n/=np.linalg.norm(n,axis=2,keepdims=True)
 normal=D/(name+'_n.dds');Image.fromarray(np.round((n*.5+.5)*255).astype(np.uint8)).convert('RGBA').save(normal,pixel_format='DXT5')
 report[key]=dict(source=str(S/filename),source_sha256=hashlib.sha256((S/filename).read_bytes()).hexdigest(),diffuse=str(color),normal=str(normal),size=[2048,2048],tile_m=tile,roughness=roughness,generated_normal_is_approximation=True,normal_convention='GTA/DirectX')
 print('TEXTURE_READY',key,flush=True)
# Extract embedded source maps without re-baking or changing the original UVs.
b=(S/'sofa_original.glb').read_bytes();ln,typ=struct.unpack_from('<II',b,12);j=json.loads(b[20:20+ln]);off=20+ln;binlen,_=struct.unpack_from('<II',b,off);blob=b[off+8:off+8+binlen]
maps=[]
for i,image in enumerate(j['images']):
 view=j['bufferViews'][image['bufferView']];start=view.get('byteOffset',0);raw=blob[start:start+view['byteLength']]
 original=D/('sofa_original_'+str(i)+'.jpg');original.write_bytes(raw)
 im=Image.open(io.BytesIO(raw)).convert('RGBA');original_size=list(im.size)
 if max(im.size)>2048:im.thumbnail((2048,2048),Image.Resampling.LANCZOS)
 if i==2:
  pixels=np.array(im);pixels[:,:,1]=255-pixels[:,:,1];im=Image.fromarray(pixels)
 target=D/(['sofa_albedo','sofa_metal_roughness','sofa_normal'][i]+'.dds');im.save(target,pixel_format='DXT5')
 maps.append(dict(source=str(original),dds=str(target),source_size=original_size,export_size=list(im.size)))
 if i==1:
  roughness=np.array(im,dtype=np.float32)[:,:,1]/255
  spec=np.clip(.04+(1-roughness)*.32,.04,.36)
  rgb=np.repeat(np.round(spec[:,:,None]*255).astype(np.uint8),3,axis=2)
  Image.fromarray(rgb).convert('RGBA').save(D/'sofa_spec.dds',pixel_format='DXT5')
report['sofa']=dict(glb_source=str(S/'sofa_original.glb'),glb_sha256=hashlib.sha256(b).hexdigest(),maps=maps,uv_preserved=True,normal_convention='glTF/OpenGL converted to GTA/DirectX')
(W/'materiais_sala.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('ROOM_TEXTURES_READY',flush=True)
