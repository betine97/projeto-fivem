"""Encode a complete BC3 mip chain; normalize tangent normals at each level."""
import io, struct
import numpy as np
from PIL import Image

def save_dds_mips(image, path, normal=False):
    levels=[]; image=image.convert('RGBA')
    while True:
        out=io.BytesIO(); image.save(out,format='DDS',pixel_format='DXT5')
        levels.append(out.getvalue())
        if image.size==(1,1): break
        size=(max(1,image.width//2),max(1,image.height//2))
        image=image.resize(size,Image.Resampling.BOX)
        if normal:
            p=np.array(image,dtype=np.float32); n=p[:,:,:3]/127.5-1
            n/=np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-8)
            p[:,:,:3]=np.clip(np.round((n+1)*127.5),0,255)
            image=Image.fromarray(p.astype(np.uint8),'RGBA')
    header=bytearray(levels[0][:128])
    flags=struct.unpack_from('<I',header,8)[0] | 0x20000
    struct.pack_into('<I',header,8,flags)
    struct.pack_into('<I',header,28,len(levels))
    struct.pack_into('<I',header,108,0x1000|0x8|0x400000)
    path.write_bytes(bytes(header)+b''.join(x[128:] for x in levels))
    return len(levels)
