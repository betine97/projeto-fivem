exec(open(__file__.replace('inspect_house.py','render_candidates.py'),encoding='utf-8').read().split('for f in ')[0])
measure=[]
for name in ['ch2_09c_hs13']:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 f=HERE/'native'/(name+'.ydr');a=try_load_asset(f)
 with import_context_scope(ImportContext(name,AssetTarget(AssetFormat.NATIVE,AssetVersion.GEN8),f.parent,ImportSettings(False,False,False,False))):o=create_drawable(a,name=name)
 verts=[x.matrix_world@v.co for x in o.children_recursive if x.type=='MESH' for v in x.data.vertices]
 lo=Vector(tuple(min(v[i] for v in verts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in verts) for i in range(3)));center=(lo+hi)/2;size=max(hi-lo)
 measure.append(dict(name=name,min=list(lo),max=list(hi),dimensions=list(hi-lo)))
 for n,d in enumerate([(-1,1,.5),(1,1,.5),(-1,-1,.5),(0,0,2)]):
  bpy.ops.object.camera_add(location=center+Vector(d)*size);c=bpy.context.object;c.rotation_euler=(center-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=size*1.25;s.camera=c
  s.render.resolution_x=700;s.render.resolution_y=600;s.render.filepath=str(dest/(name+f'_view{n}.png'));bpy.ops.render.render(write_still=True)
 (HERE/(name+'.blend')).parent.mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(HERE/(name+'.blend')))
(HERE/'measure_candidates.json').write_text(json.dumps(measure,indent=2))








