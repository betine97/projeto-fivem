"""Extract supplied canvas pixels for UV mapping; no generated replacement art."""
import sys,json,io,struct
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps')]
import numpy as np
from PIL import Image,ImageFilter
T=P/'textures';T.mkdir(exist_ok=True)
def normalize(image):
    arr=np.array(image.convert('RGBA'),dtype=np.float32);n=arr[:,:,:3]/127.5-1
    n/=np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-8)
    arr[:,:,:3]=np.clip(np.round((n+1)*127.5),0,255)
    return Image.fromarray(arr.astype(np.uint8))
def dds(image,path,normal=False,opaque=True):
    levels=[];image=image.convert('RGBA')
    while True:
        b=io.BytesIO();image.save(b,format='DDS',pixel_format='DXT1' if opaque and not normal else 'DXT5');levels.append(b.getvalue())
        if image.size==(1,1):break
        image=image.resize((max(1,image.width//2),max(1,image.height//2)),Image.Resampling.BOX)
        if normal:image=normalize(image)
    head=bytearray(levels[0][:128]);struct.pack_into('<I',head,8,struct.unpack_from('<I',head,8)[0]|0x20000)
    struct.pack_into('<I',head,28,len(levels));struct.pack_into('<I',head,108,0x1000|8|0x400000)
    path.write_bytes(bytes(head)+b''.join(x[128:] for x in levels))
rows=[]
for i,crop,height,label,position,heading in [
    (2,(136,94,949,1361),1.45,'Quadro geometrico escritorio',[-4.65,2.461,.95],3.141592653589793),
    (3,(191,56,1066,1195),1.28,'Quadro composicao sala jogos',[5.82,5.6,.95],1.5707963267948966),
    (4,(85,102,1000,1345),1.35,'Quadro abstrato hall esquerdo',[9.4,2.239,.95],0),
    (5,(114,122,973,1340),1.35,'Quadro abstrato hall direito',[10.6,2.239,.95],0)]:
    image=Image.open(P/'references'/f'print_{i}.png').crop(crop).convert('RGB')
    image.save(T/f'quadro_{i}_canvas.png')
    aspect=image.width/image.height;width=height*aspect
    colour=image.resize((1024,2048),Image.Resampling.LANCZOS)
    dds(colour,T/f'quadro_{i}_cor.dds')
    # Only high-frequency plaster/brush texture affects the shallow normal map;
    # composition blocks remain flat instead of becoming large raised shapes.
    grey=image.convert('L').resize((512,1024),Image.Resampling.LANCZOS)
    high=np.array(grey,dtype=np.float32)-np.array(grey.filter(ImageFilter.GaussianBlur(6)),dtype=np.float32)
    dy,dx=np.gradient(high/255)
    n=np.stack([-dx*1.4,dy*1.4,np.ones_like(dx)],axis=2);n/=np.linalg.norm(n,axis=2,keepdims=True)
    rgba=np.full((1024,512,4),255,dtype=np.uint8);rgba[:,:,:3]=np.clip(np.round((n+1)*127.5),0,255)
    dds(Image.fromarray(rgba),T/f'quadro_{i}_normal.dds',normal=True)
    rows.append(dict(print=i,name=label,model=f'mansao_quadro_ref_{i}',position=position,heading=heading,
        width_m=width+.056,height_m=height+.056,canvas_width_m=width,canvas_height_m=height,
        depth_m=.045,reference_crop=crop,source_canvas_size=image.size,frame='bronze' if i<4 else 'black'))
for name,rgb in [('spot_branco',(233,230,220)),('spot_metal',(155,145,127)),('spot_lente',(255,239,210)),
                 ('spot_prisma',(222,209,177)),('moldura_preta',(22,22,20)),('moldura_bronze',(63,54,39)),('moldura_filete',(131,110,71)),
                 ('quadro_fundo',(40,33,25)),('normal_plana',(128,128,255)),('metal_spec',(135,135,135))]:
    dds(Image.new('RGB',(4,4),rgb),T/(name+'.dds'),normal=name=='normal_plana')
(P/'artworks.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('REFERENCE_CANVASES_PREPARED',len(rows),'4-colour maps + subtle surface normals',flush=True)
