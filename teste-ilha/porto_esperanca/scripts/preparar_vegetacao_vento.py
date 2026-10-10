"""Segundo lote, vento editável e colisões de vegetação; preserva versões anteriores.

PNG originais incorporados sem regravar pixels. Movimento por campos de vértices
e tempo da cena. Colisão somente em madeira/caules; árvores permanecem enraizadas.
O modificador Blender não é exportado como animação GTA: a etapa nativa é separada.
"""
import bpy, numpy as np, json, math, sys, ast, argparse
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
OUT=P/'porto_esperanca_vegetacao_vento.blend'
PRE=P/'previews/vegetacao_vento';PRE.mkdir(parents=True,exist_ok=True)
ap=argparse.ArgumentParser();ap.add_argument('--render',action='store_true');ap.add_argument('--animacao',action='store_true')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])

# Reutilizar somente funções/imports da primeira aplicação; não executar sua rotina.
source=ast.parse((P/'scripts/aplicar_texturas_lote01.py').read_text(encoding='utf8'))
helpers={'P':P,'__file__':str(P/'scripts/aplicar_texturas_lote01.py')}
selected=[n for n in source.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))]
exec(compile(ast.Module(body=selected,type_ignores=[]),'<funcoes_texturas_lote01>','exec'),helpers)
image_file=helpers['image_file'];texture_material=helpers['texture_material']
camera=helpers['camera'];settings=helpers['settings']
def log(*a):print('VEGETACAO_VENTO:',*a,flush=True)

def tube_groups(me,banana=False):
    """Componentes conectados dos tubos originais, incluindo pseudocaules verdes."""
    ids={0,1,3} if banana else {0,1};parents={}
    def find(a):
        parents.setdefault(a,a)
        while parents[a]!=a:parents[a]=parents[parents[a]];a=parents[a]
        return a
    def union(a,b):
        a=find(a);b=find(b)
        if a!=b:parents[b]=a
    polys=[p for p in me.polygons if p.material_index in ids]
    for p in polys:
        for vi in p.vertices:union(p.vertices[0],vi)
    groups={}
    for p in polys:groups.setdefault(find(p.vertices[0]),[]).append(p)
    tubes=[]
    for ps in groups.values():
        caps=[p for p in ps if len(p.vertices)>4]
        if len(caps)!=2:continue # Folhas soltas não são tubos.
        sides=len(caps[0].vertices);vid=sorted({v for p in ps for v in p.vertices})
        if len(vid)%sides:raise RuntimeError('Tubo incompleto '+me.name)
        rings=[vid[i:i+sides] for i in range(0,len(vid),sides)]
        centers=[sum((me.vertices[v].co for v in ring),Vector())/sides for ring in rings]
        radii=[sum((me.vertices[v].co-c).length for v in ring)/sides for ring,c in zip(rings,centers)]
        tubes.append(dict(polys=ps,rings=rings,centers=centers,radii=radii,sides=sides))
    return tubes

def choose_patch(im,wood=False,slender=False,silver=False):
    w,h=im.size;px=np.empty(w*h*4,np.float32);im.pixels.foreach_get(px);px=px.reshape(h,w,4)
    # As imagens recebidas têm muito alpha parcial. Aceitar apenas interiores opacos.
    a=px[:,:,3]>.98;ii=np.pad(a.astype(np.int32),((1,0),(1,0))).cumsum(0).cumsum(1)
    sizes=[(80,160),(48,100),(24,64)] if wood else ([(24,150),(16,90),(10,55)] if slender else [(48,96),(32,64),(20,40)])
    best=None
    for ww,hh in sizes:
        for y in range(int(h*(.04 if wood else .30)),int(h*(.55 if wood else .88))-hh,9):
            for x in range(int(w*.18),int(w*.82)-ww,7):
                if ii[y+hh,x+ww]-ii[y,x+ww]-ii[y+hh,x]+ii[y,x] < ww*hh:continue
                rgb=px[y:y+hh,x:x+ww,:3].mean(axis=(0,1))
                if not wood and not silver and (rgb[1]<rgb[0]*.88 or rgb[1]<rgb[2]*.95):continue
                score=((x+ww/2)/w-.5)**2+((y+hh/2)/h-(.21 if wood else .64))**2
                if not wood:score-=float(rgb.mean() if silver else rgb[1])*.10
                if best is None or score<best[0]:best=(score,x,y,ww,hh)
        if best:break
    if not best:raise RuntimeError('Região UV opaca ausente '+im.name)
    _,x,y,ww,hh=best
    return dict(origem_uv=[x/w,y/h],tamanho_uv=[ww/w,hh/h],retangulo_pixels=[x,y,ww,hh],pixels_origem='baixo_para_cima')

def apply_second(o,wood,leaf):
    old=o.data;kind=o['tipo'];tubes=tube_groups(old,kind=='banana');woodmap={};stem_faces=set();petioles=set()
    for tube in tubes:
        sides=tube['sides'];rings=tube['rings'];cs=tube['centers'];dist=[0.]
        for a,b in zip(cs[:-1],cs[1:]):dist.append(dist[-1]+(b-a).length)
        idx={v:(ri,j) for ri,r in enumerate(rings) for j,v in enumerate(r)}
        for p in tube['polys']:
            coords=[]
            js=[idx[v][1] for v in p.vertices];seam=max(js)-min(js)>sides/2
            for v in p.vertices:
                ri,j=idx[v]
                coords.append(((sides if seam and j==0 else j)/sides,dist[ri]/1.5) if len(p.vertices)==4 else (.5+.4*math.cos(j*math.tau/sides),.5+.4*math.sin(j*math.tau/sides)))
            woodmap[p.index]=coords
            if kind=='banana':stem_faces.add(p.index)
            if kind=='fan' and sides==5:petioles.add(p.index)
    verts=[];faces=[];mis=[];uvs=[];flex=[]
    for p in old.polygons:
        off=len(verts);verts.extend(tuple(old.vertices[v].co) for v in p.vertices);faces.append(tuple(range(off,off+len(p.vertices))))
        mi=13 if p.index in stem_faces else p.material_index;mis.append(mi)
        uvs.append(woodmap.get(p.index,[(0,0),(0,.999),(.999,.999),(.999,0)][:len(p.vertices)]))
        flex.append(mi not in (0,1,9,13) or p.index in petioles)
    tris=[i for i,(f,m) in enumerate(zip(faces,mis)) if len(f)==3 and m in (2,3,4,8,10)]
    patterns=[[(.5,0),(0,.5),(.5,.5)],[(.5,0),(.5,.5),(.999,.5)],[(.5,.999),(.5,.5),(0,.5)],[(.5,.999),(.999,.5),(.5,.5)]]
    for i,fi in enumerate(tris):uvs[fi]=patterns[i%4]
    if len(tris)%4:raise RuntimeError('Folhas triangulares incompletas '+o.name)
    quads=[i for i,(f,m) in enumerate(zip(faces,mis)) if len(f)==4 and m in (2,3,4,8,10)]
    segments=9 if kind=='banana' else 5
    for q,fi in enumerate(quads):
        t0=((q//2)%segments)/segments;t1=(((q//2)%segments)+1)/segments
        u0=.5;u1=0 if q%2==0 else .999
        # Banana: nervura, borda, borda, nervura. Leque: borda, borda, nervura, nervura.
        uvs[fi]=[(u0,t0),(u1,t0),(u1,t1),(u0,t1)] if kind=='banana' else [(u1,t0),(u1,t1),(u0,t1),(u0,t0)]
    me=bpy.data.meshes.new(o.name+'_TEXTURAS_VENTO');me.from_pydata(verts,[],faces);me.update()
    for i,mat in enumerate(old.materials):me.materials.append(wood if i in (0,1) else leaf if i in (2,3,4,8,10) else mat)
    me.materials.append(leaf);me.materials.append(wood)
    me.polygons.foreach_set('material_index',mis);uv=me.uv_layers.new(name='UV_Textura')
    for p,coords in zip(me.polygons,uvs):
        p.use_smooth=True
        for li,xy in zip(p.loop_indices,coords):uv.data[li].uv=xy
    a=me.attributes.new('vento_flexivel','BOOLEAN','FACE');a.data.foreach_set('value',flex)
    for ob in bpy.data.objects:
        if ob.type=='MESH' and ob.data==old:ob.data=me;ob['texturas_lote02']=True
    return me

def roots_for(tubes):
    roots=[]
    for t in tubes:
        cs=t['centers']
        if min(c.z for c in cs)<.10 and cs[-1].z>cs[0].z+.3:roots.append(cs[-1])
    return roots

def wind_attributes(o,tubes):
    me=o.data;kind=o['tipo'];roots=roots_for(tubes);n=len(me.vertices)
    weights=np.zeros(n,np.float32);phase=np.zeros(n,np.float32)
    flexible=me.attributes.get('vento_flexivel')
    tri=[]
    for p in me.polygons:
        leaf=bool(flexible.data[p.index].value) if flexible else p.material_index not in (0,1,9)
        if not leaf:continue
        if kind in ('broad','yucca','ground') and len(p.vertices)==3:tri.append(p);continue
        for vi in p.vertices:
            v=me.vertices[vi].co
            root=min(roots,key=lambda r:(v-r).length) if roots else Vector((0,0,o['altura_referencia_m']*.75))
            d=(v-root).length;r=2.4 if kind=='banana' else 2.5 if kind=='fan' else 3.6
            weights[vi]=min(1.,d/r)**1.3
            # Campo contínuo: vértices duplicados na mesma posição recebem o mesmo deslocamento.
            phase[vi]=v.x*.55+v.y*.73+v.z*.19
    if len(tri)%4:raise RuntimeError('Grupo de folhas com vento incompleto '+o.name)
    for k in range(0,len(tri),4):
        a=me.vertices[tri[k].vertices[0]].co;b=me.vertices[tri[k+2].vertices[0]].co;d=b-a;len2=d.length_squared
        for p in tri[k:k+4]:
            for vi in p.vertices:
                v=me.vertices[vi].co;t=max(0.,min(1.,(v-a).dot(d)/len2)) if len2>1e-9 else 0.
                weights[vi]=t**1.35;phase[vi]=a.x*.73+a.y*.91+a.z*.17
    for name,values in [('vento_peso',weights),('vento_fase',phase)]:
        attr=me.attributes.new(name,'FLOAT','POINT');attr.data.foreach_set('value',values)
    return dict(vertices_fixos=int((weights==0).sum()),vertices_moveis=int((weights>0).sum()),peso_maximo=float(weights.max()))

def wind_nodes():
    g=bpy.data.node_groups.new('Vento vegetacao | raizes fixas e folhas flexiveis','GeometryNodeTree')
    for name,kind,direction in [('Geometry','NodeSocketGeometry','INPUT'),('Geometry','NodeSocketGeometry','OUTPUT'),('Amplitude (m)','NodeSocketFloat','INPUT'),('Fase instancia','NodeSocketFloat','INPUT')]:
        s=g.interface.new_socket(name=name,in_out=direction,socket_type=kind)
        if name=='Amplitude (m)':s.default_value=.16;s.min_value=0;s.max_value=1
    ns=g.nodes;ls=g.links;inp=ns.new('NodeGroupInput');out=ns.new('NodeGroupOutput');pos=ns.new('GeometryNodeSetPosition')
    ls.new(inp.outputs['Geometry'],pos.inputs['Geometry']);ls.new(pos.outputs['Geometry'],out.inputs['Geometry'])
    time=ns.new('GeometryNodeInputSceneTime');weight=ns.new('GeometryNodeInputNamedAttribute');weight.data_type='FLOAT';weight.inputs['Name'].default_value='vento_peso'
    phase=ns.new('GeometryNodeInputNamedAttribute');phase.data_type='FLOAT';phase.inputs['Name'].default_value='vento_fase'
    def m(op,a,b=None):
        node=ns.new('ShaderNodeMath');node.operation=op
        for i,v in enumerate([a,b]):
            if v is None:continue
            if isinstance(v,(int,float)):node.inputs[i].default_value=v
            else:ls.new(v,node.inputs[i])
        return node.outputs[0]
    ph=m('ADD',phase.outputs['Attribute'],inp.outputs['Fase instancia'])
    tx=m('ADD',m('MULTIPLY',time.outputs['Seconds'],1.65),ph)
    ty=m('ADD',m('MULTIPLY',time.outputs['Seconds'],1.22),ph)
    flutter=m('SINE',m('ADD',m('MULTIPLY',time.outputs['Seconds'],6.3),m('MULTIPLY',ph,2.1)))
    x=m('ADD',m('SINE',tx),m('MULTIPLY',flutter,.20));y=m('MULTIPLY',m('COSINE',ty),.55);z=m('MULTIPLY',flutter,.12)
    gust=m('ADD',.78,m('MULTIPLY',m('SINE',m('MULTIPLY',time.outputs['Seconds'],.44)),.22))
    amp=m('MULTIPLY',m('MULTIPLY',inp.outputs['Amplitude (m)'],weight.outputs['Attribute']),gust)
    vec=ns.new('ShaderNodeCombineXYZ')
    for i,v in enumerate([x,y,z]):ls.new(m('MULTIPLY',v,amp),vec.inputs[i])
    ls.new(vec.outputs[0],pos.inputs['Offset'])
    # Organizar visualmente o grafo em colunas.
    for i,node in enumerate(ns):node.location=((i%6)*230,(i//6)*-170)
    g['tecnica']='Deformação de vértices por tempo; não é solver de pano nem animação nativa GTA.'
    return g

def add_wind(o,group,amplitude):
    mod=o.modifiers.new('VENTO | folhas e frondes','NODES');mod.node_group=group
    sockets={s.name:s.identifier for s in group.interface.items_tree if getattr(s,'in_out',None)=='INPUT'}
    values={'Amplitude (m)':amplitude,'Fase instancia':float(o.location.x*.021+o.location.y*.017)}
    for name,value in values.items():
        if bpy.app.version>=(5,2,0):getattr(mod.properties.inputs,sockets[name]).value=value
        else:mod[sockets[name]]=value
    o['vento_amplitude_m']=amplitude;o['folhas_balancam']=True;o['tronco_enraizado']=True

def collision_mesh(key,original,tubes):
    verts=[];faces=[];used=[]
    for t in tubes:
        cs=t['centers'];length=sum((b-a).length for a,b in zip(cs[:-1],cs[1:]))
        main=min(c.z for c in cs)<.10 and max(c.z for c in cs)>.3
        if length<.12 or (max(t['radii'])<.075 and not main):continue
        ids=sorted({v for p in t['polys'] for v in p.vertices});remap={v:len(verts)+i for i,v in enumerate(ids)}
        verts.extend(tuple(original.vertices[v].co) for v in ids);faces.extend(tuple(remap[v] for v in p.vertices) for p in t['polys']);used.append(t)
    if not used:raise RuntimeError('Nenhum caule sólido '+key)
    me=bpy.data.meshes.new('COLISAO_'+key);me.from_pydata(verts,[],faces);me.update()
    me['somente_troncos_caules_raizes']=True;me['folhas_colidem']=False
    return me,used

def link_obj(scene,name,me,pos=(0,0,0)):
    o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);o.location=pos;return o

def passive(o):
    o.hide_set(False);bpy.context.view_layer.objects.active=o;o.select_set(True)
    bpy.ops.rigidbody.object_add();o.rigid_body.type='PASSIVE';o.rigid_body.collision_shape='MESH'
    o.rigid_body.use_margin=True;o.rigid_body.collision_margin=.003;o.select_set(False)
    o.hide_render=True;o.display_type='WIRE'

def demo(models,collisions,group,amps,tube_data):
    s=bpy.data.scenes.new('Fisica e vento');bpy.context.window.scene=s;s.unit_settings.system='METRIC'
    s.world=bpy.data.scenes['Porto Esperanca'].world.copy();s.render.fps=24;s.frame_start=1;s.frame_end=144
    bodymat=bpy.data.materials.new('Bolinhas de teste');bodymat.diffuse_color=(.85,.06,.015,1);bodymat.use_nodes=True
    bodymat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.85,.06,.015,1)
    trials=[]
    for i,key in enumerate(['11_mangueira','12_bananeira','16_palma_azul']):
        x=(i-1)*13;src=bpy.data.objects[key];o=link_obj(s,'DEMO_'+key,src.data,(x,0,0));add_wind(o,group,amps[key])
        col=link_obj(s,'CONTATO_'+key,collisions[key],(x,0,0));passive(col)
        candidates=[t for t in tube_data[key] if min(c.z for c in t['centers'])<.1 and t['centers'][-1].z>.3]
        t=max(candidates,key=lambda t:t['centers'][-1].z);top=t['centers'][-1];radius=min(.10,t['radii'][-1]*.55)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=radius,location=(x+top.x,top.y,top.z+.65))
        ball=bpy.context.object;ball.name='BOLA_CONTATO_'+key;ball.data.materials.append(bodymat)
        bpy.ops.rigidbody.object_add();ball.rigid_body.mass=.2;ball.rigid_body.collision_shape='SPHERE';ball.rigid_body.restitution=0;ball.rigid_body.friction=.8;ball.rigid_body.collision_margin=.001
        # Controle cai ao lado sem obstáculo: evidencia contato antes de tocar o chão.
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=radius,location=(x+top.x+5,top.y,top.z+.65))
        ctrl=bpy.context.object;ctrl.name='BOLA_CONTROLE_'+key;ctrl.data.materials.append(bodymat);bpy.ops.rigidbody.object_add();ctrl.rigid_body.collision_shape='SPHERE';ctrl.rigid_body.mass=.2
        trials.append(dict(modelo=key,bola=ball.name,controle=ctrl.name,topo_caule_m=top.z,raio_bola_m=radius))
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.20));floor=bpy.context.object;floor.name='CHAO_TESTE_FISICA';floor.scale=(80,50,.4);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    floor.data.materials.append(bpy.data.materials['Reserva praca']);passive(floor);floor.hide_render=False;floor.display_type='TEXTURED'
    s.rigidbody_world.substeps_per_frame=8;s.rigidbody_world.solver_iterations=20;s.rigidbody_world.point_cache.frame_end=144
    ld=bpy.data.lights.new('Sol vento','SUN');ld.energy=2;ld.angle=.14;sun=link_obj(s,'Sol vento',ld);sun.rotation_euler=(.5,-.3,-.6)
    s.camera=camera(s,'CAM_VENTO',(24,-49,20),(0,0,5),ortho=42);settings(s,1280,720)
    s['teste_contato']=json.dumps(trials);s['instrucoes']='Reproduzir quadros 1 a 144. Vento em folhas/frondes; troncos estáticos e colisores passivos. Bolas vermelhas testam caules.'
    return s,trials

if not args.render and not args.animacao:
    bpy.ops.wm.open_mainfile(filepath=str(P/'porto_esperanca_texturas_lote01.blend'))
    base=json.loads((P/'dados/implantacao.json').read_text(encoding='utf8'));keys=[m['id'] for m in base['modelos'][:18]]
    # Fontes conectadas anteriores à duplicação de vértices da etapa UV.
    with bpy.data.libraries.load(str(P/'porto_esperanca.blend'),link=False) as (source,dest):dest.meshes=list(keys)
    originals=dict(zip(keys,dest.meshes));tube_data={key:tube_groups(originals[key],key=='12_bananeira') for key in keys}
    entries=json.loads((P/'texturas/folhas/lote02/manifesto.json').read_text(encoding='utf8'))['arquivos']
    trunks={r['id']:r for r in json.loads((P/'texturas/troncos/manifesto.json').read_text(encoding='utf8'))['arquivos']}
    applied=[]
    for e in entries:
        key=e['modelo_inicial'];o=bpy.data.objects[key];wi=image_file(P/trunks[e['tronco']]['arquivo']);li=image_file(P/e['arquivo'])
        wc=choose_patch(wi,wood=True);lc=choose_patch(li,slender=o['tipo'] in ('banana','fan','yucca'),silver=key=='16_palma_azul')
        wm=texture_material('Casca imagem | '+key,wi,wc);lm=texture_material('Folhagem imagem | '+key,li,lc,True)
        if key=='12_bananeira':
            # Pseudocaule vivo: retirar o escurecimento marrom usado na casca lenhosa.
            tint=next(n for n in wm.node_tree.nodes if n.type=='MIX_RGB');tint.inputs[2].default_value=(1,1,1,1)
        me=apply_second(o,wm,lm)
        applied.append(dict(id=key,poligonos=len(me.polygons),vertices=len(me.vertices),tronco=trunks[e['tronco']]['arquivo'],folhas=e['arquivo'],regiao_casca=wc,regiao_foliolo=lc,nota_associacao=e['nota']))
        log('LOTE02_APLICADO',key)
    group=wind_nodes();amps={};winds=[];collisions={};colls=[]
    templates=bpy.data.collections.new('10_COLISAO_VEGETACAO_MODELOS');bpy.data.scenes['Porto Esperanca'].collection.children.link(templates);templates.hide_render=True
    for key in keys:
        o=bpy.data.objects[key];kind=o['tipo'];amp=.28 if kind=='banana' else .24 if kind in ('palm','fan') else .075 if kind=='yucca' else .10
        if key in ('14_arbusto_costeiro','18_cerca_viva'):amp=.06
        amps[key]=amp;wr=wind_attributes(o,tube_data[key]);wr.update(id=key,amplitude_m=amp);winds.append(wr)
        me,used=collision_mesh(key,originals[key],tube_data[key]);collisions[key]=me
        co=bpy.data.objects.new('COL_'+key,me);templates.objects.link(co);co.display_type='WIRE';co.hide_render=True;co['modelo']=key;co['folhas_colidem']=False;co['tipo_fisica']='estatica; tronco, caules e raízes principais';o['colisor_modelo']=co.name
        raw=P/'dados/colisoes_vegetacao';raw.mkdir(exist_ok=True)
        me.calc_loop_triangles()
        np.savez_compressed(raw/(key+'.npz'),vertices=np.array([v.co[:] for v in me.vertices],np.float32),triangulos=np.array([t.vertices[:] for t in me.loop_triangles],np.int32))
        colls.append(dict(id=key,vertices=len(me.vertices),poligonos=len(me.polygons),tubos=len(used),objeto=co.name,folhas_colidem=False))
    # Todos os usuários das dezoito malhas recebem o mesmo grafo editável com fase por posição.
    for key in keys:
        me=bpy.data.objects[key].data
        for o in list(bpy.data.objects):
            if o.type=='MESH' and o.data==me:add_wind(o,group,amps[key])
    porto=bpy.data.scenes['Porto Esperanca'];bpy.context.window.scene=porto
    instances=bpy.data.collections.new('11_COLISAO_VEGETACAO_IMPLANTACAO');porto.collection.children.link(instances);instances.hide_render=True;instances.hide_viewport=True
    count=0
    for o in list(bpy.data.collections['04_VEGETACAO'].objects):
        key=o.get('modelo')
        if key not in collisions:continue
        c=bpy.data.objects.new('COL_INST_'+o.name,collisions[key]);instances.objects.link(c);c.matrix_world=o.matrix_world.copy();c.display_type='WIRE';c.hide_render=True;c['modelo']=key;c['origem_visual']=o.name;count+=1
    # Mostrar biblioteca de colisores apenas ao ativar manualmente a coleção.
    templates.hide_viewport=True
    # Catálogo novo: reaproveita função de apresentação com oito espécies em duas fileiras.
    gallery=helpers['gallery']([e['modelo_inicial'] for e in entries]);gallery.name='Amostra texturas lote02'
    for o in gallery.objects:
        if o.name.startswith('AMOSTRA_'):
            key=o.name.replace('AMOSTRA_','').split('.')[0]
            if key in amps:add_wind(o,group,amps[key])
    ds,trials=demo(keys,collisions,group,amps,tube_data)
    for original in originals.values():
        if original.users==0:bpy.data.meshes.remove(original)
    porto['revisao_texturas']='porto-20261009-vegetacao-vento-1';porto['exportacao_fivem']=False
    porto['vento']='18 modelos com deformação editável; caules fixos';porto['colisoes_vegetacao']=count
    bpy.context.window.scene=ds;ds.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    report=dict(revisao=porto['revisao_texturas'],arquivo=OUT.name,modelos_lote02=applied,modelos_texturizados_total=18,vento=winds,colisoes=colls,colisores_implantados=count,teste_contato=trials,instalado_fivem=False,vento_nativo_validado=False,imagens_alteradas=False,limites=['Vento Blender é deformação visual, não solver de pano.','Colisores implantados são malhas estáticas de preparação; cena Fisica e vento contém corpos rígidos passivos e bolas ativas.','Conversão para shaders/canais nativos e colisão GTA ocorre em etapa separada; não presumir que modificadores Blender funcionem no FiveM.','Seis espécies adicionais do projeto permanecem com materiais procedurais anteriores.'])
    (P/'dados/preparacao_vegetacao_vento.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');log('SALVO',OUT.name,'COLISORES',count)
else:
    bpy.ops.wm.open_mainfile(filepath=str(OUT));ds=bpy.data.scenes['Fisica e vento']
    if args.render:
        for sn,fn in [('Amostra texturas lote02','catalogo_lote02.png'),('Fisica e vento','vento_e_contato.png')]:
            s=bpy.data.scenes[sn];bpy.context.window.scene=s;s.frame_set(1);settings(s,1900 if 'Amostra' in sn else 1280,1000 if 'Amostra' in sn else 720)
            s.render.filepath=str(PRE/fn);bpy.ops.render.render(write_still=True);log('PREVIA',fn)
    if args.animacao:
        bpy.context.window.scene=ds;ds.render.engine='BLENDER_EEVEE';ds.eevee.taa_render_samples=24
        ds.render.resolution_x=960;ds.render.resolution_y=540;ds.render.resolution_percentage=100
        # Quadros sequenciais garantem a avaliação da cena física. Imagens são renders, não edições dos PNG recebidos.
        for f in range(1,97):
            ds.frame_set(f)
            if (f-1)%3==0:
                ds.render.filepath=str(PRE/'animacao'/f'vento_{(f-1)//3:03d}.png');bpy.ops.render.render(write_still=True)
                log('QUADRO',f)
