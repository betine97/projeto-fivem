"""Refina os modelos locais; sem editar qualquer imagem original."""
import bpy, math, random, json, importlib.util
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]

def blade(vs,fs,start,end,width,bend=.018):
    a=Vector(start);b=Vector(end);ax=b-a
    side=ax.cross(Vector((0,0,1)))
    if side.length<.001:side=Vector((1,0,0))
    side.normalize();offset=len(vs)
    for j in range(5):
        t=j/4;p=a.lerp(b,t)+Vector((0,0,bend*math.sin(t*math.pi)))
        r=width*math.sin(math.pi*t)**.75
        vs.extend([tuple(p-side*r),tuple(p+Vector((0,0,.008))),tuple(p+side*r)])
    for j in range(4):
        k=offset+j*3;fs.extend([(k,k+1,k+4,k+3),(k+1,k+2,k+5,k+4)])

def replace_mesh(o,vs,fs):
    mats=list(o.data.materials);me=bpy.data.meshes.new(o.name+'_detalhada');me.from_pydata(vs,[],fs);me.update()
    for m in mats:me.materials.append(m)
    old=o.data;o.data=me
    if old.users==0:bpy.data.meshes.remove(old)

def foliage():
    for o in list(bpy.data.objects):
        if o.type!='MESH':continue
        if o.name.startswith('Folha_tropical'):
            a=Vector(o.data.vertices[0].co);b=Vector(o.data.vertices[-1].co);ax=b-a
            side=ax.cross(Vector((0,0,1)))
            if side.length<.001:continue
            side.normalize();vs=[];fs=[]
            for j in range(1,16):
                t=j/17;p=a.lerp(b,t);length=ax.length*.24*math.sin(math.pi*t)**.7
                for s in (-1,1):blade(vs,fs,p,p+side*(s*length)+ax*.12+Vector((0,0,-length*.15)),length*.12)
            blade(vs,fs,a,b,.018);replace_mesh(o,vs,fs)
        elif o.name.startswith(('Folhagem_floreira','Ramo_pendente')):
            points=[v.co for v in o.data.vertices];cen=sum(points,Vector())/len(points);size=max((p-cen).length for p in points)
            vs=[];fs=[]
            for j in range(28):
                phi=j*2.399;z=1-2*(j+.5)/28;r=math.sqrt(max(0,1-z*z))
                end=cen+Vector((math.cos(phi)*r,math.sin(phi)*r,z))*(size*1.17)
                blade(vs,fs,cen,end,size*.16,bend=size*.12)
            replace_mesh(o,vs,fs)
        elif o.name.startswith(('Flor_floreira','Flor.')):
            points=[v.co for v in o.data.vertices];cen=sum(points,Vector())/len(points);size=max((p-cen).length for p in points)
            vs=[];fs=[]
            for j in range(5):
                a=j*math.tau/5;blade(vs,fs,cen,cen+Vector((math.cos(a)*size,math.sin(a)*size,size*.1)),size*.33,bend=size*.20)
            replace_mesh(o,vs,fs)

def weather_roof():
    for m in bpy.data.materials:
        if not m.name.startswith('Telhas_pixels_da_referencia'):continue
        nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
        if not bs or not bs.inputs['Base Color'].is_linked:continue
        source=bs.inputs['Base Color'].links[0].from_socket
        tex=nt.nodes.new('ShaderNodeTexCoord');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=27;noise.inputs['Detail'].default_value=5;noise.inputs['Roughness'].default_value=.72
        nt.links.new(tex.outputs['Object'],noise.inputs['Vector'])
        ramp=nt.nodes.new('ShaderNodeValToRGB');r=ramp.color_ramp
        r.elements[0].position=.23;r.elements[0].color=(.13,.10,.07,1);r.elements[1].position=.72;r.elements[1].color=(1,.91,.75,1)
        nt.links.new(noise.outputs['Fac'],ramp.inputs[0]);mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.70
        nt.links.new(source,mix.inputs[1]);nt.links.new(ramp.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],bs.inputs['Base Color'])
        fine=nt.nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=190;fine.inputs['Detail'].default_value=3
        nt.links.new(tex.outputs['Object'],fine.inputs['Vector']);bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.3;bump.inputs['Distance'].default_value=.025
        nt.links.new(fine.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],bs.inputs['Normal'])

def apply_polish(mod):
    spec=importlib.util.spec_from_file_location('passagens',ROOT/'scripts'/'conferir_passagens.py');access=importlib.util.module_from_spec(spec);spec.loader.exec_module(access);access.correct_geometry(mod)
    sc=bpy.context.scene
    if sc.get('refinamento_aplicado'):return
    random.seed(9010+mod.BUILDID)
    for o in bpy.data.objects:
        if o.name.startswith(('Letreiro_','Cruz_farmacia')):o.location.y-=.20
        if o.type=='LIGHT' and o.name.startswith('Luz_interior'):o.data.energy=650 if mod.C.get('loja') else 170
    glass=bpy.data.materials.get('Vidro')
    if glass:
        bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.82,.89,.88,1);bs.inputs['Transmission Weight'].default_value=.98;bs.inputs['Roughness'].default_value=.08
    weather_roof();foliage()
    # Raise produce onto real display stands, rather than leaving crates on ground.
    if mod.BUILDID in (6,8):
        for o in mod.COL.get('Esquadrias',()).objects:
            if o.name.startswith('Caixote_'):o.location.z+=.67
            elif o.name.startswith('Fruta'):
                for v in o.data.vertices:v.co.z+=.67
        for x in (-mod.C['w']*.30,-mod.C['w']*.07,mod.C['w']*.28):
            y=-mod.C['d']/2-.22
            mod.box('Banca_frutas_tampo',(x,y,.66),(.94,.71,.08),mod.M['Madeira'],'Esquadrias')
            for dx in (-.37,.37):
                for dy in (-.23,.23):mod.box('Banca_frutas_pe',(x+dx,y+dy,.33),(.065,.065,.66),mod.M['Madeira'],'Esquadrias')
    if mod.BUILDID in (4,8):
        flower=bpy.data.materials.get('Flor')
        if flower:flower.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.87,.85,.66,1)
    sc['refinamento_aplicado']=True

def update():
    spec=importlib.util.spec_from_file_location('modelagem',ROOT/'scripts'/'modelar_estruturas.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for path in sorted((ROOT/'modelos').glob('[0-9][0-9]_*.blend')):
        bpy.ops.wm.open_mainfile(filepath=str(path));id=int(path.stem[:2]);mod.BUILDID=id;mod.C=dict(mod.CFG[id]);mod.C.update(story=3.2,H=mod.C.get('h',mod.C['n']*3.2))
        mod.COL={c.name:c for c in bpy.data.collections};mod.M={m.name:m for m in bpy.data.materials};mod.MATCACHE={}
        apply_polish(mod);mod.camera();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
        mod.render(ROOT/'previews'/f'{id:02}_exterior.png');mod.render(ROOT/'previews'/f'{id:02}_interior.png',True)
        jf=ROOT/'dados'/f'{id:02}_modelo.json';data=json.loads(jf.read_text(encoding='utf-8'));data['refinamento_aplicado']=True;jf.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        print('REFINADO',id,flush=True)
    print('REFINAMENTO_CONCLUIDO',flush=True)

if __name__=='__main__':update()
