"""Refina amostragem de materiais e empacota todas as dependencias locais."""
import bpy,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('modelagem',ROOT/'scripts'/'modelar_estruturas.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
for path in sorted((ROOT/'modelos').glob('[0-9][0-9]_*.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(path));id=int(path.stem[:2]);mod.BUILDID=id;mod.C=dict(mod.CFG[id]);mod.C['story']=3.2;mod.C['H']=mod.C.get('h',mod.C['n']*3.2)
    mod.P={k:mod.homography(mod.C[k]) for k in ('frente','lado')};mod.PHOTO=next(i for i in bpy.data.images if i.name.startswith('Referencia_original_'))
    mod.COL={c.name:c for c in bpy.data.collections};mod.M={m.name:m for m in bpy.data.materials}
    old=bpy.data.materials.get('Reboco_extraido_da_referencia');new=mod.sampled_material('Reboco_revisado',mod.find_wall_patch(),mod.C['c'])
    if old:old.user_remap(new);bpy.data.materials.remove(old)
    new.name='Reboco_extraido_da_referencia';mod.M['Reboco_foto']=new
    if id==10:
        landings=[o for o in bpy.data.objects if o.name.startswith('Mezanino') and o.scale.x<2]
        for o in landings:o.location.y=7.20;o.scale.y=1.0
        data=json.loads((ROOT/'dados'/'10_modelo.json').read_text(encoding='utf-8'))
        for hole in data['aberturas']:
            if hole['tipo']=='vao_escada_mezanino':hole['limites'][3]=6.7
        (ROOT/'dados'/'10_modelo.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    mod.render(ROOT/'previews'/f'{id:02}_exterior.png');mod.render(ROOT/'previews'/f'{id:02}_interior.png',True)
    print('ACABAMENTO_REVISADO',id,flush=True)
print('REVISAO_CONCLUIDA',flush=True)
