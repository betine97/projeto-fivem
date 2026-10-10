"""Read the approved Blender assets into native-ready meshes. Originals untouched."""
import bpy,bmesh,numpy as np,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
O=Path(__file__).resolve().parents[1];P=O.parent;R=P.parent
for d in ['cache','fontes','dados']:(O/d).mkdir(exist_ok=True)
BAKED_FILE=O/'dados/materiais_baked.json'
BAKED=json.loads(BAKED_FILE.read_text(encoding='utf8')) if BAKED_FILE.exists() else {}
ASSET_NAME=''

def image_info(im):
    data=bytes(im.packed_file.data) if im.packed_file else Path(bpy.path.abspath(im.filepath)).read_bytes()
    ext=Path(im.filepath).suffix or '.png';name='pe_tex_'+hashlib.sha256(data).hexdigest()[:14]
    p=O/'fontes'/(name+ext);p.write_bytes(data)
    return name,str(p)

def material_info(m):
    if not m or not m.use_nodes:return dict(color=list(m.diffuse_color[:3]) if m else [.5,.5,.5])
    bs=m.node_tree.nodes.get('Principled BSDF') or next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    # Follow the BSDF color branch: a normal/roughness image can precede albedo in node order.
    def images(socket,seen=None):
        seen=set() if seen is None else seen
        result=[]
        for link in socket.links:
            n=link.from_node
            if n.as_pointer() in seen:continue
            seen.add(n.as_pointer())
            if n.type=='TEX_IMAGE' and n.image:result.append(n)
            else:
                for s in n.inputs:
                    if s.is_linked:result.extend(images(s,seen))
        return result
    tex=images(bs.inputs['Base Color']) if bs else []
    result=dict(name=m.name,color=list(bs.inputs['Base Color'].default_value[:3]) if bs else list(m.diffuse_color[:3]),roughness=float(bs.inputs['Roughness'].default_value) if bs else .8,metallic=float(bs.inputs['Metallic'].default_value) if bs else 0,transmission=float(bs.inputs['Transmission Weight'].default_value) if bs else 0)
    if tex:
        tx=tex[0];result['texture'],result['file']=image_info(tx.image)
        result['extension']=tx.extension;result['node']=tx.name
    baked=BAKED.get(ASSET_NAME,{}).get(m.name)
    if baked:
        # The baked proxy preserves the original sampler space; source images are untouched.
        result.update(baked)
        result['source_name']=m.name
    return result

def uv_eval(node,uv):
    if node.type in ['UVMAP','TEX_COORD']:return np.c_[uv,np.zeros(len(uv))]
    if node.type=='VECT_MATH':
        def val(s):return uv_eval(s.links[0].from_node,uv) if s.is_linked else np.broadcast_to(np.array(s.default_value),(len(uv),3)).copy()
        a=val(node.inputs[0]);op=node.operation
        if op=='FRACTION':return a-np.floor(a)
        if op=='MULTIPLY':return a*val(node.inputs[1])
        if op=='ADD':return a+val(node.inputs[1])
        if op=='SCALE':return a*node.inputs[3].default_value
    raise RuntimeError('Unsupported UV node '+node.name+' '+node.type)

def extract(objects,name,tree=False,lod=0):
    global ASSET_NAME
    ASSET_NAME=name.split('_LOD')[0]
    mats=[];mi={};parts=[[],[],[],[],[],[],[]];collv=[];collt=[];objcount=0
    # Hidden collision collections otherwise retain stale copied transforms.
    for c in bpy.data.collections:
        if c.name.startswith('Colisao_preparada'):c.hide_viewport=False
    for obj in objects:
        if obj.type in ['FONT','CURVE']:
            obj.data.resolution_u=3 if not lod else 2;obj.data.bevel_resolution=0
        if name.startswith('pe_estrutura') and obj.type=='MESH' and not obj.name.startswith('COL_'):
            if obj.name.startswith(('Toldo_tecido','Babado_toldo')) and not any(m.type=='SOLIDIFY' for m in obj.modifiers):
                # These source canopies were single-sided quads; give their back faces physical thickness.
                mod=obj.modifiers.new('Espessura_exportacao','SOLIDIFY');mod.thickness=.012;mod.offset=0
            bevel=obj.modifiers.get('Arestas_exportacao')
            if bevel:bevel.show_viewport=not lod;bevel.show_render=not lod
            elif not lod and obj.name.startswith(('Parede_','Banca_','Mesa','Balcao','Armario','Prateleira','Pilar','Moldura','Caixote_','Porta_')) and not any(m.type=='BEVEL' for m in obj.modifiers):
                loc,rot,scale=obj.matrix_world.decompose()
                if min(abs(v) for v in scale)>.0001:
                    # The shared unit cubes have non-uniform scales. Apply scale to a working copy first,
                    # so the bevel stays eight millimetres instead of distorting a thin wall.
                    obj.data=obj.data.copy();obj.data.transform(Matrix.Diagonal((*scale,1)))
                    obj.matrix_world=Matrix.LocRotScale(loc,rot,Vector((1,1,1)))
                    bevel=obj.modifiers.new('Arestas_exportacao','BEVEL');bevel.width=.008;bevel.segments=2;bevel.affect='EDGES';bevel.limit_method='ANGLE'
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        if obj.type not in ['MESH','FONT','CURVE']:continue
        if obj.name.startswith('COL_'):
            ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();v=np.array([obj.matrix_world@v.co for v in me.vertices]);off=len(collv);collv.extend(v);collt.extend(np.array([t.vertices for t in me.loop_triangles])+off);ev.to_mesh_clear();continue
        if obj.hide_render:continue
        if lod and any(c.name.startswith('Interior') for c in obj.users_collection):continue
        if lod and any(c.name.startswith('Vegetacao') for c in obj.users_collection):continue
        if lod>=2 and obj.type=='FONT':continue
        if lod and max(obj.dimensions)<[0,.20,.40,.70][lod]:continue
        if lod and obj.name.startswith('Telhas_ceramicas'):
            mod=obj.modifiers.get('Exportacao_LOD') or obj.modifiers.new('Exportacao_LOD','DECIMATE')
            mod.ratio=[1,.40,.12,.035][lod];bpy.context.view_layer.update()
        for mod in obj.modifiers:
            if mod.type=='NODES':mod.show_viewport=False;mod.show_render=False
        ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
        if not me.loop_triangles:ev.to_mesh_clear();continue
        nvert=len(me.vertices);nloop=len(me.loops);co=np.empty(nvert*3,np.float32);me.vertices.foreach_get('co',co);co=co.reshape(-1,3)
        mat=np.array(obj.matrix_world);pos=co@mat[:3,:3].T+mat[:3,3]
        lvid=np.empty(nloop,np.int32);me.loops.foreach_get('vertex_index',lvid)
        normals=np.array([n.vector[:] for n in me.corner_normals]);normals=normals@np.linalg.inv(mat[:3,:3]);normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-8)
        uv=np.zeros((nloop,2),np.float32)
        if me.uv_layers:
            lay=me.uv_layers.get('UV_Textura') or me.uv_layers.active;lay.data.foreach_get('uv',uv.ravel())
        weight=np.zeros(nvert,np.float32);phase=np.zeros(nvert,np.float32)
        if me.attributes.get('vento_peso'):me.attributes['vento_peso'].data.foreach_get('value',weight)
        if me.attributes.get('vento_fase'):me.attributes['vento_fase'].data.foreach_get('value',phase)
        for idx,m in enumerate(me.materials):
            key=m.as_pointer() if m else 0
            if key not in mi:mi[key]=len(mats);mats.append(material_info(m))
            tris=[t for t in me.loop_triangles if t.material_index==idx]
            if not tris:continue
            lix=np.array([t.loops for t in tris]).ravel();vix=lvid[lix];u=uv[lix].copy();info=mats[mi[key]]
            if info.get('texture'):
                tx=m.node_tree.nodes.get(info.get('node',''))
                if tx and tx.inputs['Vector'].is_linked:u=uv_eval(tx.inputs['Vector'].links[0].from_node,u)[:,:2]
                if info.get('extension') in ['EXTEND','CLIP']:u=np.clip(u,0.0005,.9995)
            if info.get('uv_mode')=='object_projection':
                # Procedural materials had no UVs. Match the canonical four-metre bake surface.
                xyz=pos[vix];axis=np.argmax(np.abs(normals[lix]),axis=1);u=np.zeros((len(lix),2),np.float32)
                for ax,pair in ((0,(1,2)),(1,(0,2)),(2,(0,1))):
                    sel=axis==ax;u[sel]=xyz[sel][:,pair]/float(info.get('canonical_period',4))
            u[:,1]=1-u[:,1]
            # Original foliage RGB shader stores wind weights separately from its texture tint.
            w=weight[vix] if tree else np.zeros(len(vix));ph=phase[vix] if tree else np.zeros(len(vix))
            parts[0].append(pos[vix]);parts[1].append(normals[lix]);parts[2].append(u);parts[3].append(np.full(len(lix),mi[key],np.int32));parts[4].append(w);parts[5].append(ph)
            # A LOD-safe object identifier lets exterior small detail be omitted as a unit.
            exterior=not any(c.name.startswith('Interior') for c in obj.users_collection)
            keep=exterior and (max(obj.dimensions)>.18 or obj.name.startswith(('Parede','Laje','Degrau','Escada','Porta','Telha','Portal')))
            parts[6].append(np.full(len(lix),keep,np.uint8))
        objcount+=1;ev.to_mesh_clear()
    if name.startswith('pe_estrutura') and not lod:
        # A compact roof volume seals the attic without copying thousands of tiles
        # into collision or obstructing the modeled interiors below the ceiling.
        bm=bmesh.new()
        for obj in objects:
            if obj.type!='MESH' or obj.hide_render or not any(c.name.startswith('Cobertura') for c in obj.users_collection):continue
            ev=obj.evaluated_get(dg);me=ev.to_mesh()
            for v in me.vertices:bm.verts.new(obj.matrix_world@v.co)
            ev.to_mesh_clear()
        if len(bm.verts)>3:
            bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.index_update()
            verts=list({v for f in bm.faces for v in f.verts});indices={v:i for i,v in enumerate(verts)}
            off=len(collv);collv.extend(v.co[:] for v in verts);collt.extend([off+indices[v] for v in f.verts] for f in bm.faces)
        bm.free()
    result=dict(position=np.concatenate(parts[0]).astype(np.float32),normal=np.concatenate(parts[1]).astype(np.float32),uv=np.concatenate(parts[2]).astype(np.float32),material=np.concatenate(parts[3]),weight=np.concatenate(parts[4]),phase=np.concatenate(parts[5]),exterior=np.concatenate(parts[6]),collision_vertices=np.array(collv,np.float32),collision_triangles=np.array(collt,np.int32))
    if tree:
        flexible_mats=np.unique(result['material'][result['weight']>.001])
        flexible=np.isin(result['material'],flexible_mats)
        if np.any(flexible):
            # Alpha cards use canopy normals rather than the downward normals of their backing planes.
            p=result['position'][flexible];center=np.mean(p,axis=0);radii=np.maximum(np.ptp(p,axis=0)*.5,.5)
            center[2]=p[:,2].min()+np.ptp(p[:,2])*.25
            outward=(p-center)/(radii*radii);outward[:,2]+=.04/radii[2]
            length=np.linalg.norm(outward,axis=1,keepdims=True)
            outward=np.divide(outward,np.maximum(length,1e-8))
            result['normal'][flexible]=outward
    np.savez_compressed(O/'cache'/(name+'.npz'),**result)
    row=dict(name=name,materials=mats,triangles=len(result['position'])//3,objects=objcount,collision_triangles=len(collt),tree=tree,bb_min=result['position'].min(0).tolist(),bb_max=result['position'].max(0).tolist())
    (O/'cache'/(name+'.json')).write_text(json.dumps(row,indent=2),encoding='utf8');print('MESH_READY',name,row['triangles'],flush=True)
    return row

if __name__=='__main__':
    chosen=None
    if '--ids' in sys.argv:chosen={int(v) for v in sys.argv[sys.argv.index('--ids')+1].split(',')}
    houses=[]
    for path in ([] if '--trees-only' in sys.argv else sorted((P/'estruturas_porto_20261009/modelos').glob('*.blend'))):
        if chosen is not None and int(path.stem[:2]) not in chosen:continue
        bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(40)
        col=bpy.data.collections['Modelo_completo'];row=extract(list(col.all_objects),'pe_estrutura_'+path.stem[:2]);row['source']=str(path);row['floor']=0;houses.append(row)
        for lod in range(1,4):
            lodname=row['name']+'_LOD'+str(lod);lr=extract(list(col.all_objects),lodname,lod=lod)
            c=np.load(O/'cache'/(lodname+'.npz'));values={k:c[k] for k in c.files};mapping=np.array([next(i for i,m in enumerate(row['materials']) if m.get('name')==x.get('name')) for x in lr['materials']])
            values['material']=mapping[values['material']];np.savez_compressed(O/'cache'/(lodname+'.npz'),**values)
            lr['materials']=row['materials'];(O/'cache'/(lodname+'.json')).write_text(json.dumps(lr,indent=2))
    if chosen is not None and '--trees-only' not in sys.argv and (O/'dados/casas.json').exists():
        old=json.loads((O/'dados/casas.json').read_text());houses=sorted([r for r in old if int(r['name'][-2:]) not in chosen]+houses,key=lambda r:r['name'])
    if '--trees-only' not in sys.argv:(O/'dados/casas.json').write_text(json.dumps(houses,indent=2),encoding='utf8')
    if '--casas-only' in sys.argv:print('HOUSES_CACHED_WITH_LODS',len(houses),flush=True);sys.exit(0)
    trees=[]
    for path in sorted((P/'porto_esperanca/modelos/vegetacao_vento').glob('*.blend')):
        bpy.ops.wm.open_mainfile(filepath=str(path));obj=next(o for o in bpy.data.objects if o.type=='MESH' and o.name==path.stem)
        row=extract([obj],'pe_veg_'+path.stem,True);row['source']=str(path);trees.append(row)
    (O/'dados/arvores.json').write_text(json.dumps(trees,indent=2),encoding='utf8')
