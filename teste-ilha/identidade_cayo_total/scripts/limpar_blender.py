from pathlib import Path
import bpy,json,shutil,datetime
O=Path(__file__).resolve().parents[1];path=O/'ilha_cayo_cidade_vilarejos.blend'
backup=O/'backups';backup.mkdir(exist_ok=True)
shutil.copy2(path,backup/'ilha_antes_remocao_arvores_autorais.blend')
bpy.ops.wm.open_mainfile(filepath=str(path));old=set();collections=[]
for name in ['04_VEGETACAO','13_MATAS_DO_RESTANTE_DA_ILHA']:
    col=bpy.data.collections.get(name)
    if col:old.update(col.all_objects);collections.append(col)
bpy.data.batch_remove(ids=list(old))
for col in collections:bpy.data.collections.remove(col)
native=bpy.data.collections['14_IDENTIDADE_CAYO_NATIVA'];counts={}
for ob in native.objects:
    f=ob.get('family','');counts[f]=counts.get(f,0)+1
assert counts['tree']==18644,counts
scene=bpy.context.scene;scene['removed_authored_forest_objects']=len(old);scene['forest_source']='Native Cayo Perico geometry, shaders and wind preserved in FiveM; all former authored forest instances removed.'
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
report=dict(removed_authored_objects=len(old),remaining_authored_forest_collections=0,native_instances_by_family=counts,blend=str(path),backup=str(backup/'ilha_antes_remocao_arvores_autorais.blend'))
(O/'dados/remocao_blender.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('AUTHORED_FOREST_REMOVED',report,flush=True)
