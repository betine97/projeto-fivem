from pathlib import Path
import zipfile

base=Path(__file__).resolve().parent
files=[base/name for name in (
    'warehouse_stage11_ventiladores.blend',
    'warehouse_stage11_ventilador_detalhe.png',
    'warehouse_stage11_exaustor_teto.png',
    'warehouse_stage11_validacao.json',
    'aplicar_texturas_ventiladores.py',
    'LEIA_ME_STAGE11.txt')]
files+=list((base/'texturas_ventiladores').glob('*.png'))
dest=Path.home()/'Downloads'/'warehouse_stage11_ventiladores.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files:
        assert f.is_file() and f.stat().st_size>0
        z.write(f,f.relative_to(base))
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    assert len(z.namelist())==10
print(dest)
print(dest.stat().st_size)
