"""Approved native bases -> immutable cache -> versioned clothing variations.

No command writes into GTA archives, live resources, favorites, or tags.
Heavy native/Blender dependencies load only for the stage that needs them.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VERSION = 1


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def config():
    return read(HERE / 'settings.json')


def approved(cfg=None):
    cfg = cfg or config()
    catalog = read(ROOT / cfg['catalog'])
    tags = read(ROOT / cfg['tags'])['items']
    return [i for i in catalog['items'] if 'OK' in tags.get(i['id'], [])]


def base_item(base_id, cfg=None):
    result = next((i for i in approved(cfg) if i['id'] == base_id), None)
    if not result:
        raise ValueError('A base precisa existir no acervo e possuir a tag OK atual.')
    return result


def native(cfg):
    for path in reversed(cfg['native_dependencies']):
        sys.path.insert(0, str(ROOT / path))
    from native_backend import Backend
    return Backend(cfg, ROOT)


def cached(base_id, cfg=None):
    cfg = cfg or config()
    if not isinstance(base_id,str) or not re.fullmatch(r'[a-zA-Z0-9_]{1,64}',base_id):
        raise ValueError('ID da base inválido.')
    item = base_item(base_id, cfg)
    backend_hash = digest(HERE / 'native_backend.py')
    inventory_hash = digest(ROOT / cfg['inventory'])
    cache_key = hashlib.sha256((backend_hash + inventory_hash + json.dumps(item, sort_keys=True)).encode()).hexdigest()[:12]
    folder = HERE / 'bases' / base_id / cache_key
    manifest = folder / 'base.json'
    if manifest.exists():
        saved = read(manifest)
        if (saved.get('backend_sha256') == backend_hash
                and saved.get('inventory_sha256') == inventory_hash
                and saved['item'] == item
                and all((folder / name).is_file() and digest(folder / name) == value
                        for name, value in saved['files'].items())
                and all(Path(name).is_file()
                        and [Path(name).stat().st_size, Path(name).stat().st_mtime_ns] == value
                        for name, value in saved['archives'].items())):
            return folder, saved, True
        raise ValueError('Cache da base mudou. Preserve-o e prepare uma revisão do cache; não sobrescreva originais silenciosamente.')
    folder.mkdir(parents=True, exist_ok=True)
    result = native(cfg).extract(item, folder)
    result.update(version=VERSION, item=item, backend_sha256=backend_hash,
                  inventory_sha256=inventory_hash)
    result['files'] = {str(p.relative_to(folder)): digest(p)
                       for p in sorted(folder.rglob('*')) if p.is_file()}
    write(manifest, result)
    return folder, result, False


def copy_input(source, dest):
    source = Path(source).resolve(strict=True)
    dest = Path(dest)
    if dest.exists():
        raise ValueError(f'Entrada já existe: {dest}')
    shutil.copy2(source, dest)
    return str(dest.name)


def new_job(name, base_id, reference=None, cfg=None):
    if not re.fullmatch(r'[a-z][a-z0-9_]{1,39}', name):
        raise ValueError('Nome: 2–40 letras minúsculas, números ou _.')
    cfg = cfg or config()
    base, source, hit = cached(base_id, cfg)
    parent = HERE / 'jobs' / name
    revisions = [int(p.name[1:]) for p in parent.glob('r[0-9]*') if p.is_dir()]
    job = parent / f'r{max(revisions, default=0)+1:03}'
    job.mkdir(parents=True)
    for directory in ('inputs', 'work', 'exports', 'qa'):
        (job / directory).mkdir()
    image = copy_input(reference, job / 'inputs' / Path(reference).name) if reference else None
    item = source['item']
    ped = 'mp_m_freemode_01' if item['sex'] == 'male' else 'mp_f_freemode_01'
    # Versioned names prevent one prototype replacing an earlier variation.
    collection = f'cidade_{name}_{job.name}'
    manifest = {
        'pipeline_version': VERSION, 'name': name, 'revision': job.name,
        'base_id': base_id, 'base_manifest_sha256': digest(base / 'base.json'),
        'reference_image': image,
        'material': {'albedo_atlas': None, 'preserve_native_normal_specular': True},
        'components': [],
        'target': {'mode': 'addon', 'ped': ped, 'collection': collection,
                   'prefix': f'{ped}_{collection}', 'local_index': 0},
        'review': {'positions': False, 'appearance': False, 'in_game': False},
        'notes': ['Costas e regiões não mostradas na referência precisam de uma decisão registrada.']
    }
    write(job / 'job.json', manifest)
    write(job / 'qa' / 'intake.json', {'status': 'awaiting_reference' if not image else 'ready_for_art',
                                     'base_approved': True, 'cache_hit': hit})
    return job


def load_job(path):
    path = Path(path).resolve()
    if path.is_dir():
        path /= 'job.json'
    path.relative_to(HERE / 'jobs')
    return path.parent, read(path)


def input_path(job, value):
    if not isinstance(value, str) or not value:
        raise ValueError('Arquivo de entrada ausente.')
    path = (job / 'inputs' / value).resolve()
    path.relative_to((job / 'inputs').resolve())
    if not path.is_file():
        raise ValueError(f'Entrada não encontrada: {value}')
    return path


def preflight(path, cfg=None):
    cfg = cfg or config()
    job, data = load_job(path)
    errors, warnings, placements = [], [], []
    try:
        base, source, _ = cached(data['base_id'], cfg)
        if data['base_manifest_sha256'] != digest(base / 'base.json'):
            errors.append('A base do projeto foi alterada desde a criação.')
    except (ValueError, OSError) as error:
        errors.append(str(error))
        source = None
    for field in ('reference_image',):
        try:
            input_path(job, data.get(field))
        except (ValueError, OSError) as error:
            errors.append(f'{field}: {error}')
    try:
        input_path(job, data['material'].get('albedo_atlas'))
    except (ValueError, OSError) as error:
        errors.append(f'Atlas UV final: {error}')
    if data['material'].get('preserve_native_normal_specular') is not True:
        errors.append('Mudança de normal/especular precisa de um adaptador de material específico.')
    target = data.get('target', {})
    if (source and target.get('ped') != ('mp_m_freemode_01' if source['item']['sex'] == 'male' else 'mp_f_freemode_01')):
        errors.append('Modelo de personagem incompatível com a base.')
    if target.get('mode') != 'addon' or not re.fullmatch(r'cidade_[a-z0-9_]+', target.get('collection', '')):
        errors.append('A saída precisa ter uma coleção própria, sem substituir peças nativas.')
    if target.get('prefix') != f"{target.get('ped')}_{target.get('collection')}":
        errors.append('Prefixo de exportação incompatível com a coleção.')
    if target.get('local_index') != 0:
        errors.append('Este adaptador exporta uma peça por coleção, no índice local zero.')
    ids = set()
    backend = None
    for part in data.get('components', []):
        part_id = part.get('id')
        if not part_id or part_id in ids:
            errors.append('Componentes devem ter identificadores únicos.'); continue
        ids.add(part_id)
        if part.get('kind') == 'secondary_prop':
            warnings.append(f'{part_id}: movimento visual com mola; colisão de tecido não é oferecida pelo adaptador atual.')
            errors.append(f'{part_id}: requer autoria/exportação do objeto YDR e teste do runtime antes de liberar o pacote.')
            continue
        if part.get('kind') != 'surface_patch':
            errors.append(f'{part_id}: adaptador de componente não suportado.'); continue
        try:
            if not source:
                raise ValueError('Base indisponível.')
            if not 0.5 <= float(part['relief_mm']) <= cfg['limits']['max_relief_mm']:
                raise ValueError('Relevo fora do orçamento configurado.')
            if not re.fullmatch(r'[a-z][a-z0-9_]*', part_id):
                raise ValueError('ID de componente inválido.')
            input_path(job, part['image'])
            backend = backend or native(cfg)
            check = backend.check_anchor(base, part)
            placements.append({'id': part_id, **check})
            if not check['ok']:
                errors.extend(f'{part_id}: {text}' for text in check['errors'])
        except (KeyError, TypeError, ValueError, OSError) as error:
            errors.append(f'{part_id}: {error}')
    warnings.extend(data.get('notes', []))
    report = {'ok': not errors, 'errors': errors, 'warnings': warnings,
              'placements': placements, 'in_game_validation': 'pending'}
    write(job / 'qa' / 'preflight.json', report)
    return job, data, report


def build(path, cfg=None):
    cfg = cfg or config()
    job, data, report = preflight(path, cfg)
    if not report['ok']:
        raise ValueError('Pré-checagem bloqueou a exportação. Consulte qa/preflight.json.')
    base, _, _ = cached(data['base_id'], cfg)
    dependencies = [HERE / 'pipeline.py', HERE / 'native_backend.py', base / 'base.json',
                    job / 'job.json', input_path(job, data['material']['albedo_atlas'])]
    dependencies += [input_path(job, p['image']) for p in data['components']]
    fingerprint = hashlib.sha256(''.join(digest(p) for p in dependencies).encode()).hexdigest()
    saved_path = job / 'qa' / 'build.json'
    if saved_path.exists():
        old = read(saved_path)
        if old['fingerprint'] == fingerprint and all(
                (job / name).is_file() and digest(job / name) == sha for name, sha in old['files'].items()):
            return {**old, 'cache_hit': True}
    start = time.perf_counter()
    result = native(cfg).build(base, job, data)
    # The backend must prove the untouched original geometry survived the round trip.
    if not result.get('original_geometry_unchanged'):
        raise ValueError('A base não foi preservada na exportação.')
    result.update(fingerprint=fingerprint, cache_hit=False, seconds=round(time.perf_counter()-start, 3),
                  status='native_candidate', deployable=False,
                  pending=['addon_ymt_and_shop_metadata', 'four_views_and_pose_review', 'in_game_test'])
    result['files'] = {str(p.relative_to(job)): digest(p)
                       for p in sorted((job / 'exports').glob('*')) if p.is_file()}
    write(saved_path, result)
    return result


def blender_base(base_id, cfg=None):
    cfg = cfg or config()
    base, _, _ = cached(base_id, cfg)
    builder_hash = digest(HERE / 'blender_base.py')
    output = base / 'blender' / builder_hash[:12]
    if (output / 'base.blend').exists():
        report = read(output / 'blender.json')
        if (report['source_manifest_sha256'] == digest(base / 'base.json')
                and report['builder_sha256'] == builder_hash
                and report['blend_sha256'] == digest(output / 'base.blend')):
            return {'cache_hit': True, **report}
        raise ValueError('Projeto Blender do cache foi alterado; preserve e crie uma revisão.')
    output.mkdir(parents=True, exist_ok=True)
    command = [cfg['blender'], '--background', '--factory-startup', '--python-exit-code', '1', '--python', str(HERE / 'blender_base.py'),
               '--', str(base), str(HERE / 'settings.json'), str(output)]
    with (output / 'blender.log').open('w', encoding='utf-8') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    report = read(output / 'blender.json')
    report.update(source_manifest_sha256=digest(base / 'base.json'),
                  builder_sha256=builder_hash, blend_sha256=digest(output / 'base.blend'),
                  project=str(output / 'base.blend'))
    write(output / 'blender.json', report)
    return {'cache_hit': False, **report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    listing = commands.add_parser('bases'); listing.add_argument('--category'); listing.add_argument('--sex')
    preparing = commands.add_parser('prepare'); preparing.add_argument('--base', required=True); preparing.add_argument('--blender', action='store_true')
    creating = commands.add_parser('new'); creating.add_argument('--base', required=True); creating.add_argument('--name', required=True); creating.add_argument('--reference')
    for command in ('check', 'build'):
        sub = commands.add_parser(command); sub.add_argument('--job', required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        if args.command == 'bases':
            result = [{k:i[k] for k in ('id','sex','category','collection','index','file')}
                      for i in approved() if (not args.category or i['category']==args.category) and (not args.sex or i['sex']==args.sex)]
        elif args.command == 'prepare':
            folder, _, hit = cached(args.base)
            result = {'base': str(folder), 'cache_hit': hit}
            if args.blender:
                result['blender'] = blender_base(args.base)
        elif args.command == 'new':
            result = {'job': str(new_job(args.name, args.base, args.reference))}
        elif args.command == 'check':
            result = preflight(args.job)[2]
        else:
            result = build(args.job)
        print(json.dumps({'result': result, 'elapsed_seconds': round(time.perf_counter()-started, 3)}, ensure_ascii=False, indent=2))
        if isinstance(result, dict) and result.get('ok') is False:
            return 2
    except (ValueError, OSError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False)); return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
