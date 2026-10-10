"""Aplicar imagens originais como materiais e folhagem volumétrica no Blender.

Não altera os PNG: regiões de casca são selecionadas por coordenadas UV.
As imagens das copas fornecem cor e detalhe às folhas modeladas em 3D.
Salva uma versão separada; não regenera o terreno nem instala recursos FiveM.
"""
import bpy, json, math, random, argparse, sys
from pathlib import Path
from mathutils import Vector
import numpy as np

P = Path(__file__).resolve().parents[1]
OUT = P / 'porto_esperanca_texturas_lote01.blend'
PRE = P / 'previews' / 'texturas_lote01'
PRE.mkdir(parents=True, exist_ok=True)
ap = argparse.ArgumentParser()
ap.add_argument('--somente-render', action='store_true')
ap.add_argument('--camera', default='')
ap.add_argument('--sem-render', action='store_true')
args = ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])

def log(*parts): print('TEXTURAS_LOTE01:', *parts, flush=True)

def image_file(path):
    im = bpy.data.images.load(str(path), check_existing=True)
    im.colorspace_settings.name = 'sRGB'
    im.alpha_mode = 'STRAIGHT'
    im.pack()
    return im

def opaque_patch(im, wood=True, palm=False):
    """Selecionar região opaca na imagem, sem recortar ou regravar pixels."""
    w, h = im.size
    px = np.empty(w*h*4, dtype=np.float32)
    im.pixels.foreach_get(px)
    pixels=px.reshape(h,w,4)
    a = pixels[:,:,3] > .98
    # Blender armazena pixels de baixo para cima.
    integral = np.pad(a.astype(np.int32), ((1,0),(1,0))).cumsum(0).cumsum(1)
    widths = [80,64,48] if wood else ([28,20,14] if palm else [48,36,24])
    heights = [200,160,128] if wood else ([180,128,90] if palm else [96,80,64])
    target = (.5,.23) if wood else (.5,.65)
    best = None
    for ww,hh in zip(widths,heights):
        for y in range(int(h*(.08 if wood else .40)),int(h*(.42 if wood else .83))-hh,12):
            for x in range(int(w*.25),int(w*.75)-ww,8):
                total = integral[y+hh,x+ww]-integral[y,x+ww]-integral[y+hh,x]+integral[y,x]
                fraction = total/(ww*hh)
                if fraction < .999: continue
                distance = ((x+ww/2)/w-target[0])**2 + ((y+hh/2)/h-target[1])**2
                score = distance + (80-ww)*.0003
                if not wood:
                    rgb=pixels[y:y+hh,x:x+ww,:3].mean(axis=(0,1))
                    if rgb[1]<rgb[0]*.92 or rgb[1]<rgb[2]*1.02:continue
                    score-=float(rgb[1])*.10
                if best is None or score < best[0]:best=(score,x,y,ww,hh)
        if best is not None:break
    if best is None:raise RuntimeError('Não foi encontrada região opaca: '+im.name)
    _,x,y,ww,hh=best
    return dict(origem_uv=[x/w,y/h],tamanho_uv=[ww/w,hh/h],retangulo_pixels=[x,y,ww,hh],pixels_origem='baixo_para_cima')

def texture_material(name, im, crop=None, foliage=False):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputMaterial');out.location=(650,0)
    b=n.new('ShaderNodeBsdfPrincipled');b.location=(200,80)
    b.inputs['Roughness'].default_value=.85 if not foliage else .78
    b.inputs['Specular IOR Level'].default_value=.20
    if foliage:b.inputs['Subsurface Weight'].default_value=.025
    uv=n.new('ShaderNodeUVMap');uv.uv_map='UV_Textura';uv.location=(-950,0)
    vector=uv.outputs['UV']
    if crop:
        fract=n.new('ShaderNodeVectorMath');fract.operation='FRACTION';fract.location=(-770,0);l.new(vector,fract.inputs[0])
        scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.location=(-580,0)
        scale.inputs[1].default_value=(*crop['tamanho_uv'],1);l.new(fract.outputs[0],scale.inputs[0])
        add=n.new('ShaderNodeVectorMath');add.operation='ADD';add.location=(-390,0)
        add.inputs[1].default_value=(*crop['origem_uv'],0);l.new(scale.outputs[0],add.inputs[0]);vector=add.outputs[0]
    tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='CLIP';tex.interpolation='Linear';tex.location=(-180,100)
    l.new(vector,tex.inputs['Vector'])
    if not foliage:
        tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1
        tint.inputs[2].default_value=(.80,.71,.58,1);tint.location=(0,170)
        l.new(tex.outputs['Color'],tint.inputs[1]);l.new(tint.outputs[0],b.inputs['Base Color'])
    else:l.new(tex.outputs['Color'],b.inputs['Base Color'])
    if not foliage:
        bump=n.new('ShaderNodeBump');bump.location=(10,-180);bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.014
        l.new(tex.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs['Normal'],b.inputs['Normal'])
    if foliage and crop is None:
        transparent=n.new('ShaderNodeBsdfTransparent');transparent.location=(200,-170)
        mix=n.new('ShaderNodeMixShader');mix.location=(440,0)
        l.new(tex.outputs['Alpha'],mix.inputs[0]);l.new(transparent.outputs[0],mix.inputs[1]);l.new(b.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0])
    else:l.new(b.outputs[0],out.inputs[0])
    m.diffuse_color=(.22,.32,.08,1) if foliage else (.28,.19,.10,1)
    m['imagem_original']=str(Path(bpy.path.abspath(im.filepath)).relative_to(P))
    m['pixels_alterados']=False;m['duas_faces']=foliage
    if crop:m['regiao_uv']=json.dumps(crop)
    return m

def woody_components(me):
    parents={}
    def find(x):
        parents.setdefault(x,x)
        while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
        return x
    def union(a,b):
        a=find(a);b=find(b)
        if a!=b:parents[b]=a
    polys=[p for p in me.polygons if p.material_index in (0,1)]
    for p in polys:
        for vi in p.vertices:union(p.vertices[0],vi)
    groups={}
    for p in polys:groups.setdefault(find(p.vertices[0]),[]).append(p)
    return list(groups.values())

def wood_uv(me):
    uv={};centers=[]
    for group in woody_components(me):
        caps=[p for p in group if len(p.vertices)>4]
        if not caps:raise RuntimeError('Tubo sem tampa reconhecível')
        sides=len(caps[0].vertices);ids=sorted({vi for p in group for vi in p.vertices})
        if len(ids)%sides:raise RuntimeError('Topologia de tubo inesperada')
        rings=[ids[i:i+sides] for i in range(0,len(ids),sides)]
        cs=[sum((me.vertices[i].co for i in ring),Vector())/sides for ring in rings]
        lengths=[0.0]
        for a,b in zip(cs[:-1],cs[1:]):lengths.append(lengths[-1]+(b-a).length)
        vi_pos={vi:(ring,j) for ring,vs in enumerate(rings) for j,vi in enumerate(vs)}
        for p in group:
            coords=[]
            if len(p.vertices)==4:
                js=[vi_pos[i][1] for i in p.vertices];seam=max(js)-min(js)>sides/2
                for vi in p.vertices:
                    ri,j=vi_pos[vi];u=(sides if seam and j==0 else j)/sides
                    coords.append((u,lengths[ri]/1.5))
            else:
                for vi in p.vertices:
                    _,j=vi_pos[vi];a=math.tau*j/sides;coords.append((.5+.45*math.cos(a),.5+.45*math.sin(a)))
            uv[p.index]=coords
        if sides==6 and len(rings)==3 and cs[-1].z>cs[0].z+.5:
            centers.append(cs[-1])
    return uv,centers

def update_model(src,wood_mat,leaf_mat,foliage_image):
    old=src.data;woodmap,centers=wood_uv(old)
    verts=[];faces=[];materials=[];face_uv=[]
    palm=src.get('tipo')=='palm'
    for p in old.polygons:
        if palm and p.material_index not in (0,1,9):continue
        off=len(verts);verts.extend([tuple(old.vertices[i].co) for i in p.vertices]);faces.append(tuple(range(off,off+len(p.vertices))));materials.append(p.material_index)
        face_uv.append(woodmap.get(p.index,[(0,0),(0,.999),(.999,.999),(.999,0)][:len(p.vertices)]))
    if palm:
        # Folíolos curvos e sobrepostos, com a imagem seguindo seu comprimento.
        trunk_groups=woody_components(old)
        main=max(trunk_groups,key=lambda ps:max(old.vertices[i].co.z for p in ps for i in p.vertices)-min(old.vertices[i].co.z for p in ps for i in p.vertices))
        ids=sorted({vi for p in main for vi in p.vertices})
        root=sum((old.vertices[i].co for i in ids[-10:]),Vector())/10
        rng=random.Random(20261009+sum(map(ord,src.name)))
        radius=3.6 if src.name=='01_coqueiro' else 3.0
        def add_face(points,coords,mi=12):
            a=len(verts);verts.extend(map(tuple,points));faces.append(tuple(range(a,a+len(points))));materials.append(mi);face_uv.append(coords)
        for fi in range(22):
            angle=fi*math.tau/22+rng.uniform(-.08,.08)
            d=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-d.y,d.x,0))
            length=radius*rng.uniform(.90,1.18);arch=.46 if fi%3 else .68;drop=.38 if fi%3 else .08
            def stem(t):return root+d*length*t+Vector((0,0,length*(arch*math.sin(math.pi*t)-drop*t)))
            for j in range(12):
                c0=stem(j/12);c1=stem((j+1)/12);rr=.028*(1-j/14)
                for k in range(5):
                    aa=k*math.tau/5;bb=(k+1)*math.tau/5
                    u0=side*math.cos(aa)+Vector((0,0,math.sin(aa)));u1=side*math.cos(bb)+Vector((0,0,math.sin(bb)))
                    add_face([c0+u0*rr,c0+u1*rr,c1+u1*rr*.91,c1+u0*rr*.91],[(0,0),(.999,0),(.999,.999),(0,.999)])
            for j in range(1,49):
                t=j/50;base=stem(t);blade_length=radius*.46*math.sin(math.pi*t)**.65
                for sign in (-1,1):
                    direction=(side*sign+d*.22+Vector((0,0,-.28))).normalized()
                    across=direction.cross(Vector((0,0,1))).normalized()
                    for seg in range(4):
                        t0=seg/4;t1=(seg+1)/4
                        c0=base+direction*blade_length*t0+Vector((0,0,-.14*blade_length*t0*t0))
                        c1=base+direction*blade_length*t1+Vector((0,0,-.14*blade_length*t1*t1))
                        w0=.085*math.sin(math.pi*t0)**.6;w1=.085*math.sin(math.pi*t1)**.6
                        for ss in (-1,1):
                            off=Vector((0,0,.018))
                            add_face([c0+off,c0+across*w0*ss,c1+across*w1*ss,c1+off],[(.5,t0),(0 if ss<0 else .999,t0),(0 if ss<0 else .999,t1),(.5,t1)])
    else:
        # Conservar folhas e flores 3D. Cada folha possui UV independente.
        tri_indices=[i for i,(f,mi) in enumerate(zip(faces,materials)) if len(f)==3 and mi in (2,3,4,8,10)]
        patterns=[[(.5,0),(0,.5),(.5,.5)],[(.5,0),(.5,.5),(.999,.5)],[(.5,.999),(.5,.5),(0,.5)],[(.5,.999),(.999,.5),(.5,.5)]]
        if len(tri_indices)%4:raise RuntimeError('Folhas incompletas: '+src.name)
        for i,idx in enumerate(tri_indices):
            flip=(i//4)%2
            face_uv[idx]=[(1-u if flip else u,v) for u,v in patterns[i%4]]
    me=bpy.data.meshes.new(src.name+'_TEXTURAS_LOTE01');me.from_pydata(verts,[],faces);me.update()
    for mi,m in enumerate(old.materials):
        me.materials.append(wood_mat if mi in (0,1) else (leaf_mat if mi in (2,3,4,8,10) else m))
    me.materials.append(leaf_mat)
    me.polygons.foreach_set('material_index',materials)
    uv=me.uv_layers.new(name='UV_Textura')
    for p,coords in zip(me.polygons,face_uv):
        p.use_smooth=True
        for li,xy in zip(p.loop_indices,coords):uv.data[li].uv=xy
    users=[o for o in bpy.data.objects if o.type=='MESH' and o.data==old]
    for o in users:o.data=me;o['texturas_lote01']=True
    src['folhagem_tecnica']='22_frondes_com_foliolos_curvos_3d_texturizados' if palm else 'folhas_3d_com_uv_individual_e_flores_3d_preservadas'
    return dict(id=src.name,vertices=len(verts),poligonos=len(faces),usuarios_vinculados=len(users),grupos_copa=len(centers) if not palm else None,folhagem_tecnica=src['folhagem_tecnica'])

def camera(scene,name,pos,target,ortho=None,lens=48):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.clip_end=15000;d.lens=lens
    if ortho:d.type='ORTHO';d.ortho_scale=ortho
    return o

def settings(s,x=1600,y=1000):
    s.render.engine='CYCLES';s.cycles.samples=40;s.cycles.use_denoising=True;s.cycles.transparent_max_bounces=24
    s.render.resolution_x=x;s.render.resolution_y=y;s.render.resolution_percentage=100
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
    try:
        p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='OPTIX';p.get_devices()
        for dev in p.devices:dev.use=dev.type=='OPTIX'
        if any(dev.use for dev in p.devices):s.cycles.device='GPU'
    except Exception as e:log('GPU',str(e))

def gallery(keys):
    s=bpy.data.scenes.new('Amostra texturas lote01');s.unit_settings.system='METRIC';s.world=bpy.data.scenes['Porto Esperanca'].world.copy()
    for i,key in enumerate(keys):
        src=bpy.data.objects[key];o=bpy.data.objects.new('AMOSTRA_'+key,src.data);s.collection.objects.link(o)
        x=(i%5-2)*23;z=(1-i//5)*21;o.location=(x,0,z+1.3)
        # Pequena base de apresentação, separada dos objetos das árvores.
        bpy.ops.mesh.primitive_cube_add(size=1)
        base=bpy.context.object
        for c in list(base.users_collection):c.objects.unlink(base)
        s.collection.objects.link(base);base.name='BASE_AMOSTRA_'+key;base.location=(x,0,z+.5);base.scale=(15,12,1)
        if 'Asfalto' in bpy.data.materials:base.data.materials.append(bpy.data.materials['Asfalto'])
        td=bpy.data.curves.new('Nome '+key,'FONT');td.body=src['nome_referencia'];td.align_x='CENTER';td.size=.8
        t=bpy.data.objects.new('ROTULO_'+key,td);s.collection.objects.link(t);t.location=(x,-6,z-.6);t.rotation_euler=(math.pi/2,0,0)
        td.materials.append(bpy.data.materials['Rotulo catalogo'])
    ld=bpy.data.lights.new('Sol amostra','SUN');ld.energy=2.0;ld.angle=.13
    sun=bpy.data.objects.new('Sol amostra',ld);s.collection.objects.link(sun);sun.rotation_euler=(.6,-.3,-.5)
    s.camera=camera(s,'CAM_AMOSTRA_LOTE01',(0,-155,46),(0,0,19),ortho=116)
    settings(s,1900,1000);s['fase']='Primeira aplicação das imagens fornecidas; validação visual pendente'
    return s

def detail_scene():
    s=bpy.data.scenes.new('Detalhe arvore texturizada');s.unit_settings.system='METRIC'
    s.world=bpy.data.scenes['Porto Esperanca'].world.copy()
    src=bpy.data.objects['03_caneleira'];o=bpy.data.objects.new('ARVORE_DETALHE',src.data);s.collection.objects.link(o)
    bpy.ops.mesh.primitive_plane_add(size=200)
    ground=bpy.context.object
    for c in list(ground.users_collection):c.objects.unlink(ground)
    s.collection.objects.link(ground);ground.name='CHAO_AMOSTRA';ground.data.materials.append(bpy.data.materials['Reserva praca'])
    ld=bpy.data.lights.new('Sol detalhe','SUN');ld.energy=2;ld.angle=.12
    sun=bpy.data.objects.new('Sol detalhe',ld);s.collection.objects.link(sun);sun.rotation_euler=(.52,-.32,-.6)
    s.camera=camera(s,'DETALHE_CASCA_FOLHAS',(18,-29,13),(0,0,6.7),lens=52)
    camera(s,'DETALHE_OUTRO_ANGULO',(-24,-15,10),(0,0,7),lens=52)
    settings(s)
    return s

if args.somente_render:
    bpy.ops.wm.open_mainfile(filepath=str(OUT))
else:
    bpy.ops.wm.open_mainfile(filepath=str(P/'porto_esperanca.blend'))
    entries=json.loads((P/'texturas/folhas/lote01/manifesto.json').read_text(encoding='utf8'))['arquivos']
    trunk_data=json.loads((P/'texturas/troncos/manifesto.json').read_text(encoding='utf8'))
    trunks={r['id']:r for r in trunk_data['arquivos']}
    results=[]
    for entry in entries:
        key=entry['modelo_inicial'];src=bpy.data.objects[key];t=trunks[entry['tronco']]
        woodim=image_file(P/t['arquivo']);leafim=image_file(P/entry['arquivo'])
        woodcrop=opaque_patch(woodim,True)
        leafcrop=opaque_patch(leafim,False,palm=src.get('tipo')=='palm')
        woodmat=texture_material('Casca imagem | '+key,woodim,woodcrop)
        leafmat=texture_material('Folhagem imagem | '+key,leafim,leafcrop,True)
        result=update_model(src,woodmat,leafmat,leafim)
        result.update(tronco=t['arquivo'],folhas=entry['arquivo'],regiao_casca=woodcrop,regiao_foliolo=leafcrop,associacao='inicial_por_aparencia_a_validar')
        results.append(result);log('MODELO_APLICADO',key,len(src.data.polygons))
    gallery([r['id'] for r in results])
    porto=bpy.data.scenes['Porto Esperanca'];settings(porto)
    detail_scene()
    porto['revisao_texturas']='porto-20261009-texturas-lote01-1';porto['exportacao_fivem']=False
    bpy.context.window.scene=porto;porto.camera=bpy.data.objects['VISTA_GERAL']
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    report=dict(revisao=porto['revisao_texturas'],arquivo=OUT.name,modelos=results,imagens_originais_packed=20,imagens_alteradas=False,instalado_fivem=False,edificios_adicionados=0,coordenadas_preservadas=True,tecnica='Troncos e galhos 3D com imagem de casca via UV. Folhas e flores 3D preservadas nas oito árvores de copa; materiais usam regiões de folhagem por UV individual. Palmeiras com 22 frondes e folíolos curvos geométricos texturizados. PNG originais intactos.',limitacoes=['Associações iniciais entre imagens e espécies precisam de validação visual.','As imagens de copas completas foram usadas como fontes de cor/detalhe por UV; as folhas continuam malhas autorais e não cópias individuais das folhas da fotografia.','Iluminação e perspectiva das referências estão presentes nas imagens.','Não inclui LOD, shaders GTA, colisões de vegetação ou instalação no FiveM.'])
    (P/'dados/aplicacao_texturas_lote01.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    log('ARQUIVO_SALVO',OUT.name)

if not args.sem_render:
    jobs=[('Amostra texturas lote01','CAM_AMOSTRA_LOTE01','catalogo_texturas.png'),('Detalhe arvore texturizada','DETALHE_CASCA_FOLHAS','arvore_sombra_detalhe.png'),('Detalhe arvore texturizada','DETALHE_OUTRO_ANGULO','arvore_sombra_outro_angulo.png'),('Porto Esperanca','VISTA_PRACA','porto_texturas.png')]
    for sn,cn,fn in jobs:
        if args.camera and args.camera!=cn:continue
        s=bpy.data.scenes[sn];bpy.context.window.scene=s;settings(s,1900 if sn.startswith('Amostra') else 1600,1000)
        s.camera=bpy.data.objects[cn];s.render.filepath=str(PRE/fn);log('RENDER',fn)
        bpy.ops.render.render(write_still=True)
    log('PREVIAS_CONCLUIDAS')
