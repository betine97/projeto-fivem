import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parent

def image_material(name, roughness, tint=None):
    m=bpy.data.materials.new('STAGE12_'+name);m.use_nodes=True
    t=m.node_tree;p=t.nodes.get('Principled BSDF')
    im=t.nodes.new('ShaderNodeTexImage');im.image=bpy.data.images.load(str(BASE/'texturas_plantas'/(name+'.png')),check_existing=True)
    color=im.outputs['Color']
    if tint:
        mix=t.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*tint,1)
        t.links.new(color,mix.inputs[1]);color=mix.outputs[0]
    t.links.new(color,p.inputs['Base Color']);p.inputs['Roughness'].default_value=roughness
    bump=t.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.17;bump.inputs['Distance'].default_value=.0007
    t.links.new(im.outputs['Color'],bump.inputs['Height']);t.links.new(bump.outputs[0],p.inputs['Normal'])
    if name=='folha':p.inputs['Subsurface Weight'].default_value=.06
    m.diffuse_color=(.075,.19,.025,1) if name in ('folha','caule') else (.09,.075,.045,1)
    return m

class Mesh:
    def __init__(self):self.v=[];self.f=[];self.uv=[];self.mi=[]
    def vert(self,co,uv=(0,0)):
        self.v.append(tuple(co));self.uv.append(uv);return len(self.v)-1
    def face(self,vs,mat):self.f.append(vs);self.mi.append(mat)
    def tube(self,a,b,r1,r2,mat=0,n=6):
        a,b=Vector(a),Vector(b);d=(b-a).normalized();x=d.cross(Vector((0,0,1)))
        if x.length<.001:x=d.cross(Vector((0,1,0)))
        x.normalize();y=d.cross(x);rings=[]
        for c,r,v in ((a,r1,0),(b,r2,1)):
            rings.append([self.vert(c+r*(math.cos(i*2*math.pi/n)*x+math.sin(i*2*math.pi/n)*y),(i/n,v)) for i in range(n+1)])
        for i in range(n):self.face((rings[0][i],rings[0][i+1],rings[1][i+1],rings[1][i]),mat)
    def oval(self,c,rx,ry,rz,mat=2,n=7,k=5):
        c=Vector(c);rings=[]
        for j in range(k+1):
            a=math.pi*j/k
            rings.append([self.vert(c+Vector((rx*math.sin(a)*math.cos(i*2*math.pi/n),ry*math.sin(a)*math.sin(i*2*math.pi/n),rz*math.cos(a))),(i/n,j/k)) for i in range(n+1)])
        for j in range(k):
            for i in range(n):self.face((rings[j][i],rings[j][i+1],rings[j+1][i+1],rings[j+1][i]),mat)
    def build(self,name,col,mats):
        data=bpy.data.meshes.new(name);data.from_pydata(self.v,[],self.f);data.update()
        obj=bpy.data.objects.new(name,data);col.objects.link(obj)
        for m in mats:data.materials.append(m)
        uv=data.uv_layers.new(name='PlantUV')
        for p,mi in zip(data.polygons,self.mi):
            p.material_index=mi;p.use_smooth=True
            for li in p.loop_indices:uv.data[li].uv=self.uv[data.loops[li].vertex_index]
        return obj

def leaflet(mesh,origin,theta,length,width,rng):
    d=Vector((math.cos(theta),math.sin(theta),0));side=Vector((-d.y,d.x,0));rows=[];centers=[]
    bend=rng.uniform(.14,.28);tilt=rng.uniform(-.1,.28)
    for i in range(21):
        t=i/20;c=origin+d*(length*t)+Vector((0,0,length*(tilt*t-bend*t*t)))
        centers.append(c);w=width*(math.sin(math.pi*t)**.85)*(1 if i%2==0 else .72)
        rows.append([mesh.vert(c+side*w*s+Vector((0,0,-abs(s)*.008*math.sin(math.pi*t))),((s+1)/2,t)) for s in (-1,0,1)])
    for j in range(20):
        for k in range(2):mesh.face((rows[j][k],rows[j][k+1],rows[j+1][k+1],rows[j+1][k]),1)
    for j in range(0,20,4):mesh.tube(centers[j]+Vector((0,0,.0007)),centers[min(j+4,20)]+Vector((0,0,.0007)),.0007,.0003,3,4)

def fan(mesh,c,theta,size,rng):
    origin=c+Vector((math.cos(theta)*.035,math.sin(theta)*.035,.003))
    mesh.tube(c,origin,.0015,.001,0)
    for i in range(-2,3):
        length=size*(1-.20*abs(i))*rng.uniform(.91,1.07)
        leaflet(mesh,origin,theta+i*.48,length,length*.15,rng)

def bud(mesh,base,size,rng):
    # Lobed flower clusters, tapered toward the tip; decorative geometry only.
    for j in range(8):
        t=j/7;r=size*.26*(1-.70*t);z=size*t
        for k in range(5):
            a=k*2*math.pi/5+j*1.2+rng.uniform(-.35,.35)
            c=base+Vector((r*.65*math.cos(a),r*.65*math.sin(a),z+rng.uniform(-.03,.03)*size))
            mesh.oval(c,r*rng.uniform(.5,.75),r*rng.uniform(.5,.75),size*rng.uniform(.10,.15),2)
            if k%2==0:
                end=c+Vector((math.cos(a)*r,math.sin(a)*r,size*.08))
                mesh.tube(c,end,.0009,.0002,4,4)
        if j%2==0:
            for k in range(3):leaflet(mesh,base+Vector((0,0,z)),k*2.094+j,size*.42,size*.035,rng)

def plant(name,height,seed,col,mats):
    rng=random.Random(seed);mesh=Mesh()
    axis=[Vector((.012*math.sin(i*.8),.012*math.cos(i*.7),height*i/10*.90)) for i in range(11)]
    for i in range(10):mesh.tube(axis[i],axis[i+1],.010*(1-i*.075),.010*(1-(i+1)*.075),0,8)
    # Six alternate flowering branches and a main top.
    for j in range(6):
        theta=j*2.399+rng.uniform(-.16,.16);start=Vector((0,0,height*(.16+.062*j)))
        tipheight=height*(.56+.055*j);reach=.18 if j<4 else .14
        end=Vector((math.cos(theta)*reach,math.sin(theta)*reach,tipheight))
        mid=start.lerp(end,.50)+Vector((0,0,-.045));mesh.tube(start,mid,.0055,.0035);mesh.tube(mid,end,.0035,.0018)
        for k,t in enumerate((.36,.65,.88)):
            c=mid.lerp(end,t) if t>.5 else start.lerp(mid,t*2)
            fan(mesh,c,theta+(-.45 if k%2 else .4),.21*(1-.12*j/6),rng)
            fan(mesh,c,theta+1.65,.17,rng)
        bud(mesh,end,height*(.14 if j<3 else .125),rng)
    for j in range(3):
        angle=j*2.094+.6;start=Vector((0,0,height*.10));end=Vector((.17*math.cos(angle),.17*math.sin(angle),height*.36))
        mesh.tube(start,end,.004,.0018)
        for t in (.45,.75,1.0):
            fan(mesh,start.lerp(end,t),angle+.3,.23,rng)
            fan(mesh,start.lerp(end,t),angle+2.0,.18,rng)
    for j in range(8):
        c=Vector((0,0,height*(.22+j*.085)));angle=j*2.4
        for a in (angle,angle+2.094,angle+4.188):fan(mesh,c,a,.245*(1-j*.075),rng)
    bud(mesh,axis[-1]-Vector((0,0,.035)),height*.135,rng)
    return mesh.build(name,col,mats)

def apply():
    mats=[image_material('caule',.75,(.60,.74,.38)),image_material('folha',.67,(.50,.65,.30)),image_material('flor',.82,(.42,.62,.28))]
    for name,color in [('nervuras',(.20,.30,.055,1)),('pistilos',(.48,.22,.055,1))]:
        m=bpy.data.materials.new('STAGE12_'+name);m.diffuse_color=color;m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=color;mats.append(m)
    potmat=image_material('vaso',.68);soilmat=image_material('solo',.96)
    col=bpy.data.collections.get('ENV_PLANT_PLACEHOLDERS')
    pots=sorted([o for o in bpy.data.objects if o.name.startswith('PLACEHOLDER_') and o.name.endswith('_POT')],key=lambda o:o.name)
    assert len(pots)==18,len(pots)
    report=[]
    for i,pot in enumerate(pots):
        prefix=pot.name[:-4];old=bpy.data.objects.get(prefix+'_CANOPY')
        oldmax=max((old.matrix_world@Vector(c)).z for c in old.bound_box) if old else None
        for suffix in ('_STEM','_CANOPY'):
            o=bpy.data.objects.get(prefix+suffix)
            if o:bpy.data.objects.remove(o,do_unlink=True)
        for suffix in ('_POT','_RIM','_FILL'):
            o=bpy.data.objects[prefix+suffix];o.data.materials.clear();o.data.materials.append(soilmat if suffix=='_FILL' else potmat)
            if o.type=='MESH':
                for p in o.data.polygons:p.material_index=0
                if suffix=='_FILL':
                    uv=o.data.uv_layers.active or o.data.uv_layers.new()
                    radius=max(v.co.xy.length for v in o.data.vertices)
                    for p in o.data.polygons:
                        for li in p.loop_indices:
                            v=o.data.vertices[o.data.loops[li].vertex_index].co
                            uv.data[li].uv=(.5+v.x/(2*radius),.5+v.y/(2*radius))
            elif o.type=='CURVE':
                for s in o.data.splines:s.material_index=0
        soil=bpy.data.objects[prefix+'_FILL'];surface=soil.location.z+.004
        h=1.04+(i%3)*.017
        obj=plant(prefix+'_PLANT',h,101+i,col,mats);obj.location=(pot.location.x,pot.location.y,surface)
        # Slender molded ribs on the existing pot, preserving its height and diameter.
        ribs=Mesh()
        for k in range(12):
            a=k*2*math.pi/12
            ribs.tube((.171*math.cos(a),.171*math.sin(a),-.19),(.225*math.cos(a),.225*math.sin(a),.17),.004,.004,0,5)
        ribobj=ribs.build(prefix+'_POT_RIBS',col,[potmat]);ribobj.location=pot.location
        newmax=max((obj.matrix_world@Vector(c)).z for c in obj.bound_box)
        bpy.context.view_layer.update();newmax=max((obj.matrix_world@Vector(c)).z for c in obj.bound_box)
        assert newmax<1.84,(prefix,newmax)
        assert oldmax is None or newmax>oldmax+.15
        report.append({'plant':obj.name,'old_top_m':oldmax,'new_top_m':newmax,'vegetation_height_m':newmax-surface,'pot_height_m':pot.dimensions.z})
    for im in bpy.data.images:
        if im.source=='FILE' and im.filepath:im.pack()
    return report

if __name__=='__main__':
    bpy.ops.wm.open_mainfile(filepath=str(BASE/'warehouse_stage11_ventiladores.blend'))
    report=apply()
    bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'warehouse_stage12_plantas.blend'))
    (BASE/'warehouse_stage12_validacao.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('STAGE12 OK',len(report))
