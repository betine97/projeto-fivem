"""Convert the supplied GLB directly to a streamed GTA ped. No Blender dependency."""
import sys, struct, json, io, copy, shutil, hashlib, gc
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[r'C:\Users\erons\Documents\Codex\2026-10-02\projeto-fivem-3d\work\deps',str(ROOT/'laboratorio_fivem/work/pydeps')]
import numpy as np
from PIL import Image
from szio.gta5 import try_load_asset, save_asset, AssetTarget, AssetFormat, AssetVersion, EmbeddedTexture, LodLevel
from szio.types import DataSource

BASE=ROOT/'personagens/person2'
OUT=BASE/'exports'
TEX=BASE/'textures'
SOURCE=Path(r'C:\Users\erons\Downloads\Meshy_AI_hazmat_worker_lowpoly_1005172433_texture.glb')
GUARD=ROOT/'personagens/traje_guarda/exports'

def read_glb(path):
    raw=path.read_bytes()
    assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,4)[0]==2
    n=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+n]); binary=raw[28+n:]
    def accessor(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
        dtype={5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']]
        dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        assert 'byteStride' not in v and 'sparse' not in a
        off=v.get('byteOffset',0)+a.get('byteOffset',0)
        return np.frombuffer(binary,dtype=dtype,count=a['count']*dim,offset=off).reshape(a['count'],dim).copy()
    def image_bytes(i):
        v=doc['bufferViews'][doc['images'][i]['bufferView']]
        off=v.get('byteOffset',0)
        return binary[off:off+v['byteLength']]
    assert len(doc['meshes'])==1 and len(doc['meshes'][0]['primitives'])==1
    assert doc.get('skins') is None
    assert len(doc['nodes'])==1 and set(doc['nodes'][0])<={'mesh','name'}
    p=doc['meshes'][0]['primitives'][0]
    assert p.get('mode',4)==4
    return doc,accessor(p['attributes']['POSITION']),accessor(p['attributes']['NORMAL']),accessor(p['attributes']['TEXCOORD_0']),accessor(p['indices']).ravel(),image_bytes

def native_axes(values):
    return np.column_stack((values[:,0],-values[:,2],values[:,1])).astype(np.float32)

def save_dds_game(image,path):
    # Native DDS and source PNG both use top-down pixel storage. UV V is
    # converted once below; flipping the image too would corrupt atlas lookup.
    # This supplied atlas is completely opaque. BC1 preserves its 4K
    # resolution while keeping the streamed texture dictionary below 16 MiB.
    assert np.asarray(image.convert('RGBA'))[:,:,3].min()==255 or 'spec' in path.name
    image.convert('RGB').save(path,format='DDS',pixel_format='DXT1')

def bind_weights(positions,donor,bones):
    # Region-constrained transfer prevents hands inheriting pelvis weights.
    rows=[];weights=[]
    for drawable in donor.drawables.values():
        for model in drawable.models.get(LodLevel.HIGH,[]):
            for g in model.geometries:
                v=g.vertex_buffer
                dense=np.zeros((len(v),len(bones)),np.float32)
                for col in range(4):
                    np.add.at(dense,(np.arange(len(v)),g.bone_ids[v['BlendIndices'][:,col]]),v['BlendWeights'][:,col]/255.)
                rows.append(v['Position']);weights.append(dense)
    ref=np.concatenate(rows);dw=np.concatenate(weights)
    ref,unique=np.unique(ref,axis=0,return_index=True);dw=dw[unique]
    names=[b.name for b in bones];ids={n:i for i,n in enumerate(names)}
    result=np.zeros((len(positions),len(bones)),np.float32)
    for key in ['body','L_arm','R_arm','L_leg','R_leg','head']:
        side='L' if key.startswith('L') else 'R'
        sign=1 if side=='L' else -1
        def regions(p):
            head=p[:,2]>.53
            arm=(abs(p[:,0])>(.215+np.maximum(0,.40-p[:,2])*.18))&(p[:,2]>-.40)&~head
            leg=(p[:,2]<-.17)&~arm
            s=p[:,0]*sign>=0
            return head if key=='head' else arm&s if key.endswith('_arm') else leg&s if key.endswith('_leg') else ~head&~arm&~leg
        dest=np.flatnonzero(regions(positions));source=np.flatnonzero(regions(ref))
        if not len(dest):continue
        if key=='head':result[dest,ids['SKEL_Head']]=1;continue
        local=dw[source].copy()
        for i,name in enumerate(names):
            if name.startswith('FB_'):
                local[:,ids['SKEL_Head']]+=local[:,i];local[:,i]=0
            elif name.startswith('MH_'):local[:,i]=0
            elif key.endswith('_arm') and not ('_'+side+'_' in name and any(s in name for s in ['UpperArm','Forearm','Hand','Finger','ArmRoll'])):local[:,i]=0
            elif key.endswith('_leg') and not (name=='SKEL_Pelvis' or ('_'+side+'_' in name and any(s in name for s in ['Thigh','Calf','Foot','Toe']))):local[:,i]=0
        for start in range(0,len(dest),128):
            ix=dest[start:start+128]
            ds=np.sum((positions[ix,None,:]-ref[source][None,:,:])**2,axis=2)
            k=min(8,len(source));near=np.argpartition(ds,k-1,axis=1)[:,:k]
            fac=1/np.maximum(np.take_along_axis(ds,near,axis=1),.006**2)**1.5
            acc=(local[near]*fac[:,:,None]).sum(axis=1)
            fallback=ids['SKEL_'+side+'_UpperArm' if key.endswith('_arm') else 'SKEL_'+side+'_Thigh' if key.endswith('_leg') else 'SKEL_Spine2']
            acc[acc.sum(axis=1)<1e-9,fallback]=1
            result[ix]=acc
    crotch=(positions[:,2]<-.17)&(positions[:,2]>-.32)&(abs(positions[:,0])<.07)
    t=np.clip((-.17-positions[crotch,2])/.15,0,1);left=np.clip((positions[crotch,0]+.07)/.14,0,1)
    result[crotch]=0
    result[crotch,ids['SKEL_Pelvis']]=1-t
    result[crotch,ids['SKEL_L_Thigh']]=t*left
    result[crotch,ids['SKEL_R_Thigh']]=t*(1-left)
    top=np.argsort(-result,axis=1)[:,:4]
    selected=np.take_along_axis(result,top,axis=1)
    assert np.all(selected.sum(axis=1)>0)
    selected/=selected.sum(axis=1)[:,None]
    scaled=selected*255
    quant=np.floor(scaled).astype(np.uint8)
    fractions=scaled-quant
    for row in range(len(quant)):
        for col in np.argsort(-fractions[row])[:255-int(quant[row].sum())]:quant[row,col]+=1
    return top.astype(np.uint8),quant

def tangents(pos,normal,uv,index):
    faces=index.reshape(-1,3);a,b,c=faces.T
    e1=pos[b]-pos[a];e2=pos[c]-pos[a];d1=uv[b]-uv[a];d2=uv[c]-uv[a]
    det=d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0]
    factor=np.divide(1.,det,out=np.zeros_like(det),where=abs(det)>1e-10)
    ts=(e1*d2[:,1,None]-e2*d1[:,1,None])*factor[:,None]
    bs=(e2*d1[:,0,None]-e1*d2[:,0,None])*factor[:,None]
    tan=np.zeros_like(pos);bit=np.zeros_like(pos)
    for corner in [a,b,c]:np.add.at(tan,corner,ts);np.add.at(bit,corner,bs)
    tan-=normal*np.sum(tan*normal,axis=1)[:,None]
    length=np.linalg.norm(tan,axis=1)
    missing=length<1e-9
    axis=np.tile([1.,0.,0.],(len(pos),1));axis[abs(normal[:,0])>.9]=[0,1,0]
    tan[missing]=np.cross(normal[missing],axis[missing])
    tan/=np.maximum(np.linalg.norm(tan,axis=1)[:,None],1e-9)
    w=np.where(np.sum(np.cross(normal,tan)*bit,axis=1)<0,-1.,1.)
    return np.column_stack((tan,w)).astype(np.float32)

def render_front(pos,normal,uv,index,texture,path):
    # Small software rasterizer for native asset verification, not a game capture.
    width,height=640,1000;scale=490
    screen=np.column_stack((width/2+pos[:,0]*scale,50+(pos[:,2].max()-pos[:,2])*scale))
    canvas=np.full((height,width,4),[28,31,35,255],np.uint8);depth=np.full((height,width),np.inf)
    pixels=np.asarray(texture.convert('RGB'));th,tw=pixels.shape[:2]
    for tri in index.reshape(-1,3):
        p=screen[tri]
        x0,y0=np.maximum(np.floor(p.min(axis=0)).astype(int),[0,0]);x1,y1=np.minimum(np.ceil(p.max(axis=0)).astype(int),[width-1,height-1])
        if x1<x0 or y1<y0:continue
        denominator=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
        if abs(denominator)<1e-9:continue
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
        b0=((p[1,1]-p[2,1])*(xx-p[2,0])+(p[2,0]-p[1,0])*(yy-p[2,1]))/denominator
        b1=((p[2,1]-p[0,1])*(xx-p[2,0])+(p[0,0]-p[2,0])*(yy-p[2,1]))/denominator;b2=1-b0-b1
        bary=np.stack((b0,b1,b2),axis=-1);z=bary@pos[tri,1]
        sub=depth[y0:y1+1,x0:x1+1];mask=(bary.min(axis=-1)>=-1e-5)&(z<sub)
        if not np.any(mask):continue
        coords=bary@uv[tri];tx=np.clip(np.rint(coords[:,:,0]*(tw-1)).astype(int),0,tw-1);ty=np.clip(np.rint((1-coords[:,:,1])*(th-1)).astype(int),0,th-1)
        norm=bary@normal[tri]
        shade=.55+.45*np.maximum(0,norm@np.array([-.35,-.85,.4]))
        color=np.clip(pixels[ty,tx]*shade[:,:,None],0,255).astype(np.uint8)
        canvas[y0:y1+1,x0:x1+1,:3][mask]=color[mask];sub[mask]=z[mask]
    Image.fromarray(canvas).save(path)

def main():
    OUT.mkdir(exist_ok=True);TEX.mkdir(exist_ok=True)
    doc,original,normals,source_uv,index,image_bytes=read_glb(SOURCE)
    position=native_axes(original);position[:,2]-=np.float32(1.002028)
    normal=native_axes(normals)
    uv=source_uv.copy();uv[:,1]=1-uv[:,1]
    dictionary=try_load_asset(GUARD/'guardalab.ydd')
    donor=try_load_asset(ROOT/'animacoes/work/assets/a_m_y_business_01.ydd')
    bones=next(d.skeleton.bones for d in donor.drawables.values() if d.skeleton)
    actual=max(dictionary.drawables.values(),key=lambda d:sum(len(g.index_buffer) for m in d.models[LodLevel.HIGH] for g in m.geometries))
    model=copy.deepcopy(actual.models[LodLevel.HIGH][0]);geometry=copy.deepcopy(model.geometries[0])
    model.geometries=[geometry]
    indices,weights=bind_weights(position,donor,bones)
    vertices=np.zeros(len(position),dtype=geometry.vertex_buffer.dtype)
    vertices['Position']=position;vertices['Normal']=normal
    vertices['TexCoord0']=uv;vertices['TexCoord1']=uv
    vertices['BlendIndices']=indices;vertices['BlendWeights']=weights
    vertices['Colour0']=[255,128,0,255]
    vertices['Tangent']=tangents(position,normal,uv,index)
    geometry.vertex_buffer=vertices;geometry.index_buffer=index.astype(np.uint16)
    geometry.bone_ids=np.arange(len(bones),dtype=np.uint16);geometry.shader_index=1
    model.matrix_count=len(bones)
    actual.models={lod:[copy.deepcopy(model)] for lod in LodLevel}
    txd=try_load_asset(GUARD/'guardalab.ytd')
    material=doc['materials'][0]['pbrMetallicRoughness']
    diff_id=doc['textures'][material['baseColorTexture']['index']]['source']
    mr_id=doc['textures'][material['metallicRoughnessTexture']['index']]['source']
    for i,name in [(diff_id,'original_diffuse.png'),(mr_id,'original_metallic_roughness.png')]:
        (TEX/name).write_bytes(image_bytes(i))
    diffuse=Image.open(TEX/'original_diffuse.png').convert('RGBA')
    orm=np.asarray(Image.open(TEX/'original_metallic_roughness.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS),dtype=np.float32)/255
    reflectance=np.clip(.06+.42*(1-orm[:,:,1])**2+.08*orm[:,:,2],0,1)
    spec=np.zeros((*reflectance.shape,4),np.uint8);spec[:,:,:3]=np.rint(reflectance[:,:,None]*255).astype(np.uint8)
    maps={'uppr_diff_000_a_uni':diffuse,'uppr_normal_000':Image.new('RGBA',(16,16),(128,128,255,255)),'uppr_spec_000':Image.fromarray(spec)}
    for name,image in maps.items():
        path=TEX/(name+'.dds');save_dds_game(image,path)
        txd.textures[name]=EmbeddedTexture(name,image.width,image.height,DataSource.create(path))
    for drawable in dictionary.drawables.values():
        drawable.shader_group.embedded_textures.clear()
    target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
    save_asset(dictionary,target,OUT,'person2');save_asset(txd,target,OUT,'person2')
    for ext in ['yft','ymt']:shutil.copy2(GUARD/('guardalab.'+ext),OUT/('person2.'+ext))
    meta=ET.parse(GUARD/'guardalab_peds.meta');meta.getroot().find('InitDatas/Item/Name').text='person2'
    ET.indent(meta);meta.write(OUT/'person2_peds.meta',encoding='utf-8',xml_declaration=True)
    roundtrip=try_load_asset(OUT/'person2.ydd')
    result=roundtrip.drawables['hash_7CEAC270'].models[LodLevel.HIGH][0].geometries[0]
    assert np.array_equal(result.vertex_buffer['Position'],position)
    assert np.array_equal(result.vertex_buffer['TexCoord0'],uv)
    assert np.array_equal(result.index_buffer,index)
    assert np.all(result.vertex_buffer['BlendWeights'].sum(axis=1)==255)
    assert result.bone_ids.max()<len(bones)
    native_txd=try_load_asset(OUT/'person2.ytd')
    native_diffuse=Image.open(io.BytesIO(native_txd.textures['uppr_diff_000_a_uni'].data.read_bytes())).convert('RGBA')
    error=np.asarray(native_diffuse,dtype=np.float32)[:,:,:3]-np.asarray(diffuse,dtype=np.float32)[:,:,:3]
    color_rmse=float(np.sqrt(np.mean(error**2)))
    assert native_diffuse.size==diffuse.size and color_rmse<8, 'Texture compression exceeded color tolerance'
    for d in roundtrip.drawables.values():
        for m in d.models[LodLevel.HIGH]:
            for g in m.geometries:
                for p in d.shader_group.shaders[g.shader_index].parameters:
                    if isinstance(p.value,str):assert p.value in native_txd.textures
    render_front(result.vertex_buffer['Position'],result.vertex_buffer['Normal'],result.vertex_buffer['TexCoord0'],result.index_buffer,native_diffuse,BASE/'preview_native.png')
    report={'source':str(SOURCE),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'used_blender':False,'vertices':len(position),'triangles':len(index)//3,'geometry_preserved':True,'uv_preserved_with_native_v_conversion':True,'original_diffuse_png_preserved_exactly':True,'gpu_texture_format':'BC1','color_compression_rmse_0_255':color_rmse,'color_compression_psnr_db':float(20*np.log10(255/max(color_rmse,1e-9))),'diffuse_size':diffuse.size,'bones':len(bones),'max_influences':4,'unweighted_vertices':0,'full_original_mesh_at_all_lods':True,'command':'person2','files':{p.name:p.stat().st_size for p in OUT.iterdir() if p.suffix in {'.ydd','.ytd','.yft','.ymt','.meta'}}}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2))
    print('PERSON2_NATIVE_OK',json.dumps(report),flush=True)
    gc.collect()

if __name__=='__main__':main()
