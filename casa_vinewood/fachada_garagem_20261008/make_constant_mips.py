import sys,io,struct
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path.insert(0,str(R/'laboratorio_fivem/work/pydeps'))
from PIL import Image
for name in ['fach_creme','fach_cimento','fach_sinal','fach_led','fach_led_branco']:
    im=Image.open(P/'textures'/(name+'.dds')).convert('RGBA');levels=[]
    while True:
        buf=io.BytesIO();im.save(buf,format='DDS',pixel_format='DXT1');levels.append(buf.getvalue())
        if im.size==(1,1):break
        im=im.resize((max(1,im.width//2),max(1,im.height//2)))
    h=bytearray(levels[0][:128]);struct.pack_into('<I',h,8,struct.unpack_from('<I',h,8)[0]|0x20000);struct.pack_into('<I',h,28,len(levels));struct.pack_into('<I',h,108,0x1000|8|0x400000)
    (P/'textures'/(name+'.dds')).write_bytes(bytes(h)+b''.join(x[128:] for x in levels))
print('CONSTANT_MIPS_READY')
