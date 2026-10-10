"""Assemble the existing island, approved ten buildings and the coastal port."""
import bpy,numpy as np,math,json,random,sys,ast
from pathlib import Path
from mathutils import Matrix,Vector
O=Path(__file__).resolve().parents[1];P=O.parent;R=P.parent
sys.path.insert(0,str(O/'scripts'));from cache_blender import extract
# Import only authoring definitions; do not regenerate or overwrite prior assets.
file=P/'porto_esperanca/scripts/criar_porto_blender.py';tree=ast.parse(file.read_text(encoding='utf8'))
nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef))]
ns={'__file__':str(file),'LOTS':[],'ROUTES':[],'SEED':20261009};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(file),'exec'),ns);ns['setup_plan']()
OFFSET=np.array([250.,-850.,0.]);LOTS=ns['LOTS'];ROUTES=ns['ROUTES'];height=ns['height'];rng=random.Random(20261009)
bpy.ops.wm.open_mainfile(filepath=str(P/'teste-ilha.blend'));scene=bpy.context.scene;scene.name='Ilha | Porto Esperanca construido'
grid=np.load(P/'dados/terreno.npz')['terrain'].copy();x=grid[:,:,0]-OFFSET[0];y=grid[:,:,1]-OFFSET[1]
# Keep the runway and the island's northern mountains; feather the new coastline.
dx=np.maximum(np.maximum(-520-x,x-520),0);dy=np.maximum(np.maximum(-235-y,y-795),0)
w=np.clip(1-np.hypot(dx,dy)/110,0,1);w=w*w*(3-2*w)
runway=((grid[:,:,0]>-820)&(grid[:,:,0]<-60)&(grid[:,:,1]>-143)&(grid[:,:,1]<-36));w[runway]=0
original=grid[:,:,2].copy();grid[:,:,2]=original*(1-w)+height(x,y)*w
np.savez_compressed(O/'dados/terreno.npz',terrain=grid)
meta=json.loads((P/'dados/medidas.json').read_text());changed=[]
textures=P/'amostra_natural/texturas';cfg=json.loads((P/'amostra_natural/config.json').read_text())
def col(name):c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
def basic(name,color):return ns['basic'](name,color)
def groundmat(key):
    m=basic('Solo nativo '+key,(.2,.23,.1));m['native_texture']=key;tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(textures/(key+'.dds')),check_existing=True);tx.image.pack();m.node_tree.links.new(tx.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);return m
gm=[groundmat(cfg['layers'][i]['diffuse']) for i in [0,1,3,4]]
def groundcache(name,patch,center,stride):
    g=patch[::stride,::stride];ny,nx=g.shape[:2];j,i=np.meshgrid(np.arange(ny-1),np.arange(nx-1),indexing='ij');q=(j*nx+i).ravel();tris=np.concatenate([np.stack([q,q+1,q+nx+1],1),np.stack([q,q+nx+1,q+nx],1)])
    a=g.reshape(-1,3)[tris];n=np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]);slope=np.linalg.norm(n[:,:2],axis=1)/np.maximum(abs(n[:,2]),.01);n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-8)
    m=np.where(a[:,:,2].mean(1)<6,3,np.where(slope>.60,2,0));v=(a.reshape(-1,3)-center).astype(np.float32);uv=a[:,:,:2].reshape(-1,2)/6;uv[:,1]=1-uv[:,1]
    np.savez_compressed(O/'cache'/f'{name}_{stride}.npz',position=v,normal=np.repeat(n,3,axis=0),uv=uv,material=np.repeat(m,3),weight=np.zeros(len(v)),phase=np.zeros(len(v)),exterior=np.ones(len(v)),collision_vertices=patch.reshape(-1,3),collision_triangles=tris)
    return tris
for tile in meta['tiles']:
    x0,y0,x1,y1=tile['grid_bounds'];patch=grid[y0:y1+1,x0:x1+1];delta=abs(patch[:,:,2]-original[y0:y1+1,x0:x1+1])
    if delta.max()<.001:continue
    name=tile['name'];center=np.array([(patch[0,0,0]+patch[-1,-1,0])/2,(patch[0,0,1]+patch[-1,-1,1])/2,0.])
    for suffix,stride in [('',1),('_MED',2),('_LOW',4),('_VLOW',8)]:
        o=bpy.data.objects[name+suffix];g=patch[::stride,::stride];o.data.vertices.foreach_set('co',g.astype(np.float32).ravel());o.data.update()
        o.data.materials.clear()
        for m in gm:o.data.materials.append(m)
        uv=o.data.uv_layers.active or o.data.uv_layers.new(name='UVMap 0')
        for f in o.data.polygons:
            p=f.center;sl=math.hypot(f.normal.x,f.normal.y)/max(abs(f.normal.z),.01);f.material_index=3 if p.z<6 else 2 if sl>.6 else 0
            for li in f.loop_indices:co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co.x/6,co.y/6)
        groundcache(name,patch,center,stride)
    changed.append(dict(name=name,center=center.tolist(),grid_bounds=tile['grid_bounds'],materials=[dict(texture=m['native_texture'],file=str(textures/(m['native_texture']+'.dds'))) for m in gm]))
    print('ISLAND_GRADED',name,flush=True)
(O/'dados/setores_alterados.json').write_text(json.dumps(changed,indent=2))
# Existing river preview in the reshaped region is replaced with the planned channel.
for o in list(scene.objects):
    if o.type=='MESH' and any(t in o.name.lower() for t in ['rio','lago']):
        # These are presentation surfaces, not the terrain or collision sectors.
        if any('AGUA' in c.name for c in o.users_collection):o.hide_render=True;o.hide_viewport=True
with bpy.data.libraries.load(str(P/'porto_esperanca/porto_esperanca_vegetacao_vento.blend'),link=False) as (src,dst):
    dst.collections=[n for n in src.collections if n in ['02_AGUA_VISUAL','03_CIRCULACAO','04_VEGETACAO','06_PEDRAS']]
imported={}
for c in dst.collections:
    scene.collection.children.link(c);imported[c.name.split('.')[0]]=c
    for o in c.all_objects:o.location+=Vector(OFFSET)
    if c.name.startswith('02_AGUA'):
        for o in c.objects:
            if 'MAR' in o.name:o.hide_render=True
# Camera and preview retain original dense foliage. Game exports use optimized LODs.
buildings=col('10_CASAS_TEXTURIZADAS_E_COMERCIOS');placements=[];library=[]
for path in sorted((P/'estruturas_porto_20261009/modelos').glob('*.blend')):
    with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.collections=['Modelo_completo']
    c=dst.collections[0];c.name='Estrutura '+path.stem;c.use_fake_user=True;library.append(c)
    for o in c.all_objects:
        # Export and preview use the documented open-door pose; opening remains real geometry.
        if o.animation_data and o.animation_data.action:
            for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action,'fcurves') else []:pass
    # Collections are not linked directly, only through instances.
def place(id,x,y,z,heading=0,label=''):
    c=library[id-1];o=bpy.data.objects.new(label or ('Casa '+str(id)),None);o.instance_type='COLLECTION';o.instance_collection=c;buildings.objects.link(o);o.location=(x+OFFSET[0],y+OFFSET[1],z);o.rotation_euler[2]=math.radians(heading)
    placements.append(dict(name=f'pe_estrutura_{id:02}',position=list(o.location),heading=heading,scale=1,label=o.name))
ids=[6,8,7,4,5,6,1,2,3,1,2,3,4,5,1,2,3,1]
for lot,id in zip([s for s in LOTS if s['id'].startswith('U')],ids):
    cx,cy=lot['center'];place(id,cx,cy-6,lot['level']+.20,label=lot['id']+' '+library[id-1].name)
    # Extra small residential frontage on the spacious lots keeps the town scale close to the image.
    if lot['id'] in ['U08','U10','U12','U15','U16','U18']:place(2 if id==1 else 1,cx+12,cy+10,lot['level']+.2,label=lot['id']+' casa de quintal')
for id,x,y,label in [(9,380,302,'Posto da orla'),(10,382,237,'Oficina'),(10,249,55,'Armazem A'),(10,282,55,'Armazem B'),(10,315,55,'Armazem C'),(6,-160,40,'Mercado dos pescadores'),(5,195,124,'Administracao portuaria')]:place(id,x,y,float(height(x,y))+.20,0,label)
(O/'dados/implantacao_casas.json').write_text(json.dumps(placements,indent=2),encoding='utf8')
port=col('11_CAIS_TERMINAL_PRACA_E_PONTE');concrete=basic('Concreto portuario',(.43,.40,.33));red=basic('Telhado terminal ceramico',(.46,.17,.075));wall=basic('Terminal reboco claro',(.76,.72,.57));metal=basic('Guarda e amarracao',(.13,.16,.17));asphalt=basic('Asfalto patio',(.10,.11,.10));yellow=basic('Faixas de circulacao',(.76,.65,.25))
def cube(name,x,y,z,sx,sy,sz,m):
    center=Vector((x+OFFSET[0],y+OFFSET[1],z));o=ns['cube'](name,center,(sx,sy,sz),port,m)
    for v in o.data.vertices:v.co-=center
    o.location=center;return o
# Cais raised above sea with broad pedestrian / loading decks; finger piers and piles.
for x,y,sx,sy in [(-145,-5,110,25),(-10,28,110,22),(90,-5,95,24),(255,-2,180,28)]:
    cube('Cais de concreto',x,y,3.5,sx,sy,1.8,concrete)
    for xx in np.arange(x-sx/2+4,x+sx/2,12):cube('Amarrador',xx,y-sy/2+1,4.65,.65,.65,.5,metal)
for x in [-190,-140,-90,0,80]:
    y=-60 if x else -28;cube('Pier de embarque',x,y,3.65,9,86,1.5,concrete)
    for yy in np.arange(y-40,y+40,15):
        for xx in [x-3.2,x+3.2]:cube('Estaca de pier',xx,yy,.4,.9,.9,7,concrete)
cube('Patio de cargas',280,48,4.48,135,95,.22,asphalt)
cube('Praca de chegada',-8,112,4.72,90,55,.22,concrete)
for i in range(6):cube('Banco praca',-40+i*13,125,5.05,3.5,.65,.55,concrete)
# Open terminal: walls assembled around front doorway, real interior floor and roof.
cube('Terminal piso',-10,65,4.68,45,24,.25,concrete)
cube('Terminal parede fundo',-10,77,6.6,45,.25,4,wall)
for xx in [-32.5,12.5]:cube('Terminal lateral',xx,65,6.6,.25,24,4,wall)
for xx in [-24,4]:cube('Terminal fachada',xx,53,6.6,17,.25,4,wall)
for xx in [-14, -6]:cube('Terminal pilar',xx,53,6.6,.38,.38,4,wall)
cube('Terminal verga',-10,53,8.3,12,.25,.5,wall)
for side in [-1,1]:
    o=cube('Terminal telhado',-10,65+side*6,9.2,48,13,.23,red);o.rotation_euler[0]=-side*math.radians(16)
cube('Balcao terminal',-10,72,5.3,10,1.1,1,concrete)
# Bridge rail/deck adjoining the existing graded road above the new river.
rx=float(ns['riverx'](169));cube('Ponte estrutura',rx,169,5.65,65,17,1,concrete)
for yy in [161.1,176.9]:
    cube('Ponte guarda',rx,yy,6.8,65,.2,.9,concrete)
    for xx in [rx-22,rx+22]:cube('Ponte pilar',xx,yy,2.3,1.8,1.8,7,concrete)
for x in np.arange(-190,270,24):cube('Faixa eixo comercial',x,264,float(height(x,264))+.18,8,.12,.035,yellow)
# Export the circulation and the authored port by spatial sectors, with exact mesh collision.
objs=list(imported['03_CIRCULACAO'].all_objects)+list(port.all_objects);groups={}
for o in objs:
    if o.type!='MESH' or o.hide_render:continue
    pos=np.mean([o.matrix_world@Vector(c) for c in o.bound_box],0);key=(math.floor((pos[0]-OFFSET[0])/160),math.floor((pos[1]-OFFSET[1])/160));groups.setdefault(key,[]).append(o)
props=[]
for i,(key,objs) in enumerate(sorted(groups.items())):
    name=f'pe_porto_{i:02}';row=extract(objs,name);props.append(row)
(O/'dados/porto.json').write_text(json.dumps(props,indent=2))
scene.frame_set(40);scene['referencia']='Porto aprovado pelo usuario em 9/10/2026';scene['casas_lote']='estruturas_porto_20261009';scene['offset_porto']=OFFSET.tolist();scene['colisao_exportada']='terreno, cais, ruas, ponte, edificios e troncos'
camc=col('12_CAMERAS_PORTO');ns['lighting'](scene,camc)
cam=ns['camera']('Porto construido | panorama',(1100,-1650,430),(280,-630,15),camc,lens=43);scene.camera=cam
ns['camera']('Porto construido | bairro',(280,-960,55),(280,-570,10),camc,lens=40)
ns['camera']('Ilha completa',(250,-3650,1900),(0,-100,40),camc,lens=43)
scene.render.resolution_x=1500;scene.render.resolution_y=950;scene.cycles.samples=20
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(O/'ilha_porto_esperanca.blend'),compress=True)
report=dict(offset=OFFSET.tolist(),setores_alterados=len(changed),casas_instancias=len(placements),modelos_edificios=10,area_terra_km2=float((grid[:,:,2]>0).sum()*3.3276552446*4.3882341354/1e6),spawn=dict(x=242,y=-738,z=5.98,heading=180),collision_checked=False,in_game_verified=False)
(O/'dados/construcao.json').write_text(json.dumps(report,indent=2))
for camname,filename in [('Porto construido | panorama','porto_construido.png'),('Ilha completa','ilha_completa.png')]:
    scene.camera=bpy.data.objects[camname];scene.render.filepath=str(O/'previews'/filename);bpy.ops.render.render(write_still=True);print('ISLAND_RENDER',filename,flush=True)
print('ISLAND_CONSTRUCTION_READY',report,flush=True)
