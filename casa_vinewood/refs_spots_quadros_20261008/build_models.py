"""Model true recessed ceiling hardware and framed supplied art in Blender."""
import bpy,sys,json,math,bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;R=P.parents[1];W=P.parent;OUT=P/'stream';OUT.mkdir(exist_ok=True)
sys.path[:0]=[r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps',
    r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/sollumz',str(R/'laboratorio_fivem/work/pydeps')]
import numpy as np,addon_utils
addon_utils.enable('Sollumz',default_set=True)
from Sollumz.sollumz_properties import SollumType
from Sollumz.tools.drawablehelper import convert_obj_to_model
from Sollumz.tools.meshhelper import mesh_add_missing_uv_maps,mesh_add_missing_color_attrs
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.iecontext import ExportContext,ExportSettings,export_context_scope
from Sollumz.ydr.ydrexport import export_ydr
from szio.gta5 import AssetTarget,AssetFormat,AssetVersion
from PIL import Image
bpy.ops.wm.open_mainfile(filepath=str(W/'mansao_otimizada.blend'));s=bpy.context.scene
cfg=json.loads((R/'server-data/resources/cidade_mansao/decoracao_iluminacao.json').read_text())
arts=json.loads((P/'artworks.json').read_text());report={'spots':[],'models':{},'artworks':arts}
TARGET=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)
styles={}
def texture(m,node,path):
    tx=m.node_tree.nodes[node];tx.image=bpy.data.images.load(str(path),check_existing=True);tx.image.pack();tx.texture_properties.embedded=True
    if node!='DiffuseSampler':tx.image.colorspace_settings.name='Non-Color'
    else:m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],tx.inputs['Vector'])
def shader(key,preset,diffuse,normal=None,spec=None,shine=.1):
    m=create_shader(preset);m.name='ref_'+key;m['ref_style']=key
    texture(m,'DiffuseSampler',P/'textures'/(diffuse+'.dds'))
    if normal:texture(m,'BumpSampler',P/'textures'/(normal+'.dds'))
    if spec:texture(m,'SpecSampler',P/'textures'/(spec+'.dds'))
    for param,value in [('specularIntensityMult',shine),('specularFalloffMult',65 if shine>.3 else 18),
                        ('specularFresnel',.45 if shine>.3 else .05),('wetnessMultiplier',0),('bumpiness',.45)]:
        if (node:=m.node_tree.nodes.get(param)) is not None:node.set(0,value)
    for node in m.node_tree.nodes:
        if node.type=='BSDF_PRINCIPLED':
            for link in list(node.inputs['Roughness'].links):m.node_tree.links.remove(link)
            node.inputs['Roughness'].default_value=.28 if shine>.3 else .75
            if 'Weight' in node.inputs:node.inputs['Weight'].default_value=1
    # Blender 5.2 added named weight sockets before emission colour. The native
    # exporter uses shader parameters; fix only the authored preview graph.
    em=next((n for n in m.node_tree.nodes if n.type=='EMISSION'),None)
    if em:
        if 'Weight' in em.inputs:
            for link in list(em.inputs['Weight'].links):m.node_tree.links.remove(link)
            em.inputs['Weight'].default_value=1
        m.node_tree.links.new(m.node_tree.nodes['DiffuseSampler'].outputs['Color'],em.inputs['Color'])
    styles[key]=m;return m
shader('white','default.sps','spot_branco',shine=.08)
shader('reflector','normal_spec.sps','spot_metal','normal_plana','metal_spec',.5)
led=shader('lens','emissive.sps','spot_lente');led.node_tree.nodes['emissiveMultiplier'].set(0,3.5)
shader('prism','normal_spec.sps','spot_prisma','normal_plana','metal_spec',.8)
for key in ['reflector','prism']:
    mat=styles[key];bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Metallic'].default_value=.8 if key=='reflector' else .2
shader('bronze','default.sps','moldura_bronze',shine=.28)
shader('black','default.sps','moldura_preta',shine=.15)
shader('inlay','default.sps','moldura_filete',shine=.35)
shader('back','default.sps','quadro_fundo',shine=.02)
for art in arts:shader('art_'+str(art['print']),'normal.sps',f"quadro_{art['print']}_cor",f"quadro_{art['print']}_normal",shine=.04)

def collection(name):
    c=bpy.data.collections.new(name);s.collection.children.link(c);return c
sources=collection('94_MODELOS_REFERENCIA_FONTES');instances=collection('22_SPOTS_E_QUADROS_REFERENCIAS')
sources.hide_render=True
def move(obj,col):
    for c in list(obj.users_collection):c.objects.unlink(obj)
    col.objects.link(obj)
    return obj
def lathe(name,profile,segments,material,closed=True,smooth=True):
    verts=[];rings=[];faces=[]
    for radius,z in profile:
        if radius==0:rings.append([len(verts)]);verts.append((0,0,z))
        else:
            rings.append(list(range(len(verts),len(verts)+segments)))
            verts.extend((radius*math.cos(2*math.pi*j/segments),radius*math.sin(2*math.pi*j/segments),z) for j in range(segments))
    pairs=list(zip(rings,rings[1:]))
    if closed:pairs.append((rings[-1],rings[0]))
    for a,b in pairs:
        if len(a)==len(b)==1:continue
        for j in range(segments):
            k=(j+1)%segments
            if len(a)==1:faces.append((a[0],b[k],b[j]))
            elif len(b)==1:faces.append((a[j],a[k],b[0]))
            else:faces.append((a[j],a[k],b[k],b[j]))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    obj=bpy.data.objects.new(name,mesh);sources.objects.link(obj);mesh.materials.append(material)
    for poly in mesh.polygons:poly.use_smooth=smooth
    return obj
def spot_parts(seg):
    white=lathe('Aro branco chanfrado '+str(seg),[(.060,-.004),(.083,-.004),(.085,-.002),(.085,.002),(.083,.004),(.060,.004),(.058,.002),(.058,-.002)],seg,styles['white'])
    reflector=lathe('Refletor concavo metal '+str(seg),[(.059,-.002),(.048,.013),(.036,.027),(.025,.035),(.025,.038),(.038,.030),(.050,.016),(.061,.0)],seg,styles['reflector'])
    lens=lathe('Lente prismatica facetada '+str(seg),[(.008,.028),(.012,.029),(.016,.030),(.020,.032),(.024,.034),(.024,.039),(.008,.040)],seg,styles['prism'],smooth=False)
    # Small glass facets catch reflected light without making a large extra
    # texture. Alternate edge heights by 0.25 mm within the lens front bands.
    for v in lens.data.vertices:
        ring=v.index//seg;j=v.index%seg
        if ring<5:v.co.z+=.00025*(1 if (j+ring)%2 else -1)
    bm=bmesh.new();bm.from_mesh(lens.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(lens.data);bm.free();lens.data.update()
    core=lathe('Nucleo LED quente '+str(seg),[(0,.027),(.008,.028),(.008,.039),(0,.040)],seg,styles['lens'],smooth=False)
    return [white,reflector,lens,core]
spot_lods={seg:spot_parts(seg) for seg in [48,24,12,8]}

def box(name,lo,hi,mat,col=sources,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)])
    o=move(bpy.context.object,col);o.name=name;o.dimensions=[hi[i]-lo[i] for i in range(3)]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.clear();o.data.materials.append(mat)
    if bevel:
        bpy.context.view_layer.objects.active=o
        m=o.modifiers.new('Aresta arredondada real','BEVEL');m.width=bevel;m.segments=2
        bpy.ops.object.modifier_apply(modifier=m.name)
    return o
art_sources={}
for art in arts:
    ident=art['print'];w=art['canvas_width_m'];h=art['canvas_height_m'];parts=[];outer=styles[art['frame']]
    parts.append(box('Quadro '+str(ident)+' fundo',[-w/2-.024,-.022,-h/2-.024],[w/2+.024,0,h/2+.024],styles['back']))
    # A closed thin canvas, with image UVs on its actual front, not a billboard.
    canvas=box('Quadro '+str(ident)+' tela com relevo',[-w/2,-.034,-h/2],[w/2,-.026,h/2],styles['art_'+str(ident)])
    uv=canvas.data.uv_layers[0] if canvas.data.uv_layers else canvas.data.uv_layers.new(name='UVMap 0')
    uv.name='UVMap 0'
    for poly in canvas.data.polygons:
        for li in poly.loop_indices:
            co=canvas.data.vertices[canvas.data.loops[li].vertex_index].co
            uv.data[li].uv=(co.x/w+.5,co.z/h+.5)
    canvas['preserve_source_uv']=True;parts.append(canvas)
    for label,a,b in [('esquerda',[-w/2-.028,-.045,-h/2-.028],[-w/2,-.003,h/2+.028]),
                       ('direita',[w/2,-.045,-h/2-.028],[w/2+.028,-.003,h/2+.028]),
                       ('superior',[-w/2,-.045,h/2],[w/2,-.003,h/2+.028]),
                       ('inferior',[-w/2,-.045,-h/2-.028],[w/2,-.003,-h/2])]:
        parts.append(box('Quadro '+str(ident)+' moldura '+label,a,b,outer,bevel=.0008))
    if ident<4:
        for label,a,b in [('E',[-w/2-.004,-.046,-h/2],[ -w/2,-.043,h/2]),
                           ('D',[w/2,-.046,-h/2],[w/2+.004,-.043,h/2]),
                           ('S',[-w/2-.004,-.046,h/2],[w/2+.004,-.043,h/2+.004]),
                           ('I',[-w/2-.004,-.046,-h/2-.004],[w/2+.004,-.043,-h/2])]:
            parts.append(box('Quadro '+str(ident)+' filete bronze '+label,a,b,styles['inlay']))
    art_sources[ident]=parts
    parent=bpy.data.objects.new(art['name'],None);instances.objects.link(parent);parent.location=art['position'];parent.rotation_euler.z=art['heading']
    for src in parts:
        obj=src.copy();obj.data=src.data;instances.objects.link(obj);obj.parent=parent

# Remove only the old ceiling rings/diffusers. All twenty stair LED strips and
# profiles remain in their original native drawable and position.
old=bpy.data.collections['18_SPOTS_E_LED_ESCADA']
for obj in list(old.objects):
    if obj.name.startswith('Spot '):bpy.data.objects.remove(obj,do_unlink=True)
assert len(old.objects)==40,('Unexpected stair fixture count',len(old.objects))
cols={key:next(c for c in bpy.data.collections if c.name.startswith(prefix)) for key,prefix in [('slabs','04_'),('ceiling','06_')]}
for c in cols.values():c.hide_viewport=False;c.hide_render=False
bpy.context.view_layer.update()
support=[]
for c in cols.values():
    for obj in c.objects:
        if obj.type!='MESH':continue
        obj.data.calc_loop_triangles()
        vs=[obj.matrix_world@v.co for v in obj.data.vertices]
        polys=[tuple(t.vertices) for t in obj.data.loop_triangles]
        support.append((obj,BVHTree.FromPolygons(vs,polys,all_triangles=True)))
cutters={}
for row in cfg['spots']:
    x,y,_=row['position'];z=row['ceiling_z'];match=None
    for obj,bvh in support:
        hit,normal,face,distance=bvh.ray_cast(Vector((x,y,z-.03)),Vector((0,0,1)),.04)
        if hit is not None and abs(hit.z-z)<.002 and normal.z<-.7:match=obj;break
    assert match is not None,('Spot has no ceiling surface',row)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.062,depth=.060,location=(x,y,z+.018))
    cutter=bpy.context.object;cutter.name='Cavidade spot '+str(row['id']);cutters.setdefault(match,[]).append(cutter)
    parent=bpy.data.objects.new('Spot referencia '+str(row['id']),None);instances.objects.link(parent);parent.location=(x,y,z)
    for src in spot_lods[48]:
        obj=src.copy();obj.data=src.data;instances.objects.link(obj);obj.parent=parent
    report['spots'].append(dict(id=row['id'],position=[x,y,z],ceiling_object=match.name,diameter_m=.17,aperture_m=.124,recess_m=.048))
for obj,items in cutters.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in items:o.select_set(True)
    bpy.context.view_layer.objects.active=items[0];bpy.ops.object.join();cutter=bpy.context.object
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Cavidades reais spots 48 mm','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
    print('CEILING_RECESSES',obj.name,len(items),flush=True)

# Material definitions for the two modified architectural drawables only.
def archmat(family,preset,diffuse,normal=None,tile=2.4):
    m=create_shader(preset);m.name='ref_arch_'+family;m['ref_style']='arch_'+family;m['uv_tile_m']=tile
    tx=m.node_tree.nodes['DiffuseSampler'];tx.image=bpy.data.images.load(str(diffuse),check_existing=True);tx.texture_properties.embedded=True;tx.image.pack()
    m.node_tree.links.new(m.node_tree.nodes['UVMap 0'].outputs['UV'],tx.inputs['Vector'])
    if normal:
        tx=m.node_tree.nodes['BumpSampler'];tx.image=bpy.data.images.load(str(normal),check_existing=True);tx.texture_properties.embedded=True;tx.image.colorspace_settings.name='Non-Color';tx.image.pack()
    styles['arch_'+family]=m
    return m
oldopt=W/'otimizacao_20261008/textures'
materialcfg=json.loads((W/'materiais_sala.json').read_text())
archmat('wood','normal.sps',oldopt/'im_wood_panels_05.dds',oldopt/'im_wood_panels_05_n.dds')
archmat('marble','normal.sps',oldopt/'piso_marmore.dds',oldopt/'piso_marmore_n.dds',materialcfg['marble']['tile_m'])
from szio.gta5 import try_load_asset
installed=R/'server-data/resources/cidade_mansao/stream'
teto=try_load_asset(installed/'mansao_teto.ydr')
for tex in teto.shader_group.embedded_textures.values():
    path=P/'textures'/(tex.name+'.dds');path.write_bytes(tex.data.read_bytes())
ceilingdiff=next(p.value for p in teto.shader_group.shaders[0].parameters if isinstance(p.value,str))
archmat('ceiling','default.sps',P/'textures'/(ceilingdiff+'.dds'))

def export(name,objects,architecture=False):
    root=bpy.data.objects.new(name,None);s.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE
    parts=[];dg=bpy.context.evaluated_depsgraph_get()
    for src in objects:
        if src.type!='MESH':continue
        me=bpy.data.meshes.new_from_object(src.evaluated_get(dg),depsgraph=dg);me.transform(src.matrix_world)
        indices=[p.material_index for p in me.polygons]
        if architecture:
            fallback='wood' if name=='mansao_pisos' else 'ceiling'
            families=[m.get('finish_family',fallback) if m else fallback for m in src.data.materials] or [fallback]
            me.materials.clear()
            for family in families:
                assert 'arch_'+family in styles,(name,src.name,family)
                me.materials.append(styles['arch_'+family])
        elif name=='mansao_spots_led':
            family=src.data.materials[0]['decor_family'];me.materials.clear();me.materials.append(stair_styles[family])
        for poly,index in zip(me.polygons,indices):poly.material_index=min(index,len(me.materials)-1)
        uv=me.uv_layers[0] if me.uv_layers else me.uv_layers.new(name='UVMap 0');uv.name='UVMap 0'
        if not src.get('preserve_source_uv'):
            for poly in me.polygons:
                axis=max(range(3),key=lambda i:abs(poly.normal[i]));axes=(0,1) if axis==2 else ((0,2) if axis==1 else (1,2))
                tile=me.materials[poly.material_index].get('uv_tile_m',1)
                for li in poly.loop_indices:
                    co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]/tile,co[axes[1]]/tile)
        mesh_add_missing_uv_maps(me);mesh_add_missing_color_attrs(me)
        shade=.65 if architecture and all(m['ref_style'] in ('arch_wood','arch_ceiling') for m in me.materials) else 1
        for attr in me.color_attributes:attr.data.foreach_set('color_srgb',np.tile(np.array([shade,shade,shade,1],dtype=np.float32),len(attr.data)))
        o=bpy.data.objects.new(src.name+'_native',me);s.collection.objects.link(o);o.parent=root;convert_obj_to_model(o);parts.append(o)
    pts=np.array([v.co for o in parts for v in o.data.vertices]);lo=pts.min(0);hi=pts.max(0)
    with export_context_scope(ExportContext(name,ExportSettings(targets=TARGET))):export_ydr(root).save(OUT,TARGET)
    report['models'][name]={'lo':lo.tolist(),'hi':hi.tolist(),'objects':len(parts)}
    for obj in parts:bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.objects.remove(root,do_unlink=True)
    print('EXPORTED_REF',name,flush=True)
stair_styles={}
for family,rgb in [('led',(255,214,166)),('trim',(194,187,173))]:
    key='mansao_decor_'+family;path=P/'textures'/(key+'.dds');Image.new('RGBA',(4,4),(*rgb,255)).save(path,pixel_format='DXT5')
    m=create_shader('emissive.sps' if family=='led' else 'default.sps');m.name=key
    tx=m.node_tree.nodes['DiffuseSampler'];tx.image=bpy.data.images.load(str(path),check_existing=True);tx.texture_properties.embedded=True
    if family=='led':m.node_tree.nodes['emissiveMultiplier'].set(0,2.5)
    stair_styles[family]=m
for seg,parts in spot_lods.items():export('ref_spot_'+str(seg),parts)
for art in arts:export(art['model'],art_sources[art['print']])
export('mansao_spots_led',list(old.objects))
export('mansao_pisos',list(cols['slabs'].objects),True)
export('mansao_teto',list(cols['ceiling'].objects),True)
sources.hide_viewport=True
report['modified_ceiling_objects']=len(cutters)
(P/'modeling_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s['reference_revision']='spots-quadros-referencias-2026-10-08'
bpy.ops.wm.save_as_mainfile(filepath=str(W/'mansao_spots_quadros.blend'),compress=True)
print('BLENDER_REFERENCES_READY',len(report['spots']),'spots; four framed canvases',flush=True)
