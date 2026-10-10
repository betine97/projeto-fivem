from pathlib import Path
import sys,runpy
R=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from PIL import Image
dest=R/'server-data/resources/cidade_admin/ui/cayo';dest.mkdir(exist_ok=True)
paths=list((R/'teste-ilha/identidade_cayo_total/atlas').glob('*_front.png'))
for path in paths:Image.open(path).save(dest/(path.name.removesuffix('_front.png')+'.webp'),quality=90,method=6)
css=R/'server-data/resources/cidade_admin/ui/style.css'
css.write_text(css.read_text().replace('.card-info h3{white-space:normal;height:32px;line-height:16px}', '.cayo .card-info h3{white-space:normal;height:32px;line-height:16px}').replace('.card-info code{font-size:9px}', '.cayo .card-info code{font-size:9px}'),encoding='utf8')
print('CAYO_THUMBNAILS',len(paths),flush=True)
runpy.run_path(str(R/'painel_adm_20261009/build_cayo_catalog.py'),run_name='__main__')
