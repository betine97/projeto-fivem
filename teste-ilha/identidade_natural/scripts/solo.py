from common import *
import copy,struct,re,collections
from szio.gta5 import *
from szio.gta5.drawables import Geometry,Model,ShaderGroup,VertexDataType
from szio.gta5.bounds import CollisionMaterial
from szio.types import Vector,DataSource
F=np.load(O/'dados/biomas.npz');mask=F['mask'];normal=F['normals'];tangent=F['tangents']
rows=read(P/'porto_construido/qualidade_terreno/dados/terrain_quality.json')['sectors']
T=O/'terreno';T.mkdir(exist_ok=True);target=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
cfg=read(P/'amostra_natural/config.json');layers=[cfg['layers'][i] for i in [0,4,2,3]]
track=cfg['layers'][1];cliff=dict(diffuse='cs_sl_rsn_canyon_rock_01',normal='cs_sl_rsn_canyon_rock_01_n')
textures={};palette=[layers, layers[:2]+[track,layers[3]], layers[:3]+[cliff]]
for family in palette:
    for layer in family:
        for channel in ['diffuse','normal']:
            name=layer[channel];src=O/'texturas'/(name+'.dds')
            if not src.exists():src=P/'amostra_natural/texturas'/(name+'.dds')
            data=src.read_bytes();h,w=struct.unpack_from('<II',data,12);textures[name]=EmbeddedTexture(name,w,h,DataSource.create(data,name=name+'.dds'))
save_asset(AssetTextureDictionary(textures=textures),target,T,'ni_solo')
shaders=[]
pilot=try_load_asset(P/'amostra_natural/exportados/ti_terreno_03_01.ydr')
for family in palette:
    shader=copy.deepcopy(next(s for s in pilot.shader_group.shaders if s.preset_filename=='terrain_cb_4lyr.sps'));shader.name='terrain_cb_4lyr'
    refs={**{'texturesampler_layer'+str(i):l['diffuse'] for i,l in enumerate(family)},**{'bumpsampler_layer'+str(i):l['normal'] for i,l in enumerate(family)}}
    for p in shader.parameters:
        key=str(p.name).lower()
        if key in refs:p.value=refs[key]
        elif key=='specularintensitymult':p.value=Vector((.012,0,0,0))
        elif key=='wetnessmultiplier':p.value=Vector((.3,0,0,0))
    shaders.append(shader)
typ=try_load_asset(R/'server-data/resources/teste_ilha/stream/teste_ilha.ytyp')
materials=re.findall(r'CollisionMaterialDef\("([A-Z_0-9]+)"',Path(r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz/Sollumz/ybn/collision_materials.py').read_text())
dt=np.dtype([('Position','<f4',3),('Normal','<f4',3),('Colour0','u1',4),('Colour1','u1',4),('TexCoord0','<f4',2),('Tangent','<f4',4)])
def faces(n):
    j,i=np.meshgrid(np.arange(n-1),np.arange(n-1),indexing='ij');q=(j*n+i).ravel()
    return np.stack([np.stack([q,q+1,q+n+1],1),np.stack([q,q+n+1,q+n],1)],1).reshape(-1,3).astype(np.uint16)
report=[]
for row in rows:
    name=row['name'];x0,y0,x1,y1=row['grid_bounds'];center=np.array(row['center']);a=AssetDrawable(name=name,shader_group=ShaderGroup(copy.deepcopy(shaders),{}));lodcounts={}
    for lod,step in zip([LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW],[1,2,4,8]):
        g=grid[y0:y1+1:step,x0:x1+1:step];n=len(g);v=np.zeros(n*n,dt);v['Position']=g.reshape(-1,3)-center;v['Normal']=normal[y0:y1+1:step,x0:x1+1:step].reshape(-1,3);v['Colour0']=255;v['Colour1']=mask[y0:y1+1:step,x0:x1+1:step].reshape(-1,4);v['TexCoord0']=g[:,:,:2].reshape(-1,2)/6;v['TexCoord0'][:,1]=1-v['TexCoord0'][:,1];v['Tangent'][:,:3]=tangent[y0:y1+1:step,x0:x1+1:step].reshape(-1,3);v['Tangent'][:,3]=1
        tri=faces(n);p=g.reshape(-1,3)[tri].mean(1);road=sample(F['road_distance'],p[:,0],p[:,1])<1.5
        family=np.where(p[:,2]>95,2,np.where(road,1,0));geometries=[]
        for k in range(3):
            inds=tri[family==k].ravel()
            if len(inds):geometries.append(Geometry(VertexDataType.DEFAULT,v.copy(),inds,np.array([],np.uint16),k))
        a.models[lod]=[Model(0,geometries,1,False,0,0)];lodcounts[lod.name]=len(tri)
    a.lod_thresholds=dict(zip([LodLevel.HIGH,LodLevel.MEDIUM,LodLevel.LOW,LodLevel.VERYLOW],[420,850,1800,6500]));a.bounds=None;save_asset(a,target,T,name)
    arch=next(t for t in typ.archetypes if str(t.name)==name);arch.texture_dictionary='ni_solo'
    # Preserve exact old terrain vertices and primitive topology; only replace surface material responses.
    col=try_load_asset(R/'server-data/resources/teste_ilha/stream'/(name+'.ybn'));before=[];matcounts=collections.Counter()
    for child in col.children:
        verts=np.array([list(v.co) for v in child.geometry_vertices]);before.append(verts)
        triangles=np.array([list(p.vertices) for p in child.geometry_primitives]);centers=verts[triangles].mean(1)
        gx,by=sample(mask[...,1],centers[:,0],centers[:,1])/255,sample(mask[...,2],centers[:,0],centers[:,1])/255
        mix=np.stack([(1-gx)*(1-by),(1-gx)*by,gx*(1-by),gx*by],1)
        surface=np.asarray(['GRASS','SAND_LOOSE','MUD_SOFT','ROCK'])[mix.argmax(1)]
        surface=np.where(sample(F['road_distance'],centers[:,0],centers[:,1])<1.5,'DIRT_TRACK',surface)
        for primitive,m in zip(child.geometry_primitives,surface):
            primitive.material=CollisionMaterial.from_packed(materials.index(str(m)));matcounts[str(m)]+=1
    save_asset(col,target,T,name)
    reloaded=try_load_asset(T/(name+'.ybn'))
    for child,old in zip(reloaded.children,before):
        now=np.array([list(v.co) for v in child.geometry_vertices]);assert now.shape==old.shape and np.max(abs(old-now))<.015,name
    report.append(dict(name=name,lod_triangles=lodcounts,collision_materials=dict(matcounts),original_collision_sha256=sha(R/'server-data/resources/teste_ilha/stream'/(name+'.ybn'))))
    print('NATIVE_SOIL_READY',name,flush=True)
save_asset(typ,target,T,'teste_ilha')
write(O/'dados/solo.json',dict(sectors=report,layers=palette,textures=list(textures),geometry_unchanged=True,terrain_npz_sha256=sha(P/'porto_construido/dados/terreno.npz'),client_visual_verified=False))
print('NATIVE_SOIL_COMPLETE',len(rows),'sectors',flush=True)
