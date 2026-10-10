import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).resolve().parent
BASE = OUT.parent / 'modelo' / 'castelo_rockford.blend'
original_hash = hashlib.sha256(BASE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(BASE))
s = bpy.context.scene
before_objects = set(bpy.data.objects)
before_triangles = 0
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.data.calc_loop_triangles()
        before_triangles += len(o.data.loop_triangles)

cols = {}
for name, parent in [('01_ACABAMENTOS_SALAO', '01_TERREO'), ('03_ACABAMENTOS_CONSELHO', '03_REUNIAO'), ('00_JARDIM_DETALHES', '00_IMPLANTACAO')]:
    c = bpy.data.collections.new(name)
    bpy.data.collections[parent].children.link(c)
    cols[name] = c
C = cols['01_ACABAMENTOS_SALAO']

def material(name, color, rough=.5, metal=0, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if emission:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = emission
    return m

trim = bpy.data.materials['Cantaria esculpida / marfim']
wood = bpy.data.materials['Madeira nogueira']
gold = bpy.data.materials['Bronze envelhecido']
iron = bpy.data.materials['Ferro preto']
fabric = bpy.data.materials['Linho claro']
ivory = material('Boiserie / marfim acetinado', (.72, .69, .61), .55)
darkwood = material('Boiserie conselho / nogueira escura', (.065, .032, .018), .42)
led = material('Difusor lustre / luz quente 3000 K', (1, .72, .38), .35, emission=4)
leaves = material('Folhagem topiaria / variacao natural', (.07, .16, .045), .9)

# Fine surface detail without adding geometric subdivisions.
for m in [wood, darkwood]:
    nt = m.node_tree
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeVectorMath'); mapping.operation = 'MULTIPLY'
    mapping.inputs[1].default_value = (2, 35, 4)
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 3
    noise.inputs['Detail'].default_value = 2
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .18
    ramp.color_ramp.elements[0].color = (.042, .016, .006, 1)
    ramp.color_ramp.elements[1].position = .82
    ramp.color_ramp.elements[1].color = (.20, .092, .031, 1) if m == wood else (.095, .044, .019, 1)
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .12
    bump.inputs['Distance'].default_value = .003
    nt.links.new(tc.outputs['Generated'], mapping.inputs[0])
    nt.links.new(mapping.outputs[0], noise.inputs['Vector'])
    nt.links.new(noise.outputs['Fac'], ramp.inputs[0])
    nt.links.new(ramp.outputs['Color'], nt.nodes.get('Principled BSDF').inputs['Base Color'])
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], nt.nodes.get('Principled BSDF').inputs['Normal'])
nt = fabric.node_tree
noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 160
bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .13; bump.inputs['Distance'].default_value = .0015
nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
nt.links.new(bump.outputs['Normal'], nt.nodes.get('Principled BSDF').inputs['Normal'])
glass = bpy.data.materials['Vidro levemente azul']
p = glass.node_tree.nodes.get('Principled BSDF')
p.inputs['Base Color'].default_value = (.86, .92, .96, 1)
p.inputs['Transmission Weight'].default_value = 1
p.inputs['Metallic'].default_value = 0
p.inputs['Roughness'].default_value = .09
p.inputs['IOR'].default_value = 1.45

def link(o, name):
    o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    C.objects.link(o)
    o['revision'] = 'evolucao_interiores_20261008'
    return o

def cube(name, loc, size, mat, bevel=0):
    x,y,z = [v / 2 for v in size]
    vs = [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    fs = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]
    mesh = bpy.data.meshes.new(name); mesh.from_pydata(vs,[],fs); mesh.update()
    o = bpy.data.objects.new(name, mesh); C.objects.link(o); o.location = loc
    mesh.materials.append(mat); o['revision'] = 'evolucao_interiores_20261008'
    if bevel:
        mod = o.modifiers.new('Acabamento das arestas', 'BEVEL'); mod.width = bevel; mod.segments = 2
    return o

def cyl(name, loc, r, depth, mat, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc)
    o = link(bpy.context.object,name); o.data.materials.append(mat)
    for f in o.data.polygons: f.use_smooth = len(f.vertices)==4
    return o

def sphere(name, loc, scale, mat, subdiv=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=1, location=loc)
    o = link(bpy.context.object,name); o.scale = scale; o.data.materials.append(mat)
    for f in o.data.polygons: f.use_smooth = True
    return o

def ring(name, x, y, z, r, tube, mat, n=32):
    vs=[]; fs=[]
    for i in range(n):
        a = math.tau*i/n
        for j in range(6):
            b = math.tau*j/6
            vs.append((x+(r+tube*math.cos(b))*math.cos(a),y+(r+tube*math.cos(b))*math.sin(a),z+tube*math.sin(b)))
    for i in range(n):
        for j in range(6): fs.append((i*6+j,((i+1)%n)*6+j,((i+1)%n)*6+(j+1)%6,i*6+(j+1)%6))
    m=bpy.data.meshes.new(name);m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new(name,m);C.objects.link(o);m.materials.append(mat)
    for p in m.polygons:p.use_smooth=True
    o['revision']='evolucao_interiores_20261008'
    return o

def chandelier(name, x, y, floor):
    ceiling = floor + 3.94
    ringz = floor + 3.13
    cyl(name+' canopla',(x,y,ceiling-.05),.16,.08,gold)
    cyl(name+' haste',(x,y,(ceiling+ringz)/2),.026,ceiling-ringz,gold,12)
    ring(name+' aro',x,y,ringz,.82,.028,gold)
    for j in range(8):
        a=math.tau*j/8;xx=x+.82*math.cos(a);yy=y+.82*math.sin(a)
        cyl(name+' suporte',(xx,yy,ringz-.12),.035,.24,gold,12)
        sphere(name+' difusor',(xx,yy,ringz-.29),(.10,.10,.14),led,2)
    bpy.ops.object.light_add(type='AREA', location=(x,y,ringz-.44))
    o=link(bpy.context.object,name+' iluminacao ampla');o.data.shape='DISK';o.data.size=3;o.data.energy=250;o.data.color=(1,.86,.67)

def panel_x(name,x,y,width,z,mat):
    cube(name+' fundo',(x,y,z+.57),(.045,width,1.10),mat,.008)
    for yy in [y-width/2+.08,y+width/2-.08]:cube(name+' montante',(x+.032,yy,z+.57),(.045,.035,.94),trim,.005)
    for zz in [z+.10,z+1.04]:cube(name+' travessa',(x+.032,y,zz),(.045,width-.16,.035),trim,.005)

# Salon: architectural mouldings and wall panels stop before the door opening.
for y in [-8.8,-6.7,-4.6,.6,2.7,4.8,6.9,8.9]:panel_x('Boiserie salao',-4.35,y,1.8,.7,ivory)
for a,b in [(-9.9,-3.2),(-.8,9.9)]:
    cube('Rodape salao',(-4.35,(a+b)/2,.80),(.09,b-a,.18),trim,.012)
cube('Cimalha interior salao',(-4.35,0,4.50),(.17,19.8,.15),trim,.015)
for x in [-12.95,-5.05]:cube('Moldura teto salao',(x,0,4.58),(.065,17.8,.055),gold,.008)
for y in [-8.9,8.9]:cube('Moldura teto salao',(-9,y,4.58),(7.9,.065,.055),gold,.008)
for y in [-5,1,7]:chandelier('Lustre salao',-9,y,.7)
for x,y in [(-9,-5),(-9,1),(-9,7)]:
    cyl('Bandeja centro banquete',(x,y,1.555),.20,.025,gold,24)
    cyl('Vaso centro banquete',(x,y,1.70),.08,.26,ivory,16)
    for j in range(5):
        a=j*math.tau/5
        sphere('Arranjo mesa',(x+.12*math.cos(a),y+.12*math.sin(a),1.97),(.15,.12,.13),leaves)

# Meeting room: darker lower wall, ceiling coffer framing and bronze lighting.
C=cols['03_ACABAMENTOS_CONSELHO']
for a,b in [(-13.8,-1.4),(1.4,13.8)]:
    cube('Lambril conselho',((a+b)/2,2.355,9.70),(b-a,.045,1.16),darkwood,.012)
    cube('Rodape conselho',((a+b)/2,2.31,9.21),(b-a,.07,.18),trim,.008)
    cube('Acabamento superior lambril',((a+b)/2,2.30,10.30),(b-a,.065,.07),gold,.006)
    count=int((b-a)/1.7)
    for j in range(count+1):cube('Pilastra lambril',(a+j*(b-a)/count,2.31,9.71),(.035,.06,1.02),gold,.005)
cube('Cimalha conselho',(0,2.31,12.91),(27.5,.17,.15),trim,.012)
for x in [-11,-5.5,0,5.5,11]:cube('Travessa teto conselho',(x,-3.8,12.97),(.12,9.0,.12),trim,.015)
for y in [-8.3,.7]:cube('Longarina teto conselho',(0,y,12.97),(22.0,.12,.12),trim,.015)
for x in [-5,0,5]:chandelier('Lustre conselho',x,-3.8,9.1)
for x in [-6,-4,-2,0,2,4,6]:
    cube('Base microfone',(x,-3.1,9.95),(.12,.10,.025),iron,.008)
    cyl('Haste microfone',(x,-3.1,10.07),.012,.24,iron,8)
    sphere('Capsula microfone',(x,-3.1,10.20),(.021,.03,.022),iron)
    cube('Bloco reuniao',(x,-3.0,9.98),(.28,.36,.015),ivory)
    cyl('Copo agua',(x+.34,-3.10,10.02),.032,.12,glass,12)

# Panel details and hardware on existing internal leaves, preserving the openings.
for door in list(before_objects):
    if door.type!='MESH' or 'porta aberta' not in door.name:continue
    C=cols['03_ACABAMENTOS_CONSELHO'] if door.location.z>8 else cols['01_ACABAMENTOS_SALAO']
    width=door.dimensions.x if abs(door.rotation_euler.z)<.2 else max(v.co.x for v in door.data.vertices)*2
    width=2*max(abs(v.co.x) for v in door.data.vertices)
    for face in [-1,1]:
        for zz in [-.7,.25]:
            p=door.matrix_world@Vector((0,face*.033,zz))
            o=cube('Almofada porta',p,(max(.2,width-.16),.012,.75),darkwood,.008);o.rotation_euler=door.rotation_euler.copy()
        p=door.matrix_world@Vector((width*.32,face*.08,-.35))
        o=cube('Macaneta bronze',p,(.14,.04,.032),gold,.012);o.rotation_euler=door.rotation_euler.copy()

# Replace only the placeholder topiary canopy in this independent revision.
C=cols['00_JARDIM_DETALHES']
for o in list(before_objects):
    if not o.name.startswith('Topiaria') or o.type!='MESH':continue
    x,y,z=o.location
    for dx,dy,dz,size in [(0,0,.25,.54),(-.25,.06,-.1,.43),(.25,-.05,-.1,.43),(0,0,-.43,.38)]:
        sphere('Topiaria copa detalhada',(x+dx,y+dy,z+dz),(size,size,size),leaves,2)
    o.hide_render=True;o.hide_set(True)
for x in [-3.6,3.6]:
    cyl('Balizador entrada',(x,-11.1,1.15),.065,.8,iron)
    cube('Lanterna entrada',(x,-11.1,1.64),(.22,.22,.30),gold,.018)
    cube('Lanterna difusor',(x,-11.215,1.64),(.15,.016,.23),led,.008)

s['design_stage']='Revisao de acabamentos: boiserie, lustres, materiais e ferragens; exportacao FiveM pendente'
s['source_model_sha256']=original_hash
s.render.resolution_x=1200;s.render.resolution_y=900;s.render.resolution_percentage=100
s.cycles.samples=32;s.cycles.use_denoising=True
bpy.ops.file.pack_all()
for o in bpy.data.objects:
    if o.type=='FONT':o.hide_render=True
s.camera=bpy.data.objects['CAM Fachada']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'castelo_rockford_evoluido.blend'))
print('EVOLUCAO_SAVED',flush=True)
for name,cam in [('exterior','CAM Fachada'),('salao','CAM Salao'),('reuniao','CAM Reuniao')]:
    s.camera=bpy.data.objects[cam];s.render.filepath=str(OUT/('castelo_'+name+'.png'))
    bpy.ops.render.render(write_still=True)
    print('RENDER_DONE',name,flush=True)
s.camera=bpy.data.objects['CAM Fachada']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'castelo_rockford_evoluido.blend'))
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==original_hash,'Original modified during independent revision'
stats={'source_unchanged':True,'source_sha256':original_hash,'objects_before':len(before_objects),'objects_after':len(bpy.data.objects),'triangles_before':before_triangles,'triangles_after':0,'installed_fivem':False,'changes':['Boiserie salao e conselho','Lustres bronze e difusores modelados','Molduras de teto','Veios madeira e trama linho','Vidro com transmissao corrigida','Almofadas e macanetas portas existentes','Arranjos mesas e microfones','Topiaria detalhada e balizadores']}
for o in bpy.data.objects:
    if o.type=='MESH':o.data.calc_loop_triangles();stats['triangles_after']+=len(o.data.loop_triangles)
(OUT/'evolucao.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False),encoding='utf-8')
print('EVOLUCAO_FINISHED',json.dumps(stats,ensure_ascii=False),flush=True)
