"""Extract the rig only; save a separate island composition for placement review."""
import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np

O=Path(__file__).resolve().parents[1];R=O.parent
for folder in ['nativo/cache','nativo/fontes','nativo/dados','implantacao']:(O/folder).mkdir(parents=True,exist_ok=True)
ANCHOR=np.array([520.,-1070.,0.]);HEADING=180.
GROUPS={
 'ppe_estrutura':['01_JACKET_E_FUNDACOES','02_CONVESES_E_CIRCULACAO'],
 'ppe_processo':['03_EXTRACAO_E_TORRE','04_TRATAMENTO_E_REFINO','05_TUBULACOES_E_VALVULAS'],
 'ppe_modulos':['06_ALOJAMENTO_E_CONTROLE','07_HELIPONTO'],
 'ppe_equipamentos':['08_GUINDASTE_PRINCIPAL','09_GUINDASTE_APOIO','10_CARGA_BARRIS_E_EMBARQUE','11_SEGURANCA_E_SINALIZACAO']}
def log(*args):print('PETRO_NATIVE:',*args,flush=True)

def info(mat):
    result={'name':mat.name,'color':list(mat.diffuse_color[:3])}
    if mat.use_nodes:
        nodes=mat.node_tree.nodes
        tex=next((n for n in nodes if n.type=='TEX_IMAGE' and n.image),None)
        if tex:
            image=tex.image;data=bytes(image.packed_file.data) if image.packed_file else Path(bpy.path.abspath(image.filepath)).read_bytes()
            name='ppe_tx_'+hashlib.sha256(data).hexdigest()[:14]
            path=O/'nativo/fontes'/(name+'.png');path.write_bytes(data)
            result.update(texture=name,file=str(path),sha256=hashlib.sha256(data).hexdigest())
            result['uv_scale']=[1.,1.]
            if tex.inputs['Vector'].is_linked:
                mapping=tex.inputs['Vector'].links[0].from_node
                if mapping.type!='MAPPING':raise RuntimeError('Unexpected mapping '+mapping.name)
                result['uv_scale']=list(mapping.inputs['Scale'].default_value[:2])
    return result

def mesh_cache(objects,name,lod=0,collision_objects=None,extra_collision=None):
    mats=[];mi={};parts=[[],[],[],[]];cv=[];ct=[]
    dg=bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        if obj.type not in ['MESH','FONT','CURVE'] or obj.hide_render:continue
        dec=None
        if lod and obj.type=='MESH' and len(obj.data.polygons)>20:
            dec=obj.modifiers.new('PETRO export temporary LOD','DECIMATE');dec.ratio=[1.,.58,.28,.12][lod];dec.use_collapse_triangulate=True
            bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
        ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
        if not me.loop_triangles:
            ev.to_mesh_clear()
            if dec:obj.modifiers.remove(dec)
            continue
        nvert=len(me.vertices);nl=len(me.loops)
        co=np.empty(nvert*3,np.float32);me.vertices.foreach_get('co',co);co=co.reshape(-1,3)
        mat=np.array(ev.matrix_world);pos=co@mat[:3,:3].T+mat[:3,3]
        lvi=np.empty(nl,np.int32);me.loops.foreach_get('vertex_index',lvi)
        normals=np.array([n.vector[:] for n in me.corner_normals]);normals=normals@np.linalg.inv(mat[:3,:3]);normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-8)
        uv=np.zeros((nl,2),np.float32)
        if me.uv_layers:me.uv_layers.active.data.foreach_get('uv',uv.ravel())
        for idx,m in enumerate(me.materials):
            tris=[t for t in me.loop_triangles if t.material_index==idx]
            if not tris:continue
            key=m.name
            if key not in mi:mi[key]=len(mats);mats.append(info(m))
            lix=np.array([t.loops for t in tris]).ravel();u=uv[lix].copy();material=mats[mi[key]]
            u*=material.get('uv_scale',[1,1]);u[:,1]=1-u[:,1]
            parts[0].append(pos[lvi[lix]]);parts[1].append(normals[lix]);parts[2].append(u);parts[3].append(np.full(len(lix),mi[key],np.int32))
        ev.to_mesh_clear()
        if dec:obj.modifiers.remove(dec)
    if not lod:
        for obj in (collision_objects or [])+(extra_collision or []):
            ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
            v=np.array([ev.matrix_world@p.co for p in me.vertices],np.float32)
            off=len(cv);cv.extend(v);ct.extend(np.array([t.vertices for t in me.loop_triangles])+off);ev.to_mesh_clear()
    values=dict(position=np.concatenate(parts[0]).astype(np.float32),normal=np.concatenate(parts[1]).astype(np.float32),uv=np.concatenate(parts[2]).astype(np.float32),material=np.concatenate(parts[3]),collision_vertices=np.array(cv,np.float32).reshape(-1,3),collision_triangles=np.array(ct,np.int32).reshape(-1,3))
    suffix='' if not lod else '_LOD'+str(lod)
    np.savez_compressed(O/'nativo/cache'/(name+suffix+'.npz'),**values)
    row=dict(name=name,materials=mats,triangles=len(values['position'])//3,collision_triangles=len(ct),bb_min=values['position'].min(0).tolist(),bb_max=values['position'].max(0).tolist())
    (O/'nativo/cache'/(name+suffix+'.json')).write_text(json.dumps(row,indent=2),encoding='utf8')
    log('CACHE',name,suffix,row['triangles'],len(ct))
    return row

bpy.ops.wm.open_mainfile(filepath=str(O/'plataforma_petroleo.blend'));bpy.context.scene.frame_set(1)
bpy.data.collections['12_COLISAO_PREPARADA'].hide_viewport=False;bpy.context.view_layer.update()
models=[]
for name,groups in GROUPS.items():
    objects=[o for c in groups for o in bpy.data.collections[c].all_objects]
    collision=list(bpy.data.collections['12_COLISAO_PREPARADA'].objects) if name=='ppe_estrutura' else []
    extra=[]
    if name=='ppe_estrutura':
        # The jacket and guardrails also receive their actual geometry collision.
        extra+=list(bpy.data.collections['01_JACKET_E_FUNDACOES'].objects)
        for group in ['02_CONVESES_E_CIRCULACAO','07_HELIPONTO']:
            for obj in bpy.data.collections[group].objects:
                if obj.type!='MESH':continue
                # A temporary mesh extracts only the yellow guardrail polygons.
                faces=[p for p in obj.data.polygons if obj.data.materials[p.material_index].name=='Pintura amarela industrial']
                if not faces:continue
                me=bpy.data.meshes.new('Rail collision temporary');me.from_pydata([v.co[:] for v in obj.data.vertices],[],[p.vertices[:] for p in faces]);me.update()
                temp=bpy.data.objects.new('Rail collision temporary',me);bpy.context.scene.collection.objects.link(temp);temp.matrix_world=obj.matrix_world;extra.append(temp)
    models.append(mesh_cache(objects,name,collision_objects=collision,extra_collision=extra))
    for lod in range(1,4):mesh_cache(objects,name,lod)
    for obj in extra:
        if obj.name.startswith('Rail collision temporary'):bpy.data.objects.remove(obj,do_unlink=True)
(O/'nativo/dados/modelos.json').write_text(json.dumps(models,indent=2),encoding='utf8')

# Choose the coast position against the current island heightfield and quay bounds.
port=R/'teste-ilha/porto_construido';grid=np.load(port/'dados/terreno.npz')['terrain']
stepx=grid[0,1,0]-grid[0,0,0];stepy=grid[1,0,1]-grid[0,0,1]
def seabed(x,y):
    ix=(x-grid[0,0,0])/stepx;iy=(y-grid[0,0,1])/stepy;i,j=int(ix),int(iy);u,v=ix-i,iy-j
    return float((1-u)*(1-v)*grid[j,i,2]+u*(1-v)*grid[j,i+1,2]+(1-u)*v*grid[j+1,i,2]+u*v*grid[j+1,i+1,2])
def world(p):return [float(ANCHOR[0]-p[0]),float(ANCHOR[1]-p[1]),float(p[2])]
all_lo=np.min([m['bb_min'] for m in models],0);all_hi=np.max([m['bb_max'] for m in models],0)
world_lo=np.array(world(all_hi));world_hi=np.array(world(all_lo));world_lo[2]=all_lo[2];world_hi[2]=all_hi[2]
land=grid[grid[:,:,2]>=0];near=land[(land[:,0]>=world_lo[0]-10)&(land[:,0]<=world_hi[0]+10)]
clearance=float(world_lo[1]*-1+near[:,1].min())
assert clearance>70,('Coast clearance',clearance)
footings=[dict(position=world([x,y,-32]),seabed=seabed(*world([x,y,0])[:2])) for x in [-26,-9,9,26] for y in [-18,18]]
assert all(-32<f['seabed']<-2 for f in footings),footings
for row in json.loads((port/'dados/porto.json').read_text()):
    lo,hi=np.array(row['bb_min']),np.array(row['bb_max'])
    assert hi[0]<world_lo[0] or lo[0]>world_hi[0] or hi[1]<world_lo[1] or lo[1]>world_hi[1],row['name']
stations=json.loads((O/'dados/interacoes.json').read_text())['stations']
for row in stations:row['position']=world(row['position'])
placement=dict(anchor=ANCHOR.tolist(),heading=HEADING,sea_level=0.,bb_min=world_lo.tolist(),bb_max=world_hi.tolist(),coast_clearance_m=clearance,footings=footings,stations=stations,source_map=str(port/'ilha_porto_esperanca.blend'),native_gameplay='static platform validation; extraction and crane controls not implemented')
(O/'nativo/dados/implantacao.json').write_text(json.dumps(placement,indent=2),encoding='utf8');log('COAST_PLACEMENT',ANCHOR.tolist(),clearance)

# Do not overwrite the independently edited island. Append to a review copy.
bpy.ops.wm.open_mainfile(filepath=str(port/'ilha_porto_esperanca.blend'));scene=bpy.context.scene
with bpy.data.libraries.load(str(O/'plataforma_petroleo.blend'),link=False) as (src,dst):
    dst.collections=[c for c in src.collections if c!='15_APRESENTACAO']
assembly=bpy.data.collections.new('Plataforma Petro Esperanca | implantada');scene.collection.children.link(assembly)
root=bpy.data.objects.new('PETRO | origem da implantacao',None);assembly.objects.link(root);root.location=ANCHOR;root.rotation_euler[2]=math.pi
for c in dst.collections:
    assembly.children.link(c)
    for obj in c.all_objects:
        if obj.parent is None:obj.parent=root
    c.name='PETRO_'+c.name
    if 'COLISAO' in c.name:c.hide_viewport=True;c.hide_render=True
scene.frame_set(1)
data=bpy.data.cameras.new('Plataforma junto ao porto');cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam)
cam.location=(1130,-1710,440);target=Vector((385,-915,40));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();data.lens=50;data.clip_end=15000
scene.camera=cam;scene['plataforma_implantada']=str(O/'nativo/dados/implantacao.json')
for obj in scene.objects:
    for mod in obj.modifiers:
        if mod.type=='NODES':mod.show_render=False
    if obj.name.startswith('COL_'):obj.hide_render=True
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=6;scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=950;scene.render.resolution_percentage=100
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(O/'implantacao/ilha_com_plataforma.blend'),compress=True)
scene.render.filepath=str(O/'previews/05_Plataforma_na_costa.png');bpy.ops.render.render(write_still=True)
log('ISLAND_REVIEW_SAVED')
