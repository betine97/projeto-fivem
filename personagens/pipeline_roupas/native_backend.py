"""Native extraction, semantic surface checks and isolated candidate exports."""
import copy
import hashlib
import io
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from szio.gta5 import AssetFormat, AssetTarget, AssetVersion, EmbeddedTexture, save_asset, try_load_asset
from szio.gta5.shader import ShaderManager  # Load native hashed parameter names before reading assets.
from szio.gta5 import jenkhash
from szio.rpf import open_rpf
from szio.types import DataSource
from szio.vfs import VPath

TARGETS = (AssetTarget(AssetFormat.NATIVE, AssetVersion.GEN8),)


def signature(geometry):
    payload = geometry.vertex_buffer.tobytes() + geometry.index_buffer.tobytes() + geometry.bone_ids.tobytes()
    payload += str(geometry.shader_index).encode()
    return hashlib.sha256(payload).hexdigest()


def material_signature(drawable):
    textures = {name: hashlib.sha256(tex.data.read_bytes()).hexdigest()
                for name, tex in drawable.shader_group.embedded_textures.items()}
    shaders = [(s.name, s.preset_filename, int(s.render_bucket),
                [(p.name, str(p.value)) for p in s.parameters if p.name.lower() != 'diffusesampler'])
               for s in drawable.shader_group.shaders]
    return {'textures': textures, 'shaders': shaders, 'skeleton': repr(drawable.skeleton)}


def geometry_manifest(asset):
    return [{'drawable': str(key), 'lod': int(lod), 'model': mi, 'geometry': gi,
             'signature': signature(g), 'vertices': len(g.vertex_buffer),
             'triangles': len(g.index_buffer)//3}
            for key, d in asset.drawables.items() for lod, models in d.models.items()
            for mi, m in enumerate(models) for gi, g in enumerate(m.geometries)]


def sample(geometry, uv):
    """Barycentric surface sample; reject UVs that map to separate body regions."""
    vertices = geometry.vertex_buffer
    ids = geometry.index_buffer.reshape(-1, 3)
    coords = vertices['TexCoord0'][ids]
    a = coords[:, 0]; e = coords[:, 1]-a; f = coords[:, 2]-a
    det = e[:, 0]*f[:, 1]-e[:, 1]*f[:, 0]; valid = np.abs(det)>1e-9
    q = np.asarray(uv)-a
    b = np.divide(q[:,0]*f[:,1]-q[:,1]*f[:,0],det,out=np.zeros_like(det),where=valid)
    c = np.divide(e[:,0]*q[:,1]-e[:,1]*q[:,0],det,out=np.zeros_like(det),where=valid)
    weights = np.column_stack((1-b-c,b,c)); hits = np.flatnonzero(valid & (weights.min(1)>=-1e-5))
    if not len(hits):
        raise ValueError(f'UV {uv} fora da superfície da base.')
    positions = (vertices['Position'][ids[hits]] * weights[hits,:,None]).sum(1)
    if np.max(np.linalg.norm(positions-positions[0], axis=1)) > .002:
        raise ValueError(f'UV {uv} ambíguo: ilhas sobrepostas levam a regiões 3D diferentes.')
    k = hits[0]; w = np.clip(weights[k],0,1); w /= w.sum(); tri = vertices[ids[k]]
    row = tri[np.argmax(w)].copy()
    for name in ('Position','Normal','Tangent','TexCoord1'):
        if name in vertices.dtype.names:
            row[name] = (tri[name]*w[:,None]).sum(0)
    row['Normal'] /= max(np.linalg.norm(row['Normal']),1e-8)
    row['TexCoord0'] = uv
    if 'BlendWeights' in vertices.dtype.names:
        bone_weights = {}
        for vertex, factor in zip(tri,w):
            for bone, weight in zip(vertex['BlendIndices'],vertex['BlendWeights']):
                bone_weights[int(bone)] = bone_weights.get(int(bone),0)+float(weight)*factor
        selected = sorted(bone_weights.items(),key=lambda pair:pair[1],reverse=True)[:4]
        total = sum(weight for _,weight in selected)
        if total <= 0:
            raise ValueError('A superfície amostrada não possui pesos de pele válidos.')
        scaled = np.rint([weight/total*255 for _,weight in selected]).astype(int)
        scaled[0] += 255-scaled.sum()
        row['BlendIndices'] = 0; row['BlendWeights'] = 0
        for index, ((bone,_),weight) in enumerate(zip(selected,scaled)):
            row['BlendIndices'][index] = bone; row['BlendWeights'][index] = weight
    return row


def region_errors(row, region):
    """GTA rest coordinates: +X character left, -Y front, +Z up, pelvis origin."""
    if not isinstance(region,dict) or region.get('side') not in ('left','right','center'):
        raise ValueError('Declare region.side: left, right ou center.')
    if region.get('face') not in ('outer','front','back','inner'):
        raise ValueError('Declare region.face: outer, front, back ou inner.')
    x,y,z = row['Position']; nx,ny,_ = row['Normal']; errors=[]
    side=region['side']; face=region['face']
    if side=='left' and x<.01 or side=='right' and x>-.01:
        errors.append('Elemento no lado oposto do personagem.')
    if side=='center' and abs(x)>.08:
        errors.append('Elemento fora da faixa central declarada.')
    if face=='outer' and np.sign(x)*nx<.20:
        errors.append('Elemento fora da lateral externa; possível parte interna da coxa.')
    if face=='inner' and np.sign(x)*nx>-.20:
        errors.append('Elemento fora da lateral interna declarada.')
    if face=='front' and ny>-.20 or face=='back' and ny<.20:
        errors.append('Elemento na face oposta à direção declarada.')
    bounds=region.get('z_range_m')
    if bounds is not None and (len(bounds)!=2 or not bounds[0]<=z<=bounds[1]):
        errors.append('Altura fora da faixa declarada em metros na pose de repouso.')
    return errors


class Backend:
    def __init__(self,cfg,root):
        self.cfg,self.root=cfg,root
        self.inventory=json.loads((root/cfg['inventory']).read_text(encoding='utf-8'))
        self.game=Path(cfg['game'])

    def vpath(self,path):
        bits=path.split('!/')
        if bits[0]=='base':
            archive=self.game/'x64v.rpf'; rest=bits[1:]
        elif bits[0]=='x64w.rpf':
            archive=self.game/'x64w.rpf'; rest=['dlcpacks/'+bits[1]+'/dlc.rpf']+bits[2:]
        elif bits[0]=='update.rpf':
            archive=self.game/'update/update.rpf'; rest=bits[1:]
        else:
            archive=self.game/'update/x64/dlcpacks'/bits[0]/'dlc.rpf'; rest=bits[1:]
        return VPath(str(archive)+'/'+'/'.join(rest)),archive

    def extract(self,item,folder):
        (folder/'source').mkdir(parents=True,exist_ok=True)
        key=lambda row: all(row[k]==v for k,v in {'sex':item['sex'],'collection':item['collection'],'part':item['category'],'index':item['index']}.items())
        model=next(m for m in self.inventory['models'] if key(m) and Path(m['path']).name==item['file'])
        texture=next(t for t in self.inventory['textures'] if key(t) and Path(t['path']).name==item['textureFile'])
        archives={}; paths={}
        for kind,row in (('model',model),('texture',texture)):
            vpath,archive=self.vpath(row['path']);asset=try_load_asset(vpath)
            if asset is None:
                raise ValueError('Arquivo nativo não pôde ser carregado: '+row['path'])
            name=Path(row['path']).name
            save_asset(asset,TARGETS,folder/'source',Path(name).stem)
            paths[kind]=str(Path('source')/name)
            archives[str(archive)]=[archive.stat().st_size,archive.stat().st_mtime_ns]
        ped='mp_m_freemode_01' if item['sex']=='male' else 'mp_f_freemode_01'
        archive=self.game/'x64v.rpf'
        rpf=open_rpf(archive)
        nested=rpf.open_nested('models/cdimages/streamedpeds_mp.rpf')
        (folder/'source'/f'{ped}.yft').write_bytes(nested.read_bytes(f'{ped}.yft'))
        archives[str(archive)]=[archive.stat().st_size,archive.stat().st_mtime_ns]
        paths['rig']=str(Path('source')/f'{ped}.yft')
        asset=try_load_asset(folder/paths['model']);txd=try_load_asset(folder/paths['texture'])
        originals=geometry_manifest(asset)
        texture_dir=folder/'source'/'textures';texture_dir.mkdir(exist_ok=True)
        textures=dict(txd.textures)
        for drawable in asset.drawables.values():
            textures.update(drawable.shader_group.embedded_textures)
        for name,tex in textures.items():
            (texture_dir/(name+'.dds')).write_bytes(tex.data.read_bytes())
        self.uv_guide(asset,folder/'uv_regions.png')
        return {'paths':paths,'archives':archives,'geometry':originals,
                'coordinates':{'left':'+X','front':'-Y','up':'+Z','origin':'native pelvis','unit':'metre'},
                'textures':list(textures),'archive_sources':{'model':model['path'],'texture':texture['path']}}

    def uv_guide(self,asset,path):
        image=Image.new('RGB',(1024,1024),(28,32,37));draw=ImageDraw.Draw(image)
        colors={'front':(83,180,104),'back':(197,141,58),'outer':(60,142,215),'inner':(192,74,108),'other':(76,83,91)}
        for drawable in asset.drawables.values():
            for model in drawable.models[min(drawable.models)]:
                for geometry in model.geometries:
                    v=geometry.vertex_buffer
                    for tri in geometry.index_buffer.reshape(-1,3):
                        pos=v['Position'][tri].mean(0);normal=v['Normal'][tri].mean(0)
                        face=('outer' if np.sign(pos[0])*normal[0]>.45 else 'inner' if np.sign(pos[0])*normal[0]<-.45 else 'front' if normal[1]<-.45 else 'back' if normal[1]>.45 else 'other')
                        draw.polygon([tuple(uv*1023) for uv in v['TexCoord0'][tri]],fill=colors[face],outline=(130,130,130))
        draw.rectangle((0,0,1024,32),fill=(20,23,27));draw.text((10,9),'BLUE outer | PINK inner | GREEN front | OCHRE back | native UV',fill=(255,255,255))
        image.save(path)

    def check_anchor(self,base,part):
        source=json.loads((base/'base.json').read_text(encoding='utf-8'))
        asset=try_load_asset(base/source['paths']['model'])
        u0,v0,u1,v1=part['uv_rect']
        if not 0<=u0<u1<=1 or not 0<=v0<v1<=1:
            raise ValueError('Retângulo UV inválido.')
        drawables=list(asset.drawables.values())
        for name in ('drawable','model','geometry'):
            index=part.get(name,0)
            if not isinstance(index,int) or isinstance(index,bool) or index<0:
                raise ValueError(f'Índice de {name} inválido.')
        if part.get('drawable',0)>=len(drawables):
            raise ValueError('Drawable do componente não existe na base.')
        d=drawables[part.get('drawable',0)]
        errors=[];points=[];lod_reports=[]
        # Use exactly the tessellation points that will be exported, for every LOD.
        for lod, models in d.models.items():
            if part.get('model',0)>=len(models) or part.get('geometry',0)>=len(models[part.get('model',0)].geometries):
                raise ValueError(f'Modelo/geometria do componente não existe no LOD {int(lod)}.')
            g=models[part.get('model',0)].geometries[part.get('geometry',0)]
            steps=8 if int(lod)==0 else 4; local_points=[]; local_errors=[]
            for v in np.linspace(v0,v1,steps+1):
                for u in np.linspace(u0,u1,steps+1):
                    row=sample(g,(float(u),float(v)));local_points.append(row['Position'].tolist())
                    local_errors.extend(region_errors(row,part['region']))
            errors.extend(f'LOD {int(lod)}: {e}' for e in local_errors);points.extend(local_points)
            lod_reports.append({'lod':int(lod),'samples':len(local_points),
                                'bounds_m':[np.min(local_points,0).tolist(),np.max(local_points,0).tolist()]})
        return {'ok':not errors,'errors':sorted(set(errors)),
                'bounds_m':[np.min(points,0).tolist(),np.max(points,0).tolist()],
                'surface_samples':len(points),'lods':lod_reports}

    def patch(self,g,part,steps):
        u0,v0,u1,v1=part['uv_rect'];rows=[];triangles=[]
        for j in range(steps+1):
            for i in range(steps+1):
                u,v=i/steps,j/steps
                row=sample(g,(u0+(u1-u0)*u,v0+(v1-v0)*v))
                if region_errors(row,part['region']):
                    raise ValueError('Malha do componente cruza região incompatível.')
                lift=.001+(part['relief_mm']/1000-.001)*np.sin(np.pi*u)**.45*np.sin(np.pi*v)**.45
                row['Position']+=row['Normal']*lift;rows.append(row)
        for j in range(steps):
            for i in range(steps):
                a=j*(steps+1)+i;b=a+1;c=a+steps+1;d=c+1
                for tri in ((a,b,d),(a,d,c)):
                    points=np.array([rows[k]['Position'] for k in tri]);normal=sum(rows[k]['Normal'] for k in tri)
                    if np.dot(np.cross(points[1]-points[0],points[2]-points[0]),normal)<0:tri=tri[::-1]
                    triangles.append(tri)
        patch=copy.deepcopy(g);patch.vertex_buffer=np.array(rows,dtype=g.vertex_buffer.dtype)
        patch.index_buffer=np.asarray(triangles,dtype=g.index_buffer.dtype).ravel()
        # The raised surface needs new normals/tangents; native base buffers stay unchanged.
        normals=np.zeros((len(rows),3));tangents=np.zeros((len(rows),3));bitangents=np.zeros((len(rows),3))
        v=patch.vertex_buffer
        for ids in triangles:
            a,b,c=ids;e=v['Position'][b]-v['Position'][a];f=v['Position'][c]-v['Position'][a]
            n=np.cross(e,f);uv1=v['TexCoord0'][b]-v['TexCoord0'][a];uv2=v['TexCoord0'][c]-v['TexCoord0'][a]
            det=uv1[0]*uv2[1]-uv1[1]*uv2[0]
            for index in ids:
                normals[index]+=n
                if abs(det)>1e-9:
                    tangents[index]+=(e*uv2[1]-f*uv1[1])/det
                    bitangents[index]+=(f*uv1[0]-e*uv2[0])/det
        normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-8)
        v['Normal']=normals
        if 'Tangent' in v.dtype.names:
            tangent=tangents-normals*(normals*tangents).sum(1,keepdims=True)
            tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-8)
            v['Tangent'][:,:3]=tangent
            v['Tangent'][:,3]=np.where((np.cross(normals,tangent)*bitangents).sum(1)<0,-1,1)
        return patch

    def build(self,base,job,data):
        source=json.loads((base/'base.json').read_text(encoding='utf-8'))
        asset=try_load_asset(base/source['paths']['model'])
        original=geometry_manifest(asset)
        adapter=data['material'].get('adapter')
        if adapter not in (None,'palette_to_rgb'):
            raise ValueError('Adaptador de material desconhecido.')
        material_changes=[]
        if adapter=='palette_to_rgb':
            replacements={'ped_palette.sps':'ped.sps','ped_default_palette.sps':'ped_default.sps'}
            for drawable in asset.drawables.values():
                for shader in drawable.shader_group.shaders:
                    before=shader.preset_filename
                    if before not in replacements:
                        raise ValueError('O adaptador palette_to_rgb exige shaders de paleta conhecidos.')
                    preset=replacements[before];definition=ShaderManager._shaders[preset]
                    shader.name=f'hash_{jenkhash.hash_string(definition.base_name):08x}'
                    shader.preset_filename=preset
                    shader.parameters=[p for p in shader.parameters if p.name.lower()!='texturesamplerdiffpal']
                    material_changes.append({'from':before,'to':preset})
        materials=material_signature(next(iter(asset.drawables.values())))
        file=Path(source['item']['file'])
        index_pattern=rf"(?<=_){source['item']['index']:03}(?=_|$)"
        model_name=re.sub(index_pattern,'000',file.stem,count=1)
        tex_name=re.sub(index_pattern,'000',Path(source['item']['textureFile']).stem,count=1)
        suffix=data['target']['prefix']+'^'
        for d in asset.drawables.values():
            d.name=model_name+'.#dd'
            diffuse_count=0
            for shader in d.shader_group.shaders:
                for parameter in shader.parameters:
                    if parameter.name.lower()=='diffusesampler':
                        parameter.value=tex_name;diffuse_count+=1
            if not diffuse_count:
                raise ValueError('Sampler difuso nativo não foi resolvido; exportação bloqueada.')
            for lod,models in d.models.items():
                for part in data['components']:
                    g=models[part.get('model',0)].geometries[part.get('geometry',0)]
                    steps=8 if int(lod)==0 else 4
                    models[part.get('model',0)].geometries.append(self.patch(g,part,steps))
        # A single clothing YDD normally contains one drawable; prohibit ambiguous conversion.
        if len(asset.drawables)!=1:
            raise ValueError('YDD com múltiplos drawables requer um adaptador explícito.')
        asset.drawables={model_name:next(iter(asset.drawables.values()))}
        image=Image.open(job/'inputs'/data['material']['albedo_atlas']).convert('RGBA')
        if max(image.size)>self.cfg['limits']['max_texture_size'] or any(x&(x-1) for x in image.size):
            raise ValueError('Atlas deve ter dimensões potência de 2, no máximo 2048.')
        for part in data['components']:
            u0,v0,u1,v1=part['uv_rect'];rect=tuple(round(n*size) for n,size in zip((u0,v0,u1,v1),image.size*2))
            overlay=Image.open(job/'inputs'/part['image']).convert('RGBA')
            if overlay.getextrema()[3][0]==255:
                raise ValueError('Componente precisa de recorte com alpha; fundo de referência não pode ir para a peça.')
            overlay=overlay.resize((rect[2]-rect[0],rect[3]-rect[1]),Image.Resampling.LANCZOS)
            image.alpha_composite(overlay,(rect[0],rect[1]))
        image.save(job/'work'/'albedo_final.png')
        buffer=io.BytesIO();image.save(buffer,format='DDS',pixel_format='DXT5' if image.getextrema()[3][0]<255 else 'DXT1')
        txd=try_load_asset(base/source['paths']['texture'])
        txd.textures={tex_name:EmbeddedTexture(tex_name,*image.size,DataSource.create(buffer.getvalue()))}
        save_asset(asset,TARGETS,job/'exports',suffix+model_name)
        save_asset(txd,TARGETS,job/'exports',suffix+tex_name)
        result=try_load_asset(job/'exports'/(suffix+model_name+'.ydd'))
        d=next(iter(result.drawables.values()));added=0
        if material_signature(d)!=materials:
            raise ValueError('Esqueleto, normal, especular ou parâmetros nativos foram alterados.')
        if any(p.value!=tex_name for s in d.shader_group.shaders for p in s.parameters
               if p.name.lower()=='diffusesampler'):
            raise ValueError('Atlas da variação não foi associado corretamente ao material.')
        for record in original:
            geometry=d.models[record['lod']][record['model']].geometries[record['geometry']]
            if signature(geometry)!=record['signature']:
                raise ValueError('Malha, UV, pesos ou índices originais foram alterados.')
        for lod,models in d.models.items():
            original_count=sum(r['triangles'] for r in original if r['lod']==int(lod))
            count=sum(len(g.index_buffer)//3 for m in models for g in m.geometries)
            if int(lod)==0:added=count-original_count
            for m in models:
                for g in m.geometries:
                    v=g.vertex_buffer
                    if not np.isfinite(v['Position']).all() or not np.isfinite(v['Normal']).all() or not np.isfinite(v['TexCoord0']).all():
                        raise ValueError('Geometria ou UV não finita.')
                    if len(g.index_buffer) and g.index_buffer.max()>=len(v):raise ValueError('Índice fora da malha.')
                    if 'BlendWeights' in v.dtype.names and not (v['BlendWeights'].sum(1)==255).all():raise ValueError('Pesos de pele inválidos.')
        if added>self.cfg['limits']['extra_triangles_high']:
            raise ValueError('Componentes excederam o orçamento de triângulos.')
        return {'original_geometry_unchanged':True,'native_materials_and_skeleton_unchanged':not material_changes,
                'native_normal_specular_and_skeleton_preserved':True,
                'material_adapter':adapter,'shader_changes':material_changes,
                'diffuse_sampler_verified':True,'extra_triangles_high':added,'texture_size':list(image.size),
                'native_files':[suffix+model_name+'.ydd',suffix+tex_name+'.ytd'],
                'lods':[int(lod) for lod in d.models]}
