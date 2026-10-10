import json,sys,struct,io,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=W/'work/materiais'
sys.path.insert(0,str(R/'laboratorio_fivem/work/pydeps'))
import numpy as np
from PIL import Image
from dds_mipmaps import save_dds_mips
p=Path(r'C:/Users/erons/Downloads/Meshy_AI_textured_woven_rug_3d_1008033831_image-to-3d-texture.glb')
local=W/'source_assets/tapete_meshy.glb';shutil.copy2(p,local)
raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);blob=raw[28+n:]
mat=g['materials'][0];pbr=mat['pbrMetallicRoughness'];maps={}
for key,index in [('albedo',pbr['baseColorTexture']['index']),('roughness',pbr['metallicRoughnessTexture']['index']),('normal',mat['normalTexture']['index'])]:
 v=g['bufferViews'][g['images'][g['textures'][index]['source']]['bufferView']];data=blob[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
 (D/('rug_original_'+key+'.jpg')).write_bytes(data);im=Image.open(io.BytesIO(data)).convert('RGBA');im.thumbnail((4096,4096),Image.Resampling.LANCZOS)
 if key=='normal':a=np.array(im);a[:,:,1]=255-a[:,:,1];im=Image.fromarray(a)
 if key=='roughness':
  a=np.zeros((*np.array(im).shape[:2],4),dtype=np.uint8);a[:,:,:3]=15;a[:,:,3]=255;im=Image.fromarray(a);im.thumbnail((1024,1024),Image.Resampling.BOX);key='spec'
 path=D/('rug_'+key+'.dds');mips=save_dds_mips(im,path,normal=key=='normal');maps[key]=dict(path=str(path),size=list(im.size),mips=mips)
spec=dict(source=str(p),local_source=str(local),sha256=hashlib.sha256(raw).hexdigest(),maps=maps,in_game_verified=False)
(W/'tapete_sala.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('RUG_INPUT_PREPARED',maps,flush=True)
