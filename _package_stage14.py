from pathlib import Path
import shutil,zipfile
base=Path(__file__).resolve().parent
downloads=Path.home()/'Downloads'
blend=base/'warehouse_stage14_projeto_completo.blend'
shutil.copy2(blend,downloads/blend.name)
files=[blend]+[base/n for n in ('warehouse_stage14_projeto_completo.png','warehouse_stage14_zona_tecnica.png','warehouse_stage14_validacao.json','LEIA_ME_STAGE14.txt','aplicar_zona_tecnica_stage14.py')]
files+=list((base/'texturas_zona_tecnica').glob('*.png'))
dest=downloads/'warehouse_stage14_projeto_completo.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files:
        assert f.is_file() and f.stat().st_size>0
        z.write(f,f.relative_to(base))
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
print(dest,dest.stat().st_size)
print(downloads/blend.name,blend.stat().st_size)
