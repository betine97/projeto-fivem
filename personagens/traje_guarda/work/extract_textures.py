import json,struct,io,hashlib
from pathlib import Path
from PIL import Image
p=Path(r'C:\Users\erons\Downloads\Meshy_AI_guard_character_3d_1005050026_image-to-3d-texture.glb');b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);bin=b[28+n:];out=Path('personagens/traje_guarda/textures');out.mkdir(exist_ok=True)
# glTF texture indexes: normal0, baseColor1, metallicRoughness2.
for kind,idx in [('normal',0),('diff',1),('orm',2)]:
 im=j['images'][j['textures'][idx]['source']];view=j['bufferViews'][im['bufferView']];raw=bin[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];(out/('guard_'+kind+'.png')).write_bytes(raw)
 image=Image.open(io.BytesIO(raw)).convert('RGBA');w,h=image.size
 if kind=='orm':
  # Native ped specular amount from the PBR roughness channel, metallic in alpha.
  import numpy as np
  a=np.array(image);rough=a[:,:,1].astype(float)/255;spec=((1-rough)**2*255).astype('uint8');a[:,:,0]=spec;a[:,:,1]=spec;a[:,:,2]=spec;a[:,:,3]=0;image=Image.fromarray(a);kind='spec'
 hdr=[124,0x100f,h,w,w*4,0,0]+[0]*11+[32,0x41,0,32,255,65280,16711680,4278190080]+[0x1000,0,0,0,0]
 image.transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(out/('guard_'+kind+'.dds'),pixel_format='DXT5')
 print(kind,image.size,hashlib.sha256(raw).hexdigest())
