import sys,json,io,math,hashlib,collections,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'laboratorio_fivem/work/pydeps'),str(Path(__file__).parent/'render_deps'),r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps']
import numpy as np
from PIL import Image,ImageOps
import moderngl
from szio.gta5 import try_load_asset
from szio.vfs import VPath
from szio.rpf import open_rpf

OUT=ROOT/'catalogo_roupas_web/dist';OUT.mkdir(exist_ok=True)
(OUT/'previews').mkdir(exist_ok=True)
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V')
DATA=json.loads((Path(__file__).parent/'inventory.json').read_text())
CATEGORIES={'jbib':'Camisas e jaquetas','teef':'Blusas e camisetas internas','lowr':'Calças e shorts','feet':'Calçados','p_head':'Chapéus, bonés e gorros','p_eyes':'Óculos','p_ears':'Brincos','p_lwrist':'Relógios','p_rwrist':'Pulseiras','accs':'Acessórios','berd':'Máscaras','hand':'Bolsas e paraquedas','task':'Coletes'}
def vpath(path):
    bits=path.split('!/')
    if bits[0]=='base':base=GAME/'x64v.rpf';rest=bits[1:]
    elif bits[0]=='x64w.rpf':base=GAME/'x64w.rpf';rest=['dlcpacks/'+bits[1]+'/dlc.rpf']+bits[2:]
    elif bits[0]=='update.rpf':base=GAME/'update/update.rpf';rest=bits[1:]
    else:base=GAME/'update/x64/dlcpacks'/bits[0]/'dlc.rpf';rest=bits[1:]
    return VPath(str(base)+'/'+'/'.join(rest))

texgroups=collections.defaultdict(list)
for t in DATA['textures']:texgroups[(t['sex'],t['collection'],t['part'],t['index'])].append(t)
ctx=moderngl.create_standalone_context()
prog=ctx.program(vertex_shader='''#version 330
in vec3 position;in vec3 normal;in vec2 uv;
uniform vec3 center;uniform float fit;uniform float yaw;uniform float aspect;
out vec3 n;out vec2 texcoord;
void main(){float c=cos(yaw),s=sin(yaw);vec3 p=position-center;
vec3 r=vec3(c*p.x+s*p.y,-s*p.x+c*p.y,p.z);
gl_Position=vec4(r.x*fit/aspect,r.z*fit,r.y*fit*.1,1.0);
n=normalize(vec3(c*normal.x+s*normal.y,-s*normal.x+c*normal.y,normal.z));texcoord=uv;}
''',fragment_shader='''#version 330
in vec3 n;in vec2 texcoord;uniform sampler2D albedo;out vec4 color;
void main(){vec4 t=texture(albedo,texcoord);if(t.a<.15)discard;
float light=.58+.32*max(dot(normalize(n),normalize(vec3(-.5,-1,1))),0.)+.1*max(dot(normalize(n),vec3(1,0,0)),0.);
color=vec4(t.rgb*light,1.0);}
''')
SIZE=(512,640);fbo=ctx.simple_framebuffer(SIZE,components=4);fbo.use()
ctx.enable(moderngl.DEPTH_TEST)

def decode_texture(data):
    # Native A8 DDS stores opacity alone; Pillow does not decode this format.
    if data[:4]==b'DDS ' and len(data)>=128:
        flags=struct.unpack_from('<I',data,80)[0]
        bits=struct.unpack_from('<I',data,88)[0]
        if flags==2 and bits==8:
            height,width,pitch=struct.unpack_from('<3I',data,12)
            stride=max(width,pitch)
            alpha=np.frombuffer(data[128:128+stride*height],dtype=np.uint8).reshape(height,stride)[:,:width]
            rgba=np.full((height,width,4),255,dtype=np.uint8)
            rgba[:,:,3]=alpha
            return Image.fromarray(rgba)
    return Image.open(io.BytesIO(data)).convert('RGBA')

def prep(row,min_extent=.012,min_indices=9):
    asset=try_load_asset(vpath(row['path']))
    variations=sorted(texgroups[(row['sex'],row['collection'],row['part'],row['index'])],key=lambda t:t['variant'])
    if not variations:raise ValueError('no diffuse')
    selected=variations[0];txd=try_load_asset(vpath(selected['path']))
    textures=dict(txd.textures)
    pieces=[];points=[];triangles=0;missing=[]
    fallback=next(iter(textures.values()))
    for d in asset.drawables.values():
        textures.update(d.shader_group.embedded_textures)
        models=d.models[min(d.models)]
        for m in models:
            for g in m.geometries:
                v=g.vertex_buffer
                if len(g.index_buffer)<min_indices:continue
                params=d.shader_group.shaders[g.shader_index].parameters
                ref=next((p.value for p in params if p.name.lower()=='diffusesampler'),None)
                tex=textures.get(ref,fallback)
                image=decode_texture(tex.data.read_bytes());image.thumbnail((1024,1024))
                if np.asarray(image)[:,:,3].max()<20:continue
                rgba=ImageOps.flip(image)
                gpu=ctx.texture(rgba.size,4,rgba.tobytes());gpu.filter=(moderngl.LINEAR,moderngl.LINEAR)
                packed=np.column_stack((v['Position'],v['Normal'],v['TexCoord0'])).astype('f4')
                vb=ctx.buffer(packed.tobytes());ib=ctx.buffer(g.index_buffer.astype('u4').tobytes())
                vao=ctx.vertex_array(prog,[(vb,'3f 3f 2f','position','normal','uv')],ib,index_element_size=4)
                pieces.append((vao,gpu,vb,ib));points.append(v['Position']);triangles+=len(g.index_buffer)//3
    if not pieces:raise ValueError('empty model')
    p=np.concatenate(points);lo=p.min(axis=0);hi=p.max(axis=0)
    if max(hi-lo)<min_extent:raise ValueError('empty variant')
    return pieces,(lo+hi)/2,hi-lo,triangles,variations,selected

def render(pieces,center,extent,yaw,path):
    fbo.clear(.92,.93,.94,1,depth=1)
    prog['center'].value=tuple(center);prog['yaw'].value=yaw;prog['aspect'].value=SIZE[0]/SIZE[1]
    width=abs(math.cos(yaw))*extent[0]+abs(math.sin(yaw))*extent[1]
    prog['fit'].value=float(1.64/max(extent[2],width/(SIZE[0]/SIZE[1]),.01))
    for vao,gpu,_,_ in pieces:gpu.use(0);vao.render()
    image=Image.frombytes('RGBA',SIZE,fbo.read(components=4));image=ImageOps.flip(image).convert('RGB')
    image.save(path,format='WEBP',quality=85)

def collection_label(value):
    return value.replace('mp_m_freemode_01_p_','').replace('mp_f_freemode_01_p_','').replace('mp_m_freemode_01_','').replace('mp_f_freemode_01_','').replace('mp_m_freemode_01','Jogo base').replace('mp_f_freemode_01','Jogo base')

def main():
    rows=[];skips=[]
    for part,label in CATEGORIES.items():
        for sex in ['male','female']:
            candidates=[m for m in DATA['models'] if m['part']==part and m['sex']==sex and 'g9ec' not in m['collection']]
            # Prefer different original base shapes, then add DLC variety.
            candidates.sort(key=lambda m:(not m['collection'].endswith(('01','01_p')),m['index'],m['collection']))
            base=[m for m in candidates if m['collection'].endswith(('01','01_p')) and m['index']>0]
            dlc=[m for m in candidates if m not in base and m['index']>0]
            ordered=[]
            for i in range(max(len(base),len(dlc))):
                if i<len(base):ordered.append(base[i])
                if i<len(dlc):ordered.append(dlc[i])
            ordered+=[m for m in candidates if m not in ordered]
            accepted=0
            for row in ordered:
                if accepted==5:break
                pieces=[]
                try:
                    pieces,center,extent,triangles,variations,selected=prep(row)
                    ident=hashlib.sha1((row['collection']+part+str(row['index'])).encode()).hexdigest()[:12]
                    render(pieces,center,extent,.15,OUT/'previews'/f'{ident}.webp')
                    render(pieces,center,extent,math.pi+.15,OUT/'previews'/f'{ident}-back.webp')
                    record={'id':ident,'sex':sex,'category':part,'title':label,'collection':row['collection'],'collectionLabel':collection_label(row['collection']),'index':row['index'],'file':row['path'].split('/')[-1],'textureCount':len(variations),'textureFile':selected['path'].split('/')[-1],'triangles':triangles,'image':f'previews/{ident}.webp','back':f'previews/{ident}-back.webp'}
                    rows.append(record);accepted+=1
                    (OUT/'catalog.json').write_text(json.dumps({'build':3258,'samplePerCategory':10,'categories':CATEGORIES,'items':rows},ensure_ascii=False),encoding='utf-8')
                    print('READY',len(rows),part,sex,row['index'],flush=True)
                except Exception as e:skips.append({'model':row,'reason':str(e)});print('SKIP',part,str(e)[:140],flush=True)
                finally:
                    for piece in pieces:
                        for obj in piece:obj.release()
            assert accepted==5,(part,sex,accepted)
    (Path(__file__).parent/'render_report.json').write_text(json.dumps({'rendered':len(rows),'images':len(rows)*2,'renderer':ctx.info['GL_RENDERER'],'skipped':skips},indent=2),encoding='utf-8')
    print('COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
