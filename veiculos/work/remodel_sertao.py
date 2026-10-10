"""Geometry rebuild, executed in the vehicle builder namespace before export."""
import bmesh
from mathutils import Matrix

bodytex=image_material('MILITARY_OLIVE_BODY',ref_temp/'codex-clipboard-eb3a04d3-8cfb-4ed2-94d7-2ab42dec1b96.png')
rubber=material('RUBBER_OFFROAD',(.045,.041,.034))
dust=material('RUBBER_DUST',(.095,.082,.059))
edge=material('EXPOSED_EDGE',(.24,.22,.16))
darksteel=grille_tex
olive=bodytex
metal=darksteel

def planar_uv(mesh, slots=None, density=.68):
    """World-scale box projection: one repeat per 1.47 m, shared by all panels."""
    uv=mesh.uv_layers.get('UVMap 0') or mesh.uv_layers.new(name='UVMap 0')
    for p in mesh.polygons:
        if slots is not None and p.material_index not in slots:continue
        axis=max(range(3),key=lambda k:abs(p.normal[k]))
        axes=[k for k in range(3) if k!=axis]
        for li in p.loop_indices:
            co=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(co[axes[0]]*density+.137,co[axes[1]]*density+.271)

def remove_obj(o):
    if o in parts:parts.remove(o)
    bpy.data.objects.remove(o,do_unlink=True)

# Replace the old overlay geometry and native front panels, retaining the rig.
prefixes=('Capo angular','Grade base','Grade horizontal','Aro farol','Farol circular','Seta dianteira',
          'Para choque','Protecao grade','Barra frontal','Trilho cacamba','Nervura lateral',
          'Painel traseiro','Gancho carga','Base pedestal','Coluna pedestal','Escora pedestal',
          'Anel giro','Camisa perfurada','Perfuracao visual','Cano','Freio boca','Interior boca','Ranhura boca')
for o in list(bpy.data.objects):
    if o.type!='MESH':continue
    if o.name.startswith(prefixes) or o.name in ('bonnet','wing_lf','wing_rf','bumper_f','boot','headlight_l','headlight_r'):
        remove_obj(o)

# Existing glass, opening doors, seats, dashboard, wheel bones and collisions stay native.
seen=set()
for o in list(bpy.data.objects):
    if o.type!='MESH' or o.sollum_type!='sollumz_drawable_model':continue
    for level in LODLevel:
        mesh=o.sz_lods.get_lod(level).mesh
        if mesh is None or mesh.name in seen:continue
        seen.add(mesh.name)
        if o.name=='bodyshell':
            bm=bmesh.new();bm.from_mesh(mesh)
            obsolete=[f for f in bm.faces if all(v.co.y<-.44 for v in f.verts) or all(v.co.y>2.20 for v in f.verts)
                      or 'badges' in (mesh.materials[f.material_index].name if mesh.materials[f.material_index] else '')]
            bmesh.ops.delete(bm,geom=obsolete,context='FACES');bm.to_mesh(mesh);bm.free()
        slots=[]
        for i,m in enumerate(mesh.materials):
            if m and (m==ammo_tex or m.name.startswith('sertao_olive') or '[PRIMARY]' in m.name):
                mesh.materials[i]=bodytex;slots.append(i)
            elif m and m.name=='sertao_steel':mesh.materials[i]=darksteel;slots.append(i)
        planar_uv(mesh,slots)

def poly(name,verts,faces,mat=bodytex,bone='chassis',bevel=.008):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    return finish(o,name,mat,bone,bevel)

def path(name,points,r,mat=darksteel,bone='chassis',closed=False):
    for i in range(len(points) if closed else len(points)-1):
        cylinder(name,points[i],points[(i+1)%len(points)],r,mat,bone,12)

# Shaped, gently crowned bonnet with rolled shoulders and longitudinal pressings.
verts=[]
xs=[-.755,-.72,-.56,0,.56,.72,.755]
ys=[1.15,1.22,2.19,2.30]
for y in ys:
    for x in xs:
        crown=.047*(1-(abs(x)/.755)**4)
        verts.append((x,y,.773+crown-.028*(y-1.15)))
faces=[]
for j in range(3):
    for i in range(6):a=j*7+i;faces.append((a,a+1,a+8,a+7))
hood=poly('HOOD',verts,faces,bone='bonnet',bevel=0)
bpy.context.view_layer.objects.active=hood
s=hood.modifiers.new('Pressed steel thickness','SOLIDIFY');s.thickness=.025;bpy.ops.object.modifier_apply(modifier=s.name)
for x in [-.48,.48]:
    cylinder('HOOD_PRESSING',(x,1.26,.818),(x,2.18,.793),.013,bodytex,'bonnet',12)
for x in [-.758,.758]:cylinder('HOOD_PANEL_GAP',(x,1.17,.767),(x,2.30,.741),.006,black,'bonnet',8)

# Follow the rounded native roof precisely: no floating overlay panel.
cab=bpy.data.objects['bodyshell']
for x in [-.43,-.22,.22,.43]:
    points=[]
    for i in range(10):
        y=-.22+i*.078
        hit,co,normal,face=cab.ray_cast(Vector((x,y,2)),Vector((0,0,-1)))
        if hit:points.append((x,y,co.z+.002))
    path('ROOF_PRESSING',points,.004,bodytex)
for side in [-1,1]:
    bone='door_dside_f' if side<0 else 'door_pside_f'
    box('DOOR_HANDLE_'+str(side),(side*.841,.15,.696),(.022,.145,.027),edge,bone,.008)
    box('DOOR_HANDLE_RECESS',(side*.834,.15,.690),(.020,.179,.056),black,bone,.010)
    cylinder('MIRROR_ARM',(side*.80,.92,.82),(side*.98,.86,.89),.012,darksteel,bone,12)
    box('SIDE_MIRROR_'+str(side),(side*.987,.87,.97),(.064,.13,.215),bodytex,bone,.018)
    box('MIRROR_GLASS',(side*.988,.800,.975),(.045,.008,.177),silver,bone,.008)
    for y in [.23,.88]:box('DOOR_HINGE',(side*.842,y,.47),(.023,.052,.062),bodytex,bone,.006)
    for z in [.36,.385,.41,.435]:box('CAB_VENT',(side*.842,-.36,z),(.01,.16,.009),black,bevel=.003)

# Wheel openings: continuous extruded sheet surfaces with a rolled arch lip.
def side_panel(name,side,ymin,ymax,cy,top,bone='chassis'):
    zc=-.133;radius=.535
    profile=[(ymin,.04)]
    for i in range(13):
        angle=math.pi-i*math.pi/12
        y=cy+radius*math.cos(angle);z=zc+radius*math.sin(angle)
        if ymin<y<ymax:profile.append((y,max(.04,z)))
    profile.append((ymax,.04));profile.sort()
    verts=[]
    for y,z in profile:verts.extend([(side*.855,y,z),(side*.855,y,top)])
    faces=[(2*i,2*i+2,2*i+3,2*i+1) for i in range(len(profile)-1)]
    panel=poly(name,verts,faces,bone=bone)
    bpy.context.view_layer.objects.active=panel
    m=panel.modifiers.new('Sheet metal thickness','SOLIDIFY');m.thickness=.027;bpy.ops.object.modifier_apply(modifier=m.name)
    lip=[]
    for y,z in profile:
        lip.extend([(side*.854,y,z+.010),(side*.931,y,z+.022),(side*.947,y,z+.050),(side*.883,y,z+.080)])
    faces=[]
    for i in range(len(profile)-1):
        for j in range(3):a=i*4+j;faces.append((a,a+4,a+5,a+1))
    poly(name+'_ROLLED_ARCH',lip,faces,bone=bone,bevel=.006)
for side in [-1,1]:
    side_panel('FRONT_FENDER',side,1.10,2.30,1.641,.75,'wing_lf' if side<0 else 'wing_rf')
    side_panel('BED_SIDE_'+str(side),side,-2.42,-.44,-1.307,.85)
    box('FENDER_SHOULDER',(side*.802,1.69,.749),(.108,1.23,.051),bodytex,bevel=.018)
    box('BED_TOP_RAIL',(side*.851,-1.43,.858),(.088,2.03,.052),bodytex,bevel=.014)
    box('BED_INNER_WALL',(side*.811,-1.43,.611),(.028,1.98,.44),bodytex)
    for y in [-.60,-.95,-1.80,-2.23]:
        box('BED_INNER_PRESSING',(side*.787,y,.62),(.026,.045,.39),bodytex)
        cylinder('BED_TIE_DOWN',(side*.899,y,.82),(side*.899,y,.775),.011,darksteel,vertices=10)
    # Lower seam and road grime strip, placed where wear actually accumulates.
    path('BED_PANEL_CREASE',[(side*.879,-2.4,.48),(side*.879,-.47,.48)],.006,edge)
box('BED_FLOOR',(0,-1.43,.355),(1.60,1.96,.042),bodytex)
for x in [i*.105 for i in range(-7,8)]:box('BED_FLOOR_RIB',(x,-1.43,.386),(.035,1.91,.021),bodytex,bevel=.008)
box('BED_FRONT_WALL',(0,-.446,.59),(1.67,.040,.48),bodytex)
box('TAILGATE',(0,-2.424,.604),(1.67,.055,.49),bodytex,'boot',.012)
box('TAILGATE_TOP',(0,-2.424,.855),(1.75,.085,.052),bodytex,'boot')
for z in [.46,.72]:box('TAILGATE_PRESSING',(0,-2.461,z),(1.48,.012,.015),bodytex,'boot',.005)
for x in [-.58,.58]:
    cylinder('TAILGATE_HINGE',(x-.07,-2.465,.386),(x+.07,-2.465,.386),.022,darksteel,'boot',12)
    box('TAILGATE_LATCH',(x,-2.461,.775),(.08,.015,.04),darksteel,'boot')

# Recessed grille, separate headlamp buckets and rounded steel bumper.
box('FRONT_GRILLE',(0,2.313,.525),(1.65,.070,.428),black,bevel=.018)
for z in [.36,.43,.50,.57,.64,.705]:box('GRILLE_HORIZONTAL',(0,2.365,z),(1.06,.036,.026),darksteel,bevel=.009)
for side in [-1,1]:
    x=side*.652
    box('HEADLIGHT_BUCKET',(x,2.344,.526),(.319,.067,.369),darksteel,bevel=.023)
    cylinder('HEADLIGHT_BEZEL',(x,2.37,.526),(x,2.406,.526),.147,edge,vertices=40)
    cylinder('HEADLIGHT_'+('L' if side<0 else 'R'),(x,2.405,.526),(x,2.42,.526),.132,lamp_tex,vertices=40)
    box('INDICATOR_HOUSING',(side*.831,2.302,.563),(.107,.084,.225),darksteel,bevel=.010)
    box('INDICATOR_AMBER',(side*.831,2.35,.603),(.090,.014,.093),amber,bevel=.008)
    box('INDICATOR_WHITE',(side*.831,2.35,.502),(.090,.014,.07),lamp,bevel=.007)
box('FRONT_BUMPER',(0,2.447,.198),(1.90,.19,.19),darksteel,bevel=.032)
box('BUMPER_PLATE',(0,2.548,.218),(.37,.009,.10),black,bevel=.008)
path('BULL_BAR',[(-.87,2.477,.23),(-.87,2.477,.47),(-.80,2.477,.57),(.80,2.477,.57),(.87,2.477,.47),(.87,2.477,.23)],.030)
for side in [-1,1]:
    x=side*.56
    box('TOW_MOUNT',(x,2.563,.20),(.10,.045,.13),darksteel)
    points=[(x+.064*math.cos(t*math.tau/16),2.60,.13+.078*math.sin(t*math.tau/16)) for t in range(16)]
    path('TOW_HOOK_'+str(side),points,.015,edge,closed=True)
box('REAR_BUMPER',(0,-2.494,.167),(1.89,.14,.16),darksteel,bevel=.025)

# Cylindrical pedestal and triangular braces, retaining runtime pivot positions.
box('GUN_BASE_PLATE',(0,-1.15,.419),(.50,.54,.055),darksteel)
cylinder('GUN_PEDESTAL',(0,-1.15,.444),(0,-1.15,1.30),.089,bodytex,vertices=32)
for z,r in [(.465,.139),(1.255,.144),(1.302,.154)]:
    cylinder('GUN_FLANGE',(0,-1.15,z),(0,-1.15,z+.030),r,darksteel,vertices=32)
    for i in range(8):
        x=math.cos(i*math.tau/8)*r*.78;y=-1.15+math.sin(i*math.tau/8)*r*.78
        cylinder('FLANGE_BOLT',(x,y,z+.03),(x,y,z+.043),.010,edge,vertices=6)
for x,y in [(-.34,-1.65),(.34,-1.65),(0,-.65)]:
    cylinder('SUPPORT_ARM',(x,y,.414),(0,-1.15,1.16),.031,bodytex,vertices=16)
    box('SUPPORT_FOOT',(x,y,.415),(.14,.15,.025),darksteel)
for x in [-.196,.196]:
    for y in [-1.35,-.95]:cylinder('BASE_BOLT',(x,y,.451),(x,y,.470),.017,edge,vertices=6)

# Actual holes in the barrel jacket instead of dark circles painted on a tube.
cylinder('BARREL_SHROUD',(0,-.80,1.68),(0,-.39,1.68),.073,darksteel,pitch,32)
jacket=parts[-1]
for y in [-.73,-.61,-.49]:
    for direction in ['X','Z']:
        bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.025,depth=.22,location=(0,y,1.68))
        cutter=bpy.context.object
        if direction=='X':cutter.rotation_euler[1]=math.pi/2
        bpy.context.view_layer.objects.active=jacket
        mod=jacket.modifiers.new('Ventilation aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
        bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
jacket.vertex_groups[pitch].add(list(range(len(jacket.data.vertices))),1,'REPLACE')
cylinder('BARREL',(0,-.77,1.68),(0,.84,1.68),.027,darksteel,pitch,24)
cylinder('MUZZLE_BRAKE',(0,.80,1.68),(0,.97,1.68),.045,darksteel,pitch,24)
cylinder('MUZZLE_BORE',(0,.971,1.68),(0,.974,1.68),.027,black,pitch,24)
for y in [.84,.90,.95]:
    for s in [-1,1]:box('MUZZLE_SLOT',(s*.044,y,1.68),(.004,.026,.022),black,pitch,.002)
for s in [-1,1]:
    box('RECEIVER_SIDE_RAIL',(s*.115,-1.18,1.705),(.014,.69,.020),darksteel,pitch,.004)
    cylinder('RECEIVER_CHARGING_HANDLE',(s*.12,-1.30,1.63),(s*.19,-1.30,1.63),.015,darksteel,pitch,12)
for y in [-1.24,-.93]:box('AMMO_BOX_LATCH',(-.476,y,1.49),(.012,.055,.072),darksteel,pitch,.004)
path('AMMO_BOX_HANDLE',[(-.473,-1.18,1.43),(-.497,-1.18,1.47),(-.497,-1.00,1.47),(-.473,-1.00,1.43)],.008,darksteel,pitch)

# Custom wheel mesh replaces the complete donor wheel at every LOD. No chrome rim.
wheel=bpy.data.objects['wheel_lf.child']
wheelpieces=[]
def wheel_lathe(name,profile,mat,segments=48):
    vs=[];fs=[]
    for x,r in profile:
        vs.extend([(x,r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments)) for i in range(segments)])
    for j in range(len(profile)-1):
        for i in range(segments):a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
    o=poly(name,vs,fs,mat,bevel=0);wheelpieces.append(o);return o
wheel_lathe('TYRE_CARCASS',[(-.177,.255),(-.185,.30),(-.174,.393),(-.143,.445),(-.105,.455),(.105,.455),(.143,.445),(.174,.393),(.185,.30),(.177,.255)],rubber)
for side in [-1,1]:
    wheel_lathe('STEEL_RIM_OLIVE',[(side*.181,.259),(side*.187,.247),(side*.162,.230),(side*.128,.20),(side*.114,.105),(side*.167,.083),(side*.17,.0)],bodytex)
    wheel_lathe('RIM_ROLLED_LIP',[(side*.174,.255),(side*.188,.257),(side*.191,.25),(side*.174,.247)],edge)
    for i in range(6):
        t=i*math.tau/6;y=.108*math.cos(t);z=.108*math.sin(t)
        o=cylinder('WHEEL_LUG',(side*.137,y,z),(side*.162,y,z),.016,darksteel,vertices=6);wheelpieces.append(o)
    for i in range(10):
        t=i*math.tau/10;y=.202*math.cos(t);z=.202*math.sin(t)
        o=cylinder('RIM_VENT',(side*.162,y,z),(side*.166,y,z),.020,black,vertices=12);wheelpieces.append(o)
    wheel_lathe('HUB',[(side*.171,.070),(side*.192,.070),(side*.199,.055),(side*.199,0)],darksteel,24)
for row,x in enumerate([-.118,-.040,.040,.118]):
    for i in range(32):
        t=(i+(row%2)*.47)*math.tau/32
        o=box('TREAD_BLOCK',(x,.456*math.cos(t),.456*math.sin(t)),(.073,.077,.041),dust if i%9==0 else rubber,bevel=.005)
        # Local block z is radial, tangent along y.
        transform=Matrix.Translation(Vector((x,.456*math.cos(t),.456*math.sin(t)))) @ Matrix.Rotation(t-math.pi/2,4,'X')
        # box has baked translation; rotate around its own centre.
        c=Vector((x,.456*math.cos(t),.456*math.sin(t)))
        o.data.transform(Matrix.Translation(c)@Matrix.Rotation(t-math.pi/2,4,'X')@Matrix.Translation(-c))
        wheelpieces.append(o)
# Assemble in local wheel coordinates and preserve native COPY_TRANSFORMS constraint.
bpy.ops.object.select_all(action='DESELECT')
parts[:]=[o for o in parts if o not in wheelpieces]
for o in wheelpieces:o.select_set(True);o.modifiers.clear();o.vertex_groups.clear()
bpy.context.view_layer.objects.active=wheelpieces[0]
bpy.ops.object.join();combined=bpy.context.object
newmesh=combined.data.copy();newmesh.name='SERTAO_OFFROAD_WHEEL'
planar_uv(newmesh)
for i,m in enumerate(newmesh.materials):
    native=native_tyre.copy();native.name='SERTAO_WHEEL_'+m.name
    native.node_tree.nodes['DiffuseSampler'].image=m.node_tree.nodes['DiffuseSampler'].image
    native.node_tree.nodes['DiffuseSampler'].texture_properties.embedded=True
    newmesh.materials[i]=native
mesh_add_missing_uv_maps(newmesh)
if newmesh.uv_layers.get('UVMap 1'):
    for a,b in zip(newmesh.uv_layers['UVMap 0'].data,newmesh.uv_layers['UVMap 1'].data):b.uv=a.uv
for level in [LODLevel.VERYHIGH,LODLevel.HIGH,LODLevel.MEDIUM,LODLevel.LOW]:wheel.sz_lods.get_lod(level).mesh=newmesh
wheel.data=newmesh
bpy.data.objects.remove(combined,do_unlink=True)
# Rebuild list from actual custom objects after mesh joins.
parts[:]=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==drawable and o!=wheel and any(g.name in {'chassis','bonnet','boot','wing_lf','wing_rf','door_dside_f','door_pside_f','sertao_turret_yaw','sertao_turret_pitch'} for g in o.vertex_groups) and o.name not in {'chassis','door_dside_f','door_pside_f','transmission_r','transmission_f'}]
for o in parts:
    if o.data.materials and o.data.materials[0]!=lamp_tex and o.data.materials[0]!=round_tex:
        planar_uv(o.data)
    if o.data.materials and o.data.materials[0]==lamp_tex:
        cx=sum(v.co.x for v in o.data.vertices)/len(o.data.vertices)
        for loop in o.data.loops:
            co=o.data.vertices[loop.vertex_index].co
            o.data.uv_layers['UVMap 0'].data[loop.index].uv=((co.x-cx)/.280+.5,(co.z-.526)/.280+.5)
    for p in o.data.polygons:
        if len(p.vertices)==4 and 'BARREL' in o.name:p.use_smooth=True
rig['revision']='geometry-rebuild-02';rig['body_texture']='user image 3';rig['uv_density_m']=1/.68
for mesh in bpy.data.meshes:
    for i,m in enumerate(mesh.materials):
        if m is None:mesh.materials[i]=black
print('REMODEL_COMPLETE',len(parts),'parts',len(newmesh.polygons),'wheel faces')
