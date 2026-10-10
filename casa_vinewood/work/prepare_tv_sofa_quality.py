"""Keep source 4K atlases and supply filtered mipmaps for all new finishes."""
import sys, json, struct, io, hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2]; W=R/'casa_vinewood'; D=W/'work/materiais'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps')]
import numpy as np
from PIL import Image
from dds_mipmaps import save_dds_mips
config=json.loads((W/'materiais_sala.json').read_text())
for family in ('marble','wall','brick','metal'):
    row=config[family]
    for key in ('diffuse','normal'):
        p=Path(row[key]); im=Image.open(p).convert('RGBA')
        row[key+'_mip_count']=save_dds_mips(im,p,normal=key=='normal')
for family,filename in [('sofa','sofa_original.glb'),('tv','tv_console_original.glb')]:
    b=(W/'source_assets'/filename).read_bytes(); n=struct.unpack_from('<I',b,12)[0]
    j=json.loads(b[20:20+n]); blob=b[28+n:]
    mat=j['materials'][0];pbr=mat['pbrMetallicRoughness']
    indices=[pbr['baseColorTexture']['index'],pbr['metallicRoughnessTexture']['index'],mat['normalTexture']['index']]
    maps=[];images=[]
    for name,idx in zip(('albedo','metal_roughness','normal'),indices):
        source=j['images'][j['textures'][idx]['source']];view=j['bufferViews'][source['bufferView']]
        raw=blob[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
        src=D/(family+'_original_'+name+'.jpg');src.write_bytes(raw)
        im=Image.open(io.BytesIO(raw)).convert('RGBA');images.append(im.copy())
        if name=='normal':
            a=np.array(im);a[:,:,1]=255-a[:,:,1];im=Image.fromarray(a)
        dst=D/(family+'_'+name+'.dds');count=save_dds_mips(im,dst,normal=name=='normal')
        maps.append(dict(source=str(src),dds=str(dst),source_size=list(im.size),export_size=list(im.size),mip_count=count))
    # Convert roughness to restrained grayscale dielectric specularity.
    # Falloff is set explicitly in the material rather than relying on defaults.
    rough=np.array(images[1],dtype=np.float32)[:,:,1]/255
    spec=np.zeros((*rough.shape,4),dtype=np.uint8)
    spec[:,:,0]=np.round((.045+(1-rough)*.075)*255)
    spec[:,:,1]=spec[:,:,0];spec[:,:,2]=spec[:,:,0];spec[:,:,3]=255
    count=save_dds_mips(Image.fromarray(spec),D/(family+'_spec.dds'))
    config[family]=dict(glb_source=str(W/'source_assets'/filename),glb_sha256=hashlib.sha256(b).hexdigest(),maps=maps,uv_preserved=True,normal_convention='glTF/OpenGL converted to GTA/DirectX',spec_mip_count=count,specular_intensity=.22,specular_falloff=35,specular_fresnel=.12,wetness_multiplier=0)
    print('QUALITY_ATLASES',family,[(q['export_size'],q['mip_count']) for q in maps],flush=True)
(W/'materiais_sala.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
