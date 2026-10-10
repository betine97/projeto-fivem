"""BC3 atlas mipmaps with independent slots and preserved cutout coverage."""
import io, struct
import numpy as np
from PIL import Image

def coverage_resize(image,size):
    """Avoid averaging sparse leaves below the native alpha-test threshold."""
    old=np.asarray(image.convert('RGBA'));wanted=np.mean(old[...,3]>=128)
    # Filter premultiplied colour so transparent black cannot darken leaf edges.
    alpha=old[...,3:4]/255.;premul=old.astype(float);premul[...,:3]*=alpha
    reduced=np.asarray(Image.fromarray(np.rint(premul).astype('u1'),'RGBA').resize(size,Image.Resampling.BOX)).copy()
    a=reduced[...,3].astype(float)
    reduced[...,:3]=np.rint(np.clip(reduced[...,:3].astype(float)/np.maximum(a[...,None]/255.,1/255.),0,255)).astype('u1')
    if wanted>0 and a.max()>0:
        rank=max(1,round(wanted*a.size));threshold=np.sort(a.ravel())[-rank]
        multiplier=128/max(threshold,1)
        reduced[...,3]=np.rint(np.clip(a*multiplier,0,255)).astype('u1')
    return Image.fromarray(reduced,'RGBA')

def atlas_dds(images,columns,slot=256):
    """Stop when slots reach one texel; smaller mips would mix plant species."""
    side=columns*slot;levels=[];raw=[];footprints=[]
    for k in range(slot.bit_length()):
        tile=max(1,slot>>k);atlas=Image.new('RGBA',(columns*tile,columns*tile))
        for i,im in enumerate(images):
            resized=im.convert('RGBA').resize((slot,slot),Image.Resampling.LANCZOS) if k==0 else coverage_resize(im,(tile,tile))
            atlas.paste(resized,((i%columns)*tile,(i//columns)*tile))
        b=io.BytesIO();atlas.save(b,format='DDS',pixel_format='DXT5');d=b.getvalue();raw.append(d[128:]);levels.append(atlas)
        footprints.append(float(np.mean(np.asarray(atlas)[...,3]>=128)))
    b=io.BytesIO();levels[0].save(b,format='DDS',pixel_format='DXT5');header=bytearray(b.getvalue()[:128])
    flags=struct.unpack_from('<I',header,8)[0]|0x20000;struct.pack_into('<I',header,8,flags);struct.pack_into('<I',header,28,len(levels));struct.pack_into('<I',header,108,0x401008)
    return bytes(header)+b''.join(raw),levels[0],footprints
