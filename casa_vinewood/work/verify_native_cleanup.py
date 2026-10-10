from pathlib import Path
exec(Path(__file__).with_name('patch_native_house.py').read_text().split('parts=json.loads')[0])
entities=json.loads((W/'work/near_house_entities.json').read_text());validation=[]
def overlap_area(a,offset):
 area=0;count=0
 for models in a.models.values():
  for model in models:
   for g in model.geometries:
    shader=a.shader_group.shaders[g.shader_index];tex=str(next((p.value for p in shader.parameters if p.name.lower()=='diffusesampler'),''))
    if a.name=='ch2_09b_hs05' and 'wins' in tex.lower():continue
    structural=any(k in tex.lower() for k in ('wall32','wall_brick_32','idwall','wins'))
    cuts=RENDER_CUTS+(CLEANUP_CUTS if a.name!='ch2_09b_hs05' or not structural else [])
    vs=g.vertex_buffer['Position'].astype(float)+offset
    for ids in g.index_buffer.reshape(-1,3):
     tri=list(vs[ids]);original=np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))*.5
     pieces,hit=clip(tri,[(lo+.001,hi-.001) for lo,hi in cuts])
     if not hit:continue
     remaining=sum(np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))*.5 for p in pieces for t in triangles(p));loss=max(0,original-remaining)
     if loss>1e-6:area+=loss;count+=1
 return area,count
for q in json.loads((W/'alteracoes_nativas.json').read_text())['render']:
 name=Path(q['file']).stem;e=next(e for e in entities if e['name']==name);offset=np.array(e['pos'])-ORIGIN
 old=try_load_asset(N/q['file']);new=try_load_asset(OUT/q['file']);old.name=name;new.name=name
 before,n=overlap_area(old,offset);after,count=overlap_area(new,offset)
 validation.append({'file':q['file'],'intruding_surface_before_m2':before,'intruding_surface_after_m2':after,'remaining_intruding_triangles':count,'passed':after<.0001})
 print('NATIVE_CLEANUP',q['file'],round(before,4),'->',round(after,6),count,flush=True)
result={'native_render_files_reloaded':True,'tolerance_m':.001,'checks':validation,'passed':all(v['passed'] for v in validation),'in_game_test':False}
(W/'verificacao_limpeza_nativa.json').write_text(json.dumps(result,indent=2));assert result['passed']
