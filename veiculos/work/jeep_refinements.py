# Runs in build_jeep.py after the imported objects have been removed.
# The wheel rim occupies this isolated volume behind the dashboard.
steering_ids=[]
for v in body.data.vertices:
 x,y,z=v.co
 if -.65<x<-.10 and -.20<y<.16 and .60<z<1.01:
  v.co=Vector((-.37,-.025,.63))+(v.co-Vector((-.37,0,.80)))*.72
  steering_ids.append(v.index)
assert len(steering_ids)>30, 'Steering wheel selection unexpectedly empty'
body.data.update()
# Keep the original column connection; the mesh is not cut at the dashboard.
print('STEERING_REFINED',len(steering_ids),'scale=0.72 lowered=0.17m')

def solid_dds(name,color):
 path=out/(name+'.dds')
 header=[124,0x100f,4,4,16,0,0]+[0]*11+[32,0x41,0,32,0xff,0xff00,0xff0000,0xff000000]+[0x1000,0,0,0,0]
 path.write_bytes(b'DDS '+struct.pack('<31I',*header)+bytes(color)*16)
 im=bpy.data.images.load(str(path),check_existing=True);im.pack();return im

mirror=create_shader('vehicle_mesh.sps');mirror.name='JEEP_MIRROR_GTA_REFLECTIVE'
silver=solid_dds('jeep_mirror_silver',(185,195,200,255))
white=solid_dds('jeep_mirror_spec',(255,255,255,255))
for key,img in [('DiffuseSampler',silver),('SpecSampler',white)]:
 n=mirror.node_tree.nodes.get(key)
 if n:n.image=img;n.texture_properties.embedded=True
for key,val in [('specularIntensityMult',1.0),('specularFalloffMult',250.0),('reflectivePower',1.0)]:
 n=mirror.node_tree.nodes.get(key)
 if n:n.set_float(val)
housing=create_shader('spec.sps');housing.name='JEEP_MIRROR_HOUSING'
olive=solid_dds('jeep_mirror_olive',(69,74,44,255))
housing.node_tree.nodes['DiffuseSampler'].image=olive;housing.node_tree.nodes['DiffuseSampler'].texture_properties.embedded=True

def part(name,verts,faces,material):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.materials.append(material);m.update()
 mesh_add_missing_uv_maps(m);mesh_add_missing_color_attrs(m)
 for layer in m.color_attributes:
  for d in layer.data:d.color=(1,1,1,1)
 ob=body.copy();ob.data=m;ob.name=name;bpy.context.collection.objects.link(ob)
 ob.vertex_groups.clear();ob.vertex_groups.new(name='chassis').add(list(range(len(verts))),1,'REPLACE')
 for level in [LODLevel.VERYHIGH,LODLevel.HIGH,LODLevel.MEDIUM,LODLevel.LOW]:ob.sz_lods.get_lod(level).mesh=m
 return ob

# Round period-correct exterior mirror, reflective surface facing the driver.
cx,cy,cz=-.88,.24,.91
verts=[(cx,cy-.013,cz)]+[(cx+.073*math.cos(i*math.tau/48),cy-.013,cz+.073*math.sin(i*math.tau/48)) for i in range(48)]
part('JEEP_MIRROR_SURFACE',verts,[(0,i+1,(i+1)%48+1) for i in range(48)],mirror)
verts=[];faces=[]
for yy in [cy-.01,cy+.016]:
 for i in range(48):verts.append((cx+.081*math.cos(i*math.tau/48),yy,cz+.081*math.sin(i*math.tau/48)))
for i in range(48):j=(i+1)%48;faces.append((i,j,j+48,i+48))
faces.append(tuple(range(48,96)))
part('JEEP_MIRROR_FRAME',verts,faces,housing)
a=Vector((-.69,.32,.55));b=Vector((cx,cy+.016,cz));axis=(b-a).normalized();u=axis.cross(Vector((0,1,0))).normalized()*.009;v=axis.cross(u)
verts=[tuple(p+u*math.cos(i*math.tau/12)+v*math.sin(i*math.tau/12)) for p in [a,b] for i in range(12)]
part('JEEP_MIRROR_STALK',verts,[(i,(i+1)%12,(i+1)%12+12,i+12) for i in range(12)],housing)
print('JEEP_REFINEMENTS_OK')
