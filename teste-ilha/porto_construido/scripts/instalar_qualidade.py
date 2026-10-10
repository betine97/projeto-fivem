"""Deploy verified native material assets only; preserve current gameplay and NUI fixes."""
from pathlib import Path
import datetime, hashlib, json, shutil

O = Path(__file__).resolve().parents[1]
R = O.parent.parent
STREAM = O/'fivem/stream'
TERRAIN = O/'qualidade_terreno/stream'
REVISION = 'ilha-materiais-20261009-1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads((O/'dados/validacao_qualidade.json').read_text())
    assert report['passed']
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = O/'backups'/('qualidade_'+stamp)
    records = []

    def copy(source, destination):
        sha = digest(source)
        previous = digest(destination) if destination.exists() else None
        if previous == sha:
            return
        relative = destination.relative_to(R)
        preserved = backup/relative
        if destination.exists():
            preserved.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(destination,preserved)
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,destination)
        assert digest(destination) == sha
        records.append(dict(target=str(relative),old_sha256=previous,new_sha256=sha,
                            backup=str(preserved.relative_to(backup)) if previous else None))

    tiles = json.loads((O/'qualidade_terreno/dados/terrain_quality.json').read_text())['sectors']
    terrain = {p.name for p in TERRAIN.iterdir() if p.is_file()}
    assert len(tiles) >= 42
    for filename in sorted(terrain):
        assert (TERRAIN/filename).is_file(), filename
        for base in [O.parent/'fivem/stream',R/'server-data/resources/teste_ilha/stream']:
            copy(TERRAIN/filename,base/filename)
    # Native export contains these authored map assets and their dictionaries.
    for path in sorted(STREAM.iterdir()):
        if not path.is_file() or path.suffix not in ['.ydr','.ytd','.ytyp','.ymap','.ymf']:
            continue
        if (path.name in terrain and path.name!='_manifest.ymf') or path.name.startswith('ti_terreno') or path.name=='pe_solo.ytd':
            continue
        copy(path,R/'server-data/resources/porto_esperanca/stream'/path.name)
    # The resource owns a single terrain revision; collisions were never regenerated.
    island = R/'server-data/resources/teste_ilha/stream'
    port = R/'server-data/resources/porto_esperanca/stream'
    assert not any((port/n).exists() for n in terrain if n!='_manifest.ymf')
    for tile in tiles:
        name=tile['name']+'.ybn'
        previous=O/'backups/qualidade_20261009_antes/installed/teste_ilha'/name
        if previous.exists():
            assert digest(island/name)==digest(previous), name
        else:
            assert digest(island/name)==digest(TERRAIN/name), name
    # Revision is data only; copying entire resource folders would regress client fixes.
    config = R/'server-data/resources/porto_esperanca/data/config.json'
    saved = json.loads(config.read_text(encoding='utf-8-sig'))
    original = backup/config.relative_to(R)
    original.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(config,original)
    saved['material_revision']=REVISION
    config.write_text(json.dumps(saved,indent=2),encoding='utf8')
    backup.mkdir(parents=True,exist_ok=True)
    manifest = dict(revision=REVISION,created_at=stamp,backup=str(backup),records=records,
                    assets_changed=len(records),terrain_sectors=len(tiles),houses=10,
                    gameplay_scripts_unchanged=True,collision_files_unchanged=True,
                    client_visual_verified=False)
    (backup/'restauracao.json').write_text(json.dumps(manifest,indent=2))
    (O/'dados/instalacao_qualidade.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({k:v for k,v in manifest.items() if k!='records'},indent=2))


if __name__ == '__main__':
    main()
