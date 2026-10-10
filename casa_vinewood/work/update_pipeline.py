from pathlib import Path
w=Path(__file__).resolve().parent
p=w/'fit_layout.py';s=p.read_text();p.write_text(s.replace("else9.79","else 9.79"))
p=w/'export_fivem.py';s=p.read_text();s=s.replace("W/'mansao_interior_inicial.blend'","W/'mansao_encaixada.blend'")
start=s.index('floor_extra=');end=s.index('\ndef project_uv',start)
s=s[:start]+'''glass=create_shader('glass.sps');glass.name='mansao_vidro'
Image.new('RGBA',(4,4),(170,200,210,48)).save(OUT/'mansao_vidro.dds',pixel_format='DXT5')
tex=glass.node_tree.nodes['DiffuseSampler'];tex.image=bpy.data.images.load(str(OUT/'mansao_vidro.dds'),check_existing=True);tex.texture_properties.embedded=True
'''+s[end:]
s=s.replace("'mansao_paredes':list(cols['outer'].objects)","'mansao_paredes':[o for o in cols['outer'].objects if not o.name.startswith('Vidros')]")
s=s.replace("'mansao_teto':list(cols['ceil'].objects)}","'mansao_teto':list(cols['ceil'].objects),'mansao_vidros':[o for o in cols['outer'].objects if o.name.startswith('Vidros')]}")
s=s.replace("mat=wood if name==", "mat=glass if name=='mansao_vidros' else wood if name==")
s=s.replace("  collision.extend({'points':[list(mesh.vertices[i].co) for i in t.vertices],'wood':mat==wood,'source':src.name} for t in mesh.loop_triangles)","""  physical=not (name=='mansao_escada' and 'degrau' in src.name)
  if physical:
   collision.extend({'points':[list(mesh.vertices[i].co) for i in t.vertices],'wood':mat==wood,'source':src.name,'group':name} for t in mesh.loop_triangles)""")
start=s.index('# Concealed continuous');end=s.index("(W/'colisoes_fivem.json')",start)
s=s[:start]+'''# Only the separate ramps carry stair walking collision; the risers are visual.
for src in bpy.data.collections['09_COLISAO_DE_CAMINHADA (oculta)'].objects:
 src.data.calc_loop_triangles()
 collision.extend({'points':[list(src.matrix_world@src.data.vertices[i].co) for i in t.vertices],'wood':True,'source':src.name,'group':'mansao_escada'} for t in src.data.loop_triangles)
'''+s[end:]
p.write_text(s)
p=w/'patch_native_house.py';s=p.read_text()
s=s.replace("from szio.types import Vector","from szio.types import Vector\nfrom shapely.geometry import Polygon,Point,box as rect")
s=s.replace("str(ROOT/'laboratorio_fivem/work/pydeps')","str(W/'work/pydeps'),str(ROOT/'laboratorio_fivem/work/pydeps')")
start=s.index('CUTS=');end=s.index('\nTARGET=',start)
s=s[:start]+'''SPEC=json.loads((W/'encaixe_fachada.json').read_text())
RENDER_CUTS=[(np.array(a),np.array(b)) for a,b in SPEC['door_cuts']]
FOOTPRINT=Polygon(SPEC['ground_polygon']).union(Polygon(SPEC['upper_polygon'])).buffer(.38,join_style=2)
xy=list(FOOTPRINT.exterior.coords);xs=sorted(set(v[0] for v in xy));ys=sorted(set(v[1] for v in xy))
CUTS=[(np.array([x0,y0,-1.07]),np.array([x1,y1,6.52])) for x0,x1 in zip(xs,xs[1:]) for y0,y1 in zip(ys,ys[1:]) if FOOTPRINT.covers(Point((x0+x1)/2,(y0+y1)/2))]
CUTS+=RENDER_CUTS
'''+s[end:]
s=s.replace('def clip(poly):','def clip(poly,cuts=None):').replace(' for lo,hi in CUTS:\n  new=[]',' for lo,hi in (CUTS if cuts is None else cuts):\n  new=[]')
s=s.replace('    vb=g.vertex_buffer;names=',"""    sh=a.shader_group.shaders[g.shader_index]
    tex=next((p.value for p in sh.parameters if p.name.lower()=='diffusesampler'),'')
    if 'wins' in str(tex).lower():count+=len(g.index_buffer)//3;continue
    vb=g.vertex_buffer;names=""")
s=s.replace('polys,hit=clip(poly)','polys,hit=clip(poly,RENDER_CUTS)')
# Remove original house box occluders as a whole. Keeping their outside faces blocks views from inside.
s=s.replace('  tris=[];hit=False\n  for ids in FACES:',"""  footprint=Polygon(pts[[0,1,2,3],:2])
  overlaps=not footprint.intersection(FOOTPRINT.buffer(.5)).is_empty and pts[:,2].max()>-1 and pts[:,2].min()<7
  if overlaps:box_changed+=1;continue
  tris=[];hit=False
  for ids in FACES:""")
p.write_text(s)
print('PIPELINE_UPDATED')
