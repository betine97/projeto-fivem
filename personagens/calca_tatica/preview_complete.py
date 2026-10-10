"""Render the exported trousers and independent straps at their rest anchors."""
import sys,io,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'catalogo_nativo'))
import render_catalog as r
from build_straps import rotation
base=Path(__file__).resolve().parent
rig=r.try_load_asset(r.ROOT/'personagens/templates_freemode/source/mp_m_freemode_01.yft').drawable.skeleton
matrices=[]
for b in rig.bones:
    mat=r.np.eye(4);mat[:3,:3]=rotation(b.rotation);mat[:3,3]=b.position
    matrices.append(matrices[b.parent_index]@mat if b.parent_index>=0 else mat)
pieces=[];points=[]
def add(drawable,textures,anchor=None):
    for m in drawable.models[0]:
        for g in m.geometries:
            v=g.vertex_buffer;p=v['Position'].copy()
            if anchor is not None:p+=anchor
            params=drawable.shader_group.shaders[g.shader_index].parameters
            name=next(p.value for p in params if p.name.lower()=='diffusesampler')
            image=r.Image.open(io.BytesIO(textures[name].data.read_bytes())).convert('RGBA')
            tex=r.ctx.texture(image.size,4,image.tobytes());tex.filter=(r.moderngl.LINEAR,r.moderngl.LINEAR)
            packed=r.np.column_stack((p,v['Normal'],v['TexCoord0'])).astype('f4')
            vb=r.ctx.buffer(packed.tobytes());ib=r.ctx.buffer(g.index_buffer.astype('u4').tobytes())
            vao=r.ctx.vertex_array(r.prog,[(vb,'3f 3f 2f','position','normal','uv')],ib,index_element_size=4)
            pieces.append((vao,tex,vb,ib));points.append(p)
d=next(iter(r.try_load_asset(base/'exports/lowr_006_r.ydd').drawables.values()))
textures=dict(r.try_load_asset(base/'exports/lowr_diff_006_a_whi.ytd').textures);textures.update(d.shader_group.embedded_textures)
add(d,textures)
for conf in json.loads((base/'strap-config.json').read_text()):
    idx=next(i for i,b in enumerate(rig.bones) if b.tag==conf['bone']);mat=matrices[idx]
    anchor=mat[:3,3]+mat[:3,:3]@r.np.array(conf['offset'])
    d=r.try_load_asset(base/'exports'/(conf['model']+'.ydr'));add(d,d.shader_group.embedded_textures,anchor)
p=r.np.concatenate(points);lo=p.min(0);hi=p.max(0)
for name,yaw in [('complete_front',.20),('complete_side',r.math.pi/2+.20),('complete_back',r.math.pi+.20)]:
    r.render(pieces,(lo+hi)/2,hi-lo,yaw,base/(name+'.webp'))
print('COMPLETE_PREVIEWS_OK')
