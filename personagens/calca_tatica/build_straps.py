import copy,io,json,shutil
import numpy as np
from szio.gta5 import save_asset,AssetTarget,AssetFormat,AssetVersion,EmbeddedTexture
from szio.gta5.drawables import LodLevel
from szio.types import Vector,DataSource

def rotation(q):
    w,x,y,z=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
        [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
        [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def build_straps(r,base,anchors):
    out=base/'exports';stream=r.ROOT/'server-data/resources/cidade_roupas/stream'
    template=r.try_load_asset(r.ROOT/'laboratorio_fivem/work/translucent_shader_samples/v_ilev_prop_fib_glass.ydr')
    rig=r.try_load_asset(r.ROOT/'personagens/templates_freemode/source/mp_m_freemode_01.yft').drawable.skeleton
    matrices=[]
    for b in rig.bones:
        mat=np.eye(4);mat[:3,:3]=rotation(b.rotation);mat[:3,3]=b.position
        matrices.append(matrices[b.parent_index]@mat if b.parent_index>=0 else mat)
    image=r.Image.open(base/'textures/strap-alpha.png').convert('RGBA').resize((512,1024),r.Image.Resampling.LANCZOS)
    assert np.asarray(image)[:,:,3].min()==0,'Strap must have transparent silhouette'
    buf=io.BytesIO();image.save(buf,format='DDS',pixel_format='DXT5')
    typ=r.try_load_asset(r.ROOT/'server-data/resources/cidade_laboratorio/stream/cidade_laboratorio.ytyp')
    typ.name='ct_straps'
    archetype=copy.deepcopy(typ.archetypes[0]);typ.archetypes=[];config=[]
    definitions=[]
    for anchor in anchors:
        sign=1 if anchor[0]>0 else -1
        definitions.append(('ct_strap_'+('l' if sign>0 else 'r'),np.asarray(anchor),
                            58271 if sign>0 else 51826,.135,.10,(0,sign,0),(sign,0,0)))
    # Front-right waist; 29 cm tip extends past an untucked shirt.
    definitions.append(('ct_strap_belt',np.array([-.08,-.155,-.025]),11816,.29,.08,(1,0,0),(0,-1,0)))
    for name,anchor,tag,length,width,horizontal,normal in definitions:
        asset=copy.deepcopy(template);asset.name=name+'.#dr';asset.bounds=None;asset.lights=[]
        shader=asset.shader_group.shaders[0]
        asset.shader_group.shaders=[shader]
        asset.shader_group.embedded_textures={'ct_strap_tex':EmbeddedTexture('ct_strap_tex',*image.size,DataSource.create(buf.getvalue()))}
        for p in shader.parameters:
            if p.name.lower()=='diffusesampler':p.value='ct_strap_tex'
            elif isinstance(p.value,str):p.value=None
            elif p.name.lower() in ('reflectivepower','bumpiness','specularintensitymult'):p.value=Vector((0,0,0,0))
        g=copy.deepcopy(asset.models[LodLevel.HIGH][0].geometries[0])
        pts=[];ns=[];uvs=[]
        horiz=np.array(horizontal);norm=np.array(normal)
        # Double-sided 2 mm sheet. Top stays at the anchor; lower webbing has a slight curve.
        for face in (-1,1):
            for j in range(12):
                a,b=j/12,(j+1)/12
                def vertex(u,v):return horiz*((u-.5)*width)+np.array([0,0,-v*length])+norm*(face*.001+.004*np.sin(v*np.pi))
                for tex in (((0,a),(1,a),(1,b)),((0,a),(1,b),(0,b))):
                    tex=list(tex if face==1 else tex[::-1])
                    sample=np.array([vertex(u,v) for u,v in tex])
                    if np.dot(np.cross(sample[1]-sample[0],sample[2]-sample[0]),norm*face)<0:tex=tex[::-1]
                    pts.extend(vertex(u,v) for u,v in tex);ns.extend([norm*face]*3)
                    uvs.extend((u,1-v if tag==11816 else v) for u,v in tex)
        verts=np.zeros(len(pts),dtype=g.vertex_buffer.dtype)
        verts['Position']=pts;verts['Normal']=ns;verts['TexCoord0']=uvs;verts['Colour0']=255
        if 'Tangent' in verts.dtype.names:verts['Tangent']=(1,0,0,1)
        g.vertex_buffer=verts;g.index_buffer=np.arange(len(pts),dtype=np.uint16);g.shader_index=0
        m=asset.models[LodLevel.HIGH][0];m.geometries=[g];m.has_skin=False
        asset.models={LodLevel.HIGH:[m]};asset.lod_thresholds={LodLevel.HIGH:40}
        save_asset(asset,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),out,name)
        check=r.try_load_asset(out/(name+'.ydr'));assert check is not None
        ar=copy.deepcopy(archetype);ar.name=name;ar.asset_name=name;ar.physics_dictionary='';ar.texture_dictionary=''
        lo=verts['Position'].min(0);hi=verts['Position'].max(0)
        ar.bb_min=Vector(lo);ar.bb_max=Vector(hi);ar.bs_center=Vector((lo+hi)/2);ar.bs_radius=float(np.linalg.norm(hi-lo)/2)
        ar.lod_dist=40;ar.hd_texture_dist=40;typ.archetypes.append(ar)
        idx=next(i for i,b in enumerate(rig.bones) if b.tag==tag);mat=matrices[idx]
        inv=mat[:3,:3].T;offset=inv@(anchor-mat[:3,3])
        config.append({'model':name,'bone':tag,'offset':offset.tolist(),'axes':inv.T.tolist(),'length':length})
        shutil.copy2(out/(name+'.ydr'),stream/(name+'.ydr'))
    save_asset(typ,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),),out,'ct_straps')
    checktyp=r.try_load_asset(out/'ct_straps.ytyp')
    assert checktyp is not None and len(checktyp.archetypes)==3
    shutil.copy2(out/'ct_straps.ytyp',stream/'ct_straps.ytyp')
    (base/'strap-config.json').write_text(json.dumps(config,indent=2))
    (stream.parent/'data/ct_straps.json').write_text(json.dumps(config))
    print('STRAPS_OK',len(config),'props, skin anchors from native skeleton')
