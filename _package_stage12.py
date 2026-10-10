from pathlib import Path
import zipfile,json
base=Path(__file__).resolve().parent
files=[base/n for n in ('warehouse_stage12_plantas.blend','warehouse_stage12_planta_detalhe.png','warehouse_stage12_visao_geral.png','warehouse_stage12_validacao.json','refazer_plantas_stage12.py','LEIA_ME_STAGE12.txt')]
files+=list((base/'texturas_plantas').glob('*.png'))
data=json.loads((base/'warehouse_stage12_validacao.json').read_text())
assert len(data)==18
assert all(abs(p['pot_height_m']-.4)<.0001 and p['new_top_m']>p['old_top_m']+.15 and p['new_top_m']<1.84 for p in data)
dest=Path.home()/'Downloads'/'warehouse_stage12_plantas.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files:
        assert f.is_file() and f.stat().st_size>0
        z.write(f,f.relative_to(base))
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
print(dest, dest.stat().st_size)
