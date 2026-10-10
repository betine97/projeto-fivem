from pathlib import Path
import shutil,zipfile
base=Path(__file__).resolve().parent
downloads=Path.home()/'Downloads'
blend=base/'warehouse_stage13_projeto_completo.blend'
shutil.copy2(blend,downloads/blend.name)
files=[blend]+[base/n for n in ('warehouse_stage13_projeto_completo.png','warehouse_stage13_validacao.json','LEIA_ME_PROJETO_COMPLETO_STAGE13.txt','aplicar_racks_stage13.py','texturas_racks/metal_escuro_desgastado.png')]
dest=downloads/'warehouse_stage13_projeto_completo.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files:
        assert f.is_file() and f.stat().st_size>0
        z.write(f,f.relative_to(base))
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
print(str(dest),dest.stat().st_size)
print(str(downloads/blend.name),blend.stat().st_size)
