# Design space: X left-to-right on the marked wall, negative Y toward room.
# An additive fitted ensemble; no replacement of architectural geometry.
def tube(name,pts,r,family='bronze',sides=8):
    for a,b in zip(pts,pts[1:]):
        v=Vector(b)-Vector(a)
        o=lathe(name,[(0,0),(r,0),(r*.8,v.length),(0,v.length)],(0,0,0),family,sides)
        tx=v.to_track_quat('Z','Y').to_matrix().to_4x4()
        for vert in o.data.vertices:vert.co=tx@vert.co+Vector(a)
def frame(name,x0,x1,z0,z1,width=.035):
    for a,b in [((x0,-.042,z0),(x0+width,-.008,z1)),((x1-width,-.042,z0),(x1,-.008,z1)),((x0+width,-.042,z0),(x1-width,-.008,z0+width)),((x0+width,-.042,z1-width),(x1-width,-.008,z1))]:
        box(name,a,b,'creme',.003)
    for a,b in [((x0+width,-.030,z0+width),(x0+width+.009,-.018,z1-width)),((x1-width-.009,-.030,z0+width),(x1-width,-.018,z1-width)),((x0+width,-.030,z0+width),(x1-width,-.018,z0+width+.009)),((x0+width,-.030,z1-width-.009),(x1-width,-.018,z1-width))]:
        box(name+' filete',a,b,'creme',.002)
frame('Boiserie painel quadros',.15,3.42,.15,3.047,.043)
frame('Boiserie porta',3.50,5.53,.05,3.047,.041)
# Three separate moldings above the doorway imitate the reference lintel.
box('Friso sobre porta',(3.55,-.042,2.775),(5.485,-.008,2.814),'creme',.003)
box('Friso superior',(3.55,-.038,2.977),(5.485,-.008,3.012),'creme',.002)
# Floating console, true cabinet structure and four separately beveled fronts.
box('Aparador suspenso corpo',(.29,-.403,.35),(3.30,-.017,.865),'madeira',.004,True)
for j in range(4):
    a=.30+j*.7475
    box('Aparador frente %d'%j,(a,-.422,.363),(a+.738,-.398,.844),'madeira',.003)
box('Aparador tampo',(.275,-.425,.844),(3.315,-.012,.871),'madeira',.003)
box('Perfil luz sob aparador',(.34,-.225,.342),(3.25,-.208,.351),'bronze',.001)
box('LED sob aparador',(.35,-.22,.340),(3.24,-.212,.343),'led',0)
for i,(x0,x1) in enumerate([(.46,1.69),(1.89,3.12)]):
    z0=1.135;z1=2.760
    box('Quadro %d suporte'%i,(x0-.018,-.051,z0-.018),(x1+.018,-.016,z1+.018),'creme',.002)
    box('Quadro %d tela'%i,(x0,-.066,z0),(x1,-.051,z1),'arte'+str(i+1),0)
    for a,b in [((x0-.018,-.082,z0-.018),(x0,-.025,z1+.018)),((x1,-.082,z0-.018),(x1+.018,-.025,z1+.018)),((x0,-.082,z0-.018),(x1,-.025,z0)),((x0,-.082,z1),(x1,-.025,z1+.018))]:box('Quadro moldura bronze %d'%i,a,b,'bronze',.001)
    cx=(x0+x1)/2
    box('Arandela placa %d'%i,(cx-.045,-.071,2.887),(cx+.045,-.01,2.940),'bronze',.002)
    box('Arandela braco %d'%i,(cx-.009,-.175,2.905),(cx+.009,-.065,2.920),'bronze',.002)
    box('Arandela barra %d'%i,(cx-.325,-.192,2.892),(cx+.325,-.159,2.918),'bronze',.003)
    box('Arandela luz %d'%i,(cx-.310,-.183,2.889),(cx+.310,-.166,2.893),'led',0)
# Left branch vase and second small porcelain vessel.
vase('Vaso ramo oliva',.66,-.234,.874,.338,.129,'ceramica')
vase('Vaso ceramica branco',.975,-.258,.874,.248,.087,'creme','narrow')
rng=np.random.default_rng(913)
for k in range(8):
    start=Vector((.66,-.234,1.162))
    end=Vector((.66+rng.uniform(-.46,.32),-.22+rng.uniform(-.12,.13),1.62+rng.uniform(.10,.35)))
    pts=[tuple(start.lerp(end,j/5)+Vector((.025*math.sin(j+k),0,0))) for j in range(6)]
    tube('Ramo oliva',pts,.003,'bronze',6)
    for j in range(2,6):
        p=Vector(pts[j])
        for sign in [-1,1]:
            tip=p+Vector((sign*rng.uniform(.055,.11),rng.uniform(-.025,.025),rng.uniform(-.028,.052)))
            mid=(p+tip)/2;d=tip-p;side=Vector((-d.z,0,d.x)).normalized()*.013
            mesh('Folha oliva',list(map(tuple,[p,mid+side,tip,mid-side])),[(0,1,2,3),(3,2,1,0)],'folha',[(0,0),(.2,.5),(1,1),(.8,.5)],True)
vase('Tigela preta central',1.89,-.244,.874,.161,.244,'preto','bowl')
for j,(w,d) in enumerate([(.43,.24),(.40,.245),(.445,.235)]):
    x=2.73;z=.874+j*.031
    box('Livro paginas '+str(j),(x-w/2,-.31,z+.004),(x+w/2,-.31+d,z+.025),'creme',.001)
    for zz in [z,z+.025]:box('Livro capa '+str(j),(x-w/2-.003,-.314,zz),(x+w/2+.003,-.31+d+.002,zz+.004),'ceramica',.0008)
vase('Objeto ceramico redondo',2.73,-.215,.97,.135,.074,'creme')
for k in range(4):tube('Ramo pequeno ceramica',[(2.73,-.215,1.102),(2.725+k*.009,-.213,1.165+k*.01)],.0015,'bronze',5)
# Door frame fits the existing 1.1 m opening; the leaf is a separate model.
for a,b in [((3.64,-.060,0),(3.684,.20,2.5)),((4.696,-.060,0),(4.74,.20,2.5)),((3.684,-.060,2.455),(4.696,.20,2.5))]:box('Batente madeira porta',a,b,'madeira',.003,True)
box('Rebaixo escuro acima folha',(3.684,-.021,2.431),(4.696,.030,2.456),'preto',.001)
# The wall molding follows the jamb; it must not run across the door opening.
for o in list(parts):
    if o.name.startswith('Boiserie porta'):
        ps=[v.co for v in o.data.vertices]
        if max(p.z for p in ps)<.16 and min(p.x for p in ps)<3.64 and max(p.x for p in ps)>4.74:
            parts.remove(o);bpy.data.objects.remove(o,do_unlink=True)
for a,b in [((3.541,-.042,.05),(3.64,-.008,.091)),((4.74,-.042,.05),(5.489,-.008,.091))]:box('Boiserie rodape lateral porta',a,b,'creme',.003)
fixed_parts=list(parts);fixed_solids=list(solids)
# Leave 85 mm clearance beyond the perpendicular wine cabinet's 647 mm depth.
panel_s=(3.42-.72)/(3.42-.15)
for o in fixed_parts:
    if o.name.startswith(('Boiserie porta','Friso sobre porta','Friso superior','Batente madeira porta')):continue
    for v in o.data.vertices:v.co.x=.72+(v.co.x-.15)*panel_s
    o.data.update()
for q in fixed_solids:
    if q['name'].startswith('Aparador'):
        q['lo'][0]=.72+(q['lo'][0]-.15)*panel_s;q['hi'][0]=.72+(q['hi'][0]-.15)*panel_s
parts.clear();solids.clear()
# Door in design coordinates; negative X from the right-hand hinge in export.
left=3.684;right=4.696;z0=.015;z1=2.442;glass0=4.19;glass1=4.423;g0=.218;g1=2.290
for name,a,b in [('Folha madeira esquerda',(left,-.0225,z0),(glass0,.0225,z1)),('Folha madeira direita',(glass1,-.0225,z0),(right,.0225,z1)),('Folha madeira base vidro',(glass0,-.0225,z0),(glass1,.0225,g0)),('Folha madeira topo vidro',(glass0,-.0225,g1),(glass1,.0225,z1))]:box(name,a,b,'madeira',.002,True)
for a,b in [((glass0-.014,-.026,g0-.014),(glass0,-.022,g1+.014)),((glass1,-.026,g0-.014),(glass1+.014,-.022,g1+.014)),((glass0,-.026,g0-.014),(glass1,-.022,g0)),((glass0,-.026,g1),(glass1,-.022,g1+.014))]:box('Perfil preto visor',a,b,'preto',.001)
box('Visor vidro fumado',(glass0,-.004,g0),(glass1,.004,g1),'vidro_transparente',0,True)
for sign in [-1,1]:
    a=sorted([sign*.042,sign*.024]);b=sorted([sign*.070,sign*.054])
    for z in [.87,1.32]:box('Puxador suporte',(left+.071,a[0],z),(left+.09,a[1],z+.024),'preto',.002)
    box('Puxador vertical',(left+.069,b[0],.860),(left+.092,b[1],1.358),'preto',.005)
for z in [.18,1.19,2.2]:box('Dobradiça preta',(right-.017,-.018,z),(right+.007,.040,z+.073),'preto',.002)
door_parts=list(parts);door_solids=list(solids);parts[:]=fixed_parts+door_parts
spec['parts']=len(parts);spec['collision_boxes']=fixed_solids;spec['door_collision_boxes']=door_solids
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'parede_aparador_editavel.blend'),compress=True)
tx=Matrix(((0,1,0,14.168),(-1,0,0,-.98),(0,0,1,-.8),(0,0,0,1)))
def export_group(srcparts,model,transform):
    root=bpy.data.objects.new(model,None);bpy.context.scene.collection.objects.link(root);root.sollum_type=SollumType.DRAWABLE;out=[]
    for src in srcparts:
        me=src.data.copy();me.transform(transform);me.update();obj=bpy.data.objects.new(src.name+'_export',me);bpy.context.scene.collection.objects.link(obj);obj.parent=root;convert_obj_to_model(obj);out.append(obj)
    pts=np.array([v.co for o in out for v in o.data.vertices]);bounds={'lo':pts.min(0).tolist(),'hi':pts.max(0).tolist()}
    with export_context_scope(ExportContext(model,ExportSettings(targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)))):export_ydr(root).save(O,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),))
    for ratio,suffix in [(.6,'medium'),(.25,'low'),(.10,'verylow')]:
        bpy.ops.object.select_all(action='DESELECT');copies=[]
        for src in out:
            obj=src.copy();obj.data=src.data.copy();bpy.context.scene.collection.objects.link(obj);obj.parent=None;obj.select_set(True);copies.append(obj)
        bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();obj=bpy.context.object
        dec=obj.modifiers.new('LOD simplificado','DECIMATE');dec.ratio=ratio;dec.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=dec.name)
        name=model+'_'+suffix;lr=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(lr);lr.sollum_type=SollumType.DRAWABLE;obj.parent=lr;convert_obj_to_model(obj)
        with export_context_scope(ExportContext(name,ExportSettings(targets=(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),)))):export_ydr(lr).save(O,(AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),))
        bpy.data.objects.remove(obj,do_unlink=True);bpy.data.objects.remove(lr,do_unlink=True)
    return bounds
spec['fixed_bounds']=export_group(fixed_parts,spec['model'],tx)
spec['door_bounds']=export_group(door_parts,spec['door_model'],Matrix.Translation(-Vector(spec['door_hinge_local'])))
spec['door_hinge_house']=list(tx@Vector(spec['door_hinge_local']))
(P/'spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('APARADOR_BUILT',spec['parts'],spec['fixed_bounds'],spec['door_hinge_house'],flush=True)
