import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];R=P.parent
sys.path.insert(0,str(R/'laboratorio_fivem/work/pydeps'))
import numpy as np
data=np.load(P/'dados/terreno.npz');grid=data['terrain'];N=len(grid);meta=json.loads((P/'dados/medidas.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
def collection(name,hidden=False):
 c=bpy.data.collections.new(name);scene.collection.children.link(c);c.hide_render=hidden;c.hide_viewport=hidden;return c
main=collection('01_TERRENO_EDITAVEL');waters=collection('02_RIO_LAGO_MAR');strip=collection('03_PISTA_POUSO');lods=[collection('04_LOD_MEDIO',True),collection('05_LOD_BAIXO',True),collection('06_LOD_DISTANTE',True)];phys=collection('07_COLISAO_TERRENO',True);cameraCol=collection('08_CAMERAS_E_LUZES')
def material(name,color,roughness=.8):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=roughness;return m
earth=material('Terreno | areia, solo, relva e rocha',(.35,.42,.23),.95);nt=earth.node_tree;bs=nt.nodes.get('Principled BSDF');tex=nt.nodes.new('ShaderNodeTexImage');im=bpy.data.images.load(str(P/'texturas/albedo_terreno.png'));im.pack();tex.image=im;tex.extension='EXTEND';nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);geo=nt.nodes.new('ShaderNodeNewGeometry');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.28;noise.inputs['Detail'].default_value=3;nt.links.new(geo.outputs['Position'],noise.inputs['Vector']);bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.10;nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
asphalt=material('Pista | asfalto fosco',(.055,.065,.067),.88);paint=material('Pista | sinalizacao branca',(.78,.79,.75),.8)
ocean=material('Mar azul profundo',(.028,.18,.23),.24);riverMat=material('Rio e lago | agua verde azulada',(.045,.28,.26),.20)
for mat in [ocean,riverMat]:
 nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['IOR'].default_value=1.333;bs.inputs['Transmission Weight'].default_value=0;geo=nt.nodes.new('ShaderNodeNewGeometry');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.32;noise.inputs['Detail'].default_value=2;nt.links.new(geo.outputs['Position'],noise.inputs['Vector']);bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.12;nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
gradientY,gradientX=np.gradient(grid[:,:,2],meta['horizontal_cell_m'][1],meta['horizontal_cell_m'][0]);normals=np.stack([-gradientX,-gradientY,np.ones_like(gradientX)],-1);normals/=np.linalg.norm(normals,axis=-1,keepdims=True)
def mesh(name,vertices,faces,col,mat=None,uv=True):
 me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o)
 if mat:me.materials.append(mat)
 if uv:
  uvlayer=me.uv_layers.new(name='UVMap 0');x0,y0=grid[0,0,:2];dx,dy=grid[-1,-1,:2]-grid[0,0,:2];pos=np.asarray(vertices);coords=np.stack([(pos[:,0]-x0)/dx,(pos[:,1]-y0)/dy],-1);loops=np.empty(len(me.loops),np.int32);me.loops.foreach_get('vertex_index',loops);uvlayer.data.foreach_set('uv',coords[loops].astype(np.float32).ravel())
 for face in me.polygons:face.use_smooth=True
 return o
step=(N-1)//8;tiles=[]
for iy in range(8):
 for ix in range(8):
  y0=iy*step;y1=(iy+1)*step;x0=ix*step;x1=(ix+1)*step;patch=grid[y0:y1+1,x0:x1+1]
  if patch[:,:,2].max()<-15:continue
  name='ti_terreno_%02d_%02d'%(iy,ix);record={'name':name,'grid_bounds':[x0,y0,x1,y1],'lod_triangles':{}}
  for stride,col,suffix in [(1,main,''),(2,lods[0],'_MED'),(4,lods[1],'_LOW'),(8,lods[2],'_VLOW')]:
   patch=grid[y0:y1+1:stride,x0:x1+1:stride];n=len(patch);v=patch.reshape(-1,3);j,i=np.meshgrid(np.arange(n-1),np.arange(n-1),indexing='ij');a=(j*n+i).ravel();faces=np.concatenate([np.stack([a,a+1,a+n+1],1),np.stack([a,a+n+1,a+n],1)])
   o=mesh(name+suffix,v.tolist(),faces.tolist(),col,earth);o['setor_x']=ix;o['setor_y']=iy;o['nivel_lod']=stride;o['uso']='Solo autoral; sem geometria do GTA';me=o.data;nn=normals[y0:y1+1:stride,x0:x1+1:stride].reshape(-1,3);me.normals_split_custom_set_from_vertices(nn.tolist());record['lod_triangles'][str(stride)]=len(faces)
   if stride==2:
    c=bpy.data.objects.new('COL_'+name,me.copy());phys.objects.link(c);c.display_type='WIRE';c['collision_material']='GRASS';c['tipo']='Malha de colisao de referencia; exportar como YBN para FiveM';c.data.materials.clear()
  tiles.append(record)
  print('TILE_READY',name,flush=True)
# Unbounded-looking ocean is a presentation surface, separate from land collision.
sea=mesh('MAR | nivel zero',[(x,y,0) for x,y in [(-15000,-15000),(15000,-15000),(15000,15000),(-15000,15000)]],[(0,1,2),(0,2,3)],waters,ocean,False);sea['nivel_mar_m']=0;sea['uso']='Superficie visual para Blender; agua nativa do FiveM requer configuracao propria'
pts=data['river_points'];z=data['river_z'];width=data['river_halfwidth'];delta=np.gradient(pts,axis=0);norm=np.stack([-delta[:,1],delta[:,0]],-1);norm/=np.linalg.norm(norm,axis=1,keepdims=True);left=pts+norm*width[:,None];right=pts-norm*width[:,None];vertices=np.empty((len(pts)*2,3));vertices[0::2,:2]=left;vertices[1::2,:2]=right;vertices[0::2,2]=z+.045;vertices[1::2,2]=z+.045;faces=[]
for i in range(len(pts)-1):a=i*2;faces.extend([(a,a+1,a+3),(a,a+3,a+2)])
river=mesh('RIO | nascente ao estuario',vertices.tolist(),faces,waters,riverMat,False);river['comprimento_m']=meta['river_length_m'];river['agua_desce_ate_mar']=True
center=data['lakecenter'];radius=data['lake_radii'];h=float(data['lakeheight']);verts=[(center[0],center[1],h+.05)]+[(center[0]+radius[0]*math.cos(i*2*math.pi/96),center[1]+radius[1]*math.sin(i*2*math.pi/96),h+.05) for i in range(96)];mesh('LAGO | nascente elevada',verts,[(0,1+i,1+(i+1)%96) for i in range(96)],waters,riverMat,False)
run=meta['runway'];cx,cy=run['center_m'];length=run['length_m'];width=run['width_m'];h=run['level_m']+.07
def plane(name,cx,cy,length,width,h,mat):return mesh(name,[(cx-length/2,cy-width/2,h),(cx+length/2,cy-width/2,h),(cx+length/2,cy+width/2,h),(cx-length/2,cy+width/2,h)],[(0,1,2),(0,2,3)],strip,mat,False)
plane('PISTA | pouso simples sem edificios',cx,cy,length,width,h,asphalt)
for x in np.arange(cx-length/2+35,cx+length/2-35,30):plane('PISTA | faixa central',x,cy,12,.65,h+.01,paint)
for x in [cx-length/2+12,cx+length/2-12]:
 for y in np.linspace(cy-width/2+3,cy+width/2-3,8):plane('PISTA | cabeceira',x,y,14,1.1,h+.01,paint)
for y in [cy-width/2+.8,cy+width/2-.8]:plane('PISTA | borda',cx,y,length-14,.45,h+.01,paint)
scene['projeto']='Teste Ilha | terreno original 3x area estimada do Cayo Perico';scene['area_km2']=meta['land_area_km2'];scene['area_referencia_km2']=meta['reference_land_area_km2_estimate'];scene['multiplicador_area']=3;scene['geometria_cidade_original']=False;scene['nivel_mar_m']=0
world=bpy.data.worlds.new('Ceu de ilha');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.69,.84,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;scene.world=world
light=bpy.data.lights.new('Sol tropical','SUN');light.energy=3.1;light.angle=.08;o=bpy.data.objects.new('Sol tropical',light);cameraCol.objects.link(o);o.rotation_euler=(.48,-.36,-.6)
def camera(name,pos,look,lens=45,ortho=None):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);cameraCol.objects.link(o);o.location=pos;o.rotation_euler=(Vector(look)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=1;d.clip_end=60000
 if ortho:d.type='ORTHO';d.ortho_scale=ortho
 return o
camA=camera('Vista geral da ilha',(2350,-2900,2900),(0,0,80),48);camB=camera('Foz e montanhas',(1500,-1800,700),(110,-330,100),36);camC=camera('Mapa de cima',(0,0,5500),(0,0,0),ortho=3300);scene.camera=camA
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.resolution_x=1800;scene.render.resolution_y=1400;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type!='CPU'
 if any(d.use for d in prefs.devices):scene.cycles.device='GPU'
except Exception:pass
for area in bpy.context.screen.areas if bpy.context.screen else []:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=4000;area.spaces.active.region_3d.view_location=(0,0,100);area.spaces.active.clip_end=60000
scene['observacao_agua']='Agua de apresentacao em malhas separadas; integracao com agua nativa e isolamento do mundo ainda nao ativados no FiveM.'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'teste-ilha.blend'),compress=True)
meta['blender_generated']=True;meta['tiles']=tiles;meta['terrain_high_triangles']=sum(t['lod_triangles']['1'] for t in tiles);meta['terrain_collision_triangles']=sum(t['lod_triangles']['2'] for t in tiles);(P/'dados/medidas.json').write_text(json.dumps(meta,indent=2))
# Portable geometry export excludes ocean, lights, LODs and collision duplicates.
bpy.ops.object.select_all(action='DESELECT')
for col in [main,strip]:
 for o in col.objects:o.select_set(True)
for o in waters.objects:
 if o!=sea:o.select_set(True)
bpy.context.view_layer.objects.active=next(iter(main.objects));bpy.ops.export_scene.gltf(filepath=str(P/'exportacoes/ilha_terreno.glb'),export_format='GLB',use_selection=True,export_yup=True,export_materials='EXPORT')
for name,cam in [('ilha_geral.png',camA),('ilha_foz.png',camB),('ilha_mapa_superior.png',camC)]:
 scene.camera=cam;scene.render.filepath=str(P/'previews'/name);bpy.ops.render.render(write_still=True)
print('BLENDER_ISLAND_READY',len(tiles),meta['terrain_high_triangles'],flush=True)
