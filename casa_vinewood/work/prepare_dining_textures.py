import json,sys,struct,io,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'casa_vinewood';D=W/'work/materiais'
sys.path.insert(0,str(R/'laboratorio_fivem/work/pydeps'))
import numpy as np
from PIL import Image
from dds_mipmaps import save_dds_mips
cfg=json.loads((W/'materiais_sala.json').read_text());inputs=json.loads((W/'componentes_jantar_cozinha.json').read_text())
for family,row in inputs['assets'].items():
 raw=Path(row['local_source']).read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);blob=raw[28+n:];mat=g['materials'][0];pbr=mat['pbrMetallicRoughness'];maps=[];ims=[]
 for key,idx in [('albedo',pbr['baseColorTexture']['index']),('metal_roughness',pbr['metallicRoughnessTexture']['index']),('normal',mat['normalTexture']['index'])]:
  v=g['bufferViews'][g['images'][g['textures'][idx]['source']]['bufferView']];data=blob[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
  original=D/(family+'_original_'+key+'.jpg');original.write_bytes(data);im=Image.open(io.BytesIO(data)).convert('RGBA');ims.append(im.copy())
  if key=='normal':a=np.array(im);a[:,:,1]=255-a[:,:,1];im=Image.fromarray(a)
  # Specular response has no need for a 4K atlas; preserve albedo/normal source resolution.
  if key=='metal_roughness':continue
  p=D/(family+'_'+key+'.dds');mips=save_dds_mips(im,p,normal=key=='normal');maps.append(dict(name=key,path=str(p),size=list(im.size),mips=mips))
 rough=np.array(ims[1],dtype=np.float32)[:,:,1]/255;spec=np.zeros((*rough.shape,4),dtype=np.uint8);spec[:,:,:3]=np.round((.045+(1-rough)*.075)*255)[:,:,None];spec[:,:,3]=255
 im=Image.fromarray(spec);im.thumbnail((2048,2048),Image.Resampling.BOX);save_dds_mips(im,D/(family+'_spec.dds'))
 cfg[family]=dict(glb_source=row['local_source'],glb_sha256=row['sha256'],maps=maps,uv_preserved=True,specular_intensity=.22,wetness_multiplier=0)
 print('NEW_ATLASES',family,maps,flush=True)
(W/'materiais_sala.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
