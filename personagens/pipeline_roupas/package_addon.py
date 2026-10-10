"""Package a reviewed native component in its own YMT collection; no native replacement."""
import argparse
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import pipeline as p

COMPONENTS = {'berd': 1, 'hair': 2, 'uppr': 3, 'lowr': 4, 'hand': 5,
              'feet': 6, 'teef': 7, 'accs': 8, 'task': 9, 'decl': 10, 'jbib': 11}


def ymt_xml(collection, slot, texture_id=0):
    availability = ['255'] * 12
    availability[slot] = '0'
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<CPedVariationInfo name="{collection}">
 <bHasTexVariations value="false"/><bHasDrawblVariations value="false"/>
 <bHasLowLODs value="false"/><bIsSuperLOD value="false"/>
 <availComp>{' '.join(availability)}</availComp>
 <aComponentData3 itemType="CPVComponentData"><Item>
  <numAvailTex value="1"/>
  <aDrawblData3 itemType="CPVDrawblData"><Item>
   <propMask value="{1 if slot in (8,11) else 17}"/><numAlternatives value="0"/>
   <aTexData itemType="CPVTextureData"><Item>
    <texId value="{texture_id}"/><distribution value="255"/>
   </Item></aTexData><clothData><ownsCloth value="false"/></clothData>
  </Item></aDrawblData3>
 </Item></aComponentData3>
 <aSelectionSets itemType="CPedSelectionSet"/>
 <compInfos itemType="CComponentInfo"><Item>
  <pedXml_audioID>none</pedXml_audioID><pedXml_audioID2>none</pedXml_audioID2>
  <pedXml_expressionMods>0 0 0 0 0</pedXml_expressionMods>
  <flags value="0"/><inclusions>0</inclusions><exclusions>0</exclusions>
  <pedXml_vfxComps>PV_COMP_HEAD</pedXml_vfxComps><pedXml_flags value="0"/>
  <pedXml_compIdx value="{slot}"/><pedXml_drawblIdx value="0"/>
 </Item></compInfos>
 <propInfo><numAvailProps value="0"/>
  <aPropMetaData itemType="CPedPropMetaData"/><aAnchors itemType="CAnchorProps"/>
 </propInfo><dlcName>{collection}</dlcName>
</CPedVariationInfo>
'''


def hash_name(name):
    value = 0
    for byte in name.lower().encode():
        value = (value + byte) & 0xffffffff
        value = (value + (value << 10)) & 0xffffffff
        value ^= value >> 6
    value = (value + (value << 3)) & 0xffffffff
    value ^= value >> 11
    return (value + (value << 15)) & 0xffffffff


def verify_ymt(path, collection, slot, texture_id):
    root = ET.parse(path).getroot()
    expected = [255] * 12
    expected[slot] = 0
    assert list(map(int, root.findtext('availComp').split())) == expected
    assert root.findtext('dlcName').lower() in (collection.lower(), f'hash_{hash_name(collection):08x}')
    assert len(root.findall('aComponentData3/Item')) == 1
    drawables = root.findall('aComponentData3/Item/aDrawblData3/Item')
    assert len(drawables) == 1
    textures = drawables[0].findall('aTexData/Item')
    assert len(textures) == 1
    assert int(textures[0].find('texId').get('value')) == texture_id
    assert len(root.findall('compInfos/Item')) == 1
    assert int(root.find('compInfos/Item/pedXml_compIdx').get('value')) == slot
    assert int(root.find('compInfos/Item/pedXml_drawblIdx').get('value')) == 0
    assert int(root.find('propInfo/numAvailProps').get('value')) == 0
    return {'collection': collection, 'component': slot, 'drawables': 1, 'textures': 1,
            'cross_component_rules': False, 'round_trip_verified': True}


def package(job):
    job = Path(job).resolve()
    job, data, check = p.preflight(job)
    base, _, _ = p.cached(data['base_id'])
    if not check['ok']:
        raise ValueError(check)
    if not data['review']['positions'] or not data['review']['appearance']:
        raise ValueError('Revisar posicionamento e aparência antes de empacotar.')
    if data['target']['local_index'] != 0:
        raise ValueError('Este empacotador inicial registra uma peça por coleção, no índice 0.')
    report = p.build(job)
    for file, sha in report['files'].items():
        if p.digest(job / file) != sha:
            raise ValueError(f'Candidato alterado: {file}')
    target = data['target']
    collection, prefix, ped = target['collection'], target['prefix'], target['ped']
    for name in (collection, prefix, ped):
        if not re.fullmatch(r'[a-z0-9_]+', name):
            raise ValueError('Identificação inválida.')
    item = p.read(base / 'base.json')['item']
    slot = COMPONENTS[item['category']]
    profile = {('mp_m_freemode_01', 11): 'test_component.lua',
               ('mp_m_freemode_01', 4): 'test_pants.lua'}.get((ped, slot))
    if not profile:
        raise ValueError('Definir e validar perfil de aplicação para este componente/sexo antes de empacotar.')
    commands = data.get('test_commands', {'apply': f"provar_{data['name']}",
                                          'restore': f"restaurar_{data['name']}"})
    if any(not re.fullmatch(r'[a-z][a-z0-9_]+', commands.get(key, '')) for key in ('apply', 'restore')):
        raise ValueError('Comandos de teste inválidos.')
    texture_id = 1 if item['textureFile'].endswith('_whi.ytd') else 0
    folder = job / 'package' / 'resource'
    stream, metadata = folder / 'stream', folder / 'data'
    stream.mkdir(parents=True, exist_ok=True)
    metadata.mkdir(parents=True, exist_ok=True)
    source_xml, round_trip = job / 'work/addon.ymt.xml', job / 'qa/addon.roundtrip.xml'
    source_xml.write_text(ymt_xml(collection, slot, texture_id), encoding='utf-8')
    compiled = stream / f'{prefix}.ymt'
    subprocess.run(['pwsh', '-NoProfile', '-File', str(p.HERE / 'compile_ymt.ps1'),
                    '-SourceXml', str(source_xml), '-OutputYmt', str(compiled),
                    '-RoundTripXml', str(round_trip)], check=True, timeout=60)
    metadata_check = verify_ymt(round_trip, collection, slot, texture_id)
    for name in report['native_files']:
        shutil.copy2(job / 'exports' / name, stream / name)
    character = 'SCR_CHAR_MULTIPLAYER_F' if ped.startswith('mp_f_') else 'SCR_CHAR_MULTIPLAYER'
    (metadata / 'shop.meta').write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<ShopPedApparel><pedName>{ped}</pedName><dlcName>{collection}</dlcName>
 <fullDlcName>{prefix}</fullDlcName><eCharacter>{character}</eCharacter>
 <creatureMetaData/><pedOutfits/><pedComponents/><pedProps/>
</ShopPedApparel>
''', encoding='utf-8')
    (folder / 'fxmanifest.lua').write_text(f"""fx_version 'cerulean'
game 'gta5'
description '{data['name']}: variacao independente de base nativa'
files {{ 'data/shop.meta' }}
data_file 'SHOP_PED_APPAREL_META_FILE' 'data/shop.meta'
client_script 'client.lua'
""", encoding='utf-8')
    client = p.HERE / 'templates' / profile
    script = client.read_text(encoding='utf-8').replace('__COLLECTION__', collection)
    old_apply, old_restore, old_resource = ('camisetatexas', 'roupastexasanterior', 'cidade_west_texas') if slot==11 else ('calcajeans', 'jeansanterior', 'cidade_jeans_washed')
    script = script.replace(old_apply, commands['apply']).replace(old_restore, commands['restore'])
    script = script.replace(old_resource, 'cidade_' + data['name'])
    (folder / 'client.lua').write_text(script, encoding='utf-8')
    result = {'status': 'addon_packaged', 'in_game_verified': data['review']['in_game'],
              'metadata': metadata_check, 'test_commands': commands,
              'base_manifest_sha256': data['base_manifest_sha256'],
              'files': {str(f.relative_to(folder)): p.digest(f) for f in sorted(folder.rglob('*')) if f.is_file()}}
    p.write(job / 'qa/package.json', result)
    return folder, result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job', required=True)
    args = parser.parse_args()
    folder, report = package(args.job)
    print(json.dumps({'resource': str(folder), **report}, indent=2))
