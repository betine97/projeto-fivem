"""Publish compact previews of every native Cayo catalog model, with a UI backup."""
from pathlib import Path
import sys,json,datetime,shutil,runpy
R=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from PIL import Image
work=R/'painel_adm_20261009/cayo_thumbnails'
ui=R/'server-data/resources/cidade_admin/ui'
models=json.loads((work/'models.json').read_text(encoding='utf8'))
assert len(models)==926 and not [m for m in models if m.get('error')]
# Validate all renders before altering the live catalog.
for row in models:
    im=Image.open(work/'renders'/(row['name']+'.png')).convert('RGBA')
    assert im.size==(384,384) and im.getchannel('A').getbbox(),row['name']
backup=R/'server-data/backups'/('editor-imagens-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
shutil.copytree(ui,backup/'cidade_admin/ui')
(ui/'cayo').mkdir(exist_ok=True)
size=0
for index,row in enumerate(models):
    im=Image.open(work/'renders'/(row['name']+'.png')).convert('RGBA')
    target=ui/'cayo'/(row['name']+'.webp')
    try:cached=target.is_file() and Image.open(target).size==(384,384)
    except OSError:cached=False
    if not cached:
        im.save(target,format='WEBP',quality=85,method=4)
    decoded=Image.open(target)
    assert decoded.size==(384,384) and decoded.getchannel('A').getbbox(),row['name']
    size+=target.stat().st_size
    if index%100==0:print('PUBLISH_EDITOR_IMAGE',index,flush=True)
runpy.run_path(str(R/'painel_adm_20261009/build_cayo_catalog.py'),run_name='__main__')
catalog=json.loads((ui/'cayo.json').read_text(encoding='utf8'))
assert {m['name'] for m in models}=={m['sourceModel'] for m in catalog['objects']}
report=dict(passed=True,revision=catalog['revision'],models=len(models),actual_native_models=True,blank_images=0,image_bytes=size,backup=str(backup),in_game_visual_verified=False)
(R/'painel_adm_20261009/cayo-images-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('CAYO_IMAGES_PUBLISHED',len(models),'bytes',size,'backup',backup,flush=True)
