"""Bake authored materials and extract evaluated geometry; preserve source blend."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np

P=Path(__file__).resolve().parent;R=P.parents[1];T=P/'texturas';T.mkdir(parents=True,exist_ok=True)
BASE=P/'castelo_estrutura.blend'
digest=hashlib.sha256(BASE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(BASE))
s=bpy.context.scene;original_objects=list(bpy.data.objects)
materials=list(bpy.data.materials)
assert s.unit_settings.scale_length==1
defs=[]
for i,m in enumerate(materials):
    if not m.use_nodes:continue
    p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if p is None:continue
    isglass='Vidro' in m.name
    large='Calcario' in m.name or 'Ardosia' in m.name
    medium=any(t in m.name for t in ['Piso da mansao','Parede branca','Madeira nogueira','Boiserie conselho'])
    textured=large or medium or m.name.startswith('Linho') or m.name in ['Acesso veicular fosco','Pavers acesso']
    key='crf_m%02d'%i
    defs.append({'id':i,'name':m.name,'key':key,'resolution':2048 if large else 1024 if medium else 512 if m.name in ['Acesso veicular fosco','Pavers acesso'] else 512 if textured else 64,
                 'tile_uv':[1.2,1.2] if m.name in ['Acesso veicular fosco','Pavers acesso'] else [4.8,4.32] if 'Calcario' in m.name else [1.2,1.2] if 'Ardosia' in m.name else [5.4,5.4] if 'Parede branca' in m.name else [4.8,4.8],
                 'glass':isglass,'emission':float(p.inputs['Emission Strength'].default_value),
                 'roughness':float(p.inputs['Roughness'].default_value),'metallic':float(p.inputs['Metallic'].default_value),
                 'generated':any(n.type=='TEX_COORD' and any(l.from_node==n and l.from_socket.name=='Generated' for l in m.node_tree.links) for n in m.node_tree.nodes)})

# Bake colour and tangent normals with no baked sunlight or room illumination.
for o in original_objects:o.hide_render=True
s.render.engine='CYCLES';s.cycles.samples=1;s.cycles.use_denoising=False
s.render.bake.margin=0;s.render.bake.use_clear=True
bpy.ops.mesh.primitive_plane_add(size=4,location=(0,0,0))
plane=bpy.context.object;plane.name='BAKE_TILE_4M'
uv=plane.data.uv_layers.active
for row in defs:
    if '--skip-bake' in sys.argv or row['name'] not in ['Acesso veicular fosco','Pavers acesso']:
        assert all((T/(row['key']+'_'+suffix+'.png')).exists() for suffix in ['diffuse','normal'])
        continue
    m=materials[row['id']];copy=m.copy();copy.name='BAKE_'+row['key']
    plane.data.materials.clear();plane.data.materials.append(copy)
    bpy.ops.object.select_all(action='DESELECT');plane.select_set(True);bpy.context.view_layer.objects.active=plane
    nt=copy.node_tree;bsdf=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    for tc in [n for n in nt.nodes if n.type=='TEX_COORD']:
        links=[l for l in list(nt.links) if l.from_node==tc and l.from_socket.name=='UV']
        if links:
            scale=nt.nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(*row['tile_uv'],1)
            nt.links.new(tc.outputs['UV'],scale.inputs[0])
            for l in links:
                target_socket=l.to_socket;nt.links.remove(l);nt.links.new(scale.outputs[0],target_socket)
    output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL')
    image=bpy.data.images.new(row['key']+'_normal',width=row['resolution'],height=row['resolution'],alpha=True)
    image.colorspace_settings.name='Non-Color'
    target=nt.nodes.new('ShaderNodeTexImage');target.image=image;nt.nodes.active=target
    bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT')
    image.filepath_raw=str(T/(row['key']+'_normal.png'));image.file_format='PNG';image.save()
    # Switch only the bake copy to unlit base colour, preserving original graph.
    emission=nt.nodes.new('ShaderNodeEmission')
    emission.inputs['Strength'].default_value=1
    if bsdf.inputs['Base Color'].is_linked:
        nt.links.new(bsdf.inputs['Base Color'].links[0].from_socket,emission.inputs['Color'])
    else:emission.inputs['Color'].default_value=bsdf.inputs['Base Color'].default_value
    nt.links.new(emission.outputs[0],output.inputs['Surface'])
    color=bpy.data.images.new(row['key']+'_diffuse',width=row['resolution'],height=row['resolution'],alpha=True)
    target.image=color;nt.nodes.active=target
    bpy.ops.object.bake(type='EMIT')
    color.filepath_raw=str(T/(row['key']+'_diffuse.png'));color.file_format='PNG';color.save()
    bpy.data.images.remove(color);bpy.data.images.remove(image);bpy.data.materials.remove(copy)
    print('BAKED',row['key'],row['name'],row['resolution'],flush=True)
bpy.data.objects.remove(plane,do_unlink=True)
matids={m.name:i for i,m in enumerate(materials)};byid={r['id']:r for r in defs}
groups={};collisions={};objects=[];lights=[]
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
for o in original_objects:
    # Reference envelopes, original preserved tennis court and measuring dummies
    # are not new map geometry. Building, fittings, driveway and garage are.
    if o.type=='LIGHT' and o.data.type=='AREA' and (o.name.startswith('Iluminacao interior') or 'iluminacao ampla' in o.name):
        lights.append({'position':list(o.location),'color':list(o.data.color),'energy':o.data.energy});continue
    if o.type!='MESH' or o.name.startswith(('Envelope medido','Quadra original','Linha perimetro quadra','Rede quadra referencia','Pessoa 1,80m','Visitante','Escolta / veiculo','Carro garagem','Topiaria.')):continue
    if o.name=='Topiaria' or any(c.name.startswith('05_') for c in o.users_collection):continue
    col=o.users_collection[0].name
    prefix=col[:2]
    base={'00':'implantacao','01':'terreo','02':'suites','03':'conselho','04':'cobertura'}.get(prefix)
    if prefix=='07':base='terreo' if o.location.z<4.9 else 'suites' if o.location.z<9.1 else 'conselho'
    if base is None:continue
    architecture=o.name.startswith(('Terreno base','Trajeto veicular','Passeio de contorno','Guia baixa','Fachada','Torre base','Torre verga','Parede torre','Piso pavimento','Escada lance','Patamar','Forro','Cobertura','Telhado','Garagem','Divisoria','Suite frontal','Suite fundos','Banheiro suite','Equipe /','Salao /','Cozinha /','Apoio /','Conselho /','Guarda-corpo','Vidro','Caixilho','Cimalha','Coluna','Capitel','Entrada principal','Friso inferior','Sacada','Cantaria','Peitoril','Verga','Moldura torre'))
    category='arquitetura' if architecture else 'detalhes'
    if base in ['implantacao','cobertura']:category='arquitetura'
    name='crf_'+base+'_'+category
    me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg)
    me.transform(o.matrix_world);me.update();me.calc_loop_triangles()
    # Existing UVs are in metres. Added objects receive planar metre UVs.
    haduv=bool(me.uv_layers)
    layer=me.uv_layers[0] if haduv else me.uv_layers.new(name='UVMap 0');layer.name='UVMap 0'
    ps=np.array([v.co for v in me.vertices]);lo=ps.min(0);hi=ps.max(0)
    for poly in me.polygons:
        mid=matids.get(me.materials[poly.material_index].name,0) if me.materials else 0
        row=byid[mid]
        axes=(0,1) if abs(poly.normal.z)>.5 else ((0,2) if abs(poly.normal.y)>.5 else (1,2))
        for li in poly.loop_indices:
            pos=me.vertices[me.loops[li].vertex_index].co
            if row['generated']:
                layer.data[li].uv=tuple((pos[a]-lo[a])/max(float(hi[a]-lo[a]),.001) for a in axes)
            elif haduv:layer.data[li].uv=(layer.data[li].uv.x/row['tile_uv'][0],layer.data[li].uv.y/row['tile_uv'][1])
            else:layer.data[li].uv=(pos[axes[0]]/row['tile_uv'][0],pos[axes[1]]/row['tile_uv'][1])
    normals=me.corner_normals
    count=0
    for tri in me.loop_triangles:
        mid=matids[me.materials[tri.material_index].name]
        pts=np.array([me.vertices[v].co for v in tri.vertices])
        if np.linalg.norm(np.cross(pts[1]-pts[0],pts[2]-pts[0]))<1e-9:continue
        out=groups.setdefault(name,{}).setdefault(mid,[])
        uvpts=np.array([layer.data[li].uv for li in tri.loops])
        e1,e2=pts[1]-pts[0],pts[2]-pts[0];d1,d2=uvpts[1]-uvpts[0],uvpts[2]-uvpts[0]
        determinant=d1[0]*d2[1]-d1[1]*d2[0]
        tangent=(e1*d2[1]-e2*d1[1])/determinant if abs(determinant)>1e-12 else e1
        bitangent=(e2*d1[0]-e1*d2[0])/determinant if abs(determinant)>1e-12 else e2
        for vi,li in zip(tri.vertices,tri.loops):
            n=np.array(normals[li].vector);t=tangent-n*np.dot(n,tangent)
            if np.linalg.norm(t)<1e-8:t=np.cross(n,np.eye(3)[np.argmin(abs(n))])
            t/=max(np.linalg.norm(t),1e-9);sign=-1 if np.dot(np.cross(n,t),bitangent)<0 else 1
            out.append([*me.vertices[vi].co,*n,*layer.data[li].uv,*t,sign])
        # Preserve true floor holes and door openings. Glass windows are solid.
        solid=architecture or o.name.startswith(('Mesa','Cadeira','Conselho','Presidencia','SUITE','Equipe E','Equipe D','Cozinha bancada','Ilha cozinha','Armario despensa','Palco','Fonte bacia','Fonte pedestal','Vaso exterior','Boiserie','Lambril'))
        if solid:collisions.setdefault(name,[]).append(pts.tolist())
        count+=1
    objects.append({'name':o.name,'group':name,'bounds':[lo.tolist(),hi.tolist()],'triangles':count})
    bpy.data.meshes.remove(me)
    if len(objects)%200==0:print('EXTRACT_PROGRESS',len(objects),o.name,flush=True)
arrays={};records=[]
for name,shaders in groups.items():
    for mid,rows in shaders.items():
        key=name+'__'+str(mid);arrays[key]=np.array(rows,dtype=np.float32)
        records.append({'key':key,'group':name,'material':mid,'vertices':len(rows),'triangles':len(rows)//3})
np.savez_compressed(P/'geometria.npz',**arrays)
np.savez_compressed(P/'colisoes.npz',**{k:np.array(v,dtype=np.float32) for k,v in collisions.items()})
report={'source':str(BASE),'source_sha256':digest,'anchor':list(s['gta_anchor_xyz']),'rotation':s['gta_rotation_z_degrees'],'materials':defs,'geometry':records,'objects':objects,'lights':lights,'metric_scale':True,'total_triangles':sum(r['triangles'] for r in records)}
(P/'extracao.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==digest
print('EXTRACTED',report['total_triangles'],len(groups),'groups',flush=True)
