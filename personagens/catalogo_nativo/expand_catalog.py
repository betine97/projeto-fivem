"""Expand existing catalog without replacing previously selected models."""
import render_catalog as r
import json, hashlib, math, shutil
from pathlib import Path

path = r.OUT / 'catalog.json'
catalog = json.loads(path.read_text(encoding='utf-8'))
backup = Path(__file__).parent / 'catalog_before_expansion.json'
if not backup.exists():
    shutil.copy2(path, backup)
original = json.loads(backup.read_text(encoding='utf-8'))
baseline = {i['id'] for i in original['items']}
seen = {i['id'] for i in catalog['items']}
skips = []
def identifier(row):
    return hashlib.sha1((row['collection']+row['part']+str(row['index'])).encode()).hexdigest()[:12]

def add(row):
    ident = identifier(row)
    if ident in seen:
        return False
    pieces = []
    try:
        pieces, center, extent, triangles, variations, selected = r.prep(row)
        r.render(pieces,center,extent,.15,r.OUT/'previews'/f'{ident}.webp')
        r.render(pieces,center,extent,math.pi+.15,r.OUT/'previews'/f'{ident}-back.webp')
        catalog['items'].append({'id':ident,'sex':row['sex'],'category':row['part'],
            'title':r.CATEGORIES[row['part']],'collection':row['collection'],
            'collectionLabel':r.collection_label(row['collection']),'index':row['index'],
            'file':row['path'].split('/')[-1],'textureCount':len(variations),
            'textureFile':selected['path'].split('/')[-1],'triangles':triangles,
            'image':f'previews/{ident}.webp','back':f'previews/{ident}-back.webp'})
        seen.add(ident)
        return True
    except Exception as e:
        skips.append({'model':row,'reason':str(e)})
        return False
    finally:
        for piece in pieces:
            for obj in piece:obj.release()

def save():
    catalog.pop('samplePerCategory',None)
    catalog['selection'] = 'expanded-male-tops-and-all-renderable-masks'
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(catalog,ensure_ascii=False),encoding='utf-8')
    temp.replace(path)

tops = [m for m in r.DATA['models'] if m['sex']=='male' and m['part'] in ('jbib','teef') and 'g9ec' not in m['collection']]
tops.sort(key=lambda m:(m['index'],m['collection'],m['part']))
added = sum(i['id'] not in baseline and i['sex']=='male' and i['category'] in ('jbib','teef') for i in catalog['items'])
for row in tops:
    if added >= 300:break
    if add(row):
        added += 1
        if added % 25 == 0:
            save();print('TOPS',added,flush=True)
assert added == 300, added
mask_candidates = [m for m in r.DATA['models'] if m['part']=='berd']
for n,row in enumerate(mask_candidates):
    add(row)
    if n % 50 == 0:
        save();print('MASKS',n+1,'/',len(mask_candidates),flush=True)
save()
report={'total':len(catalog['items']),'newTops':added,'maskCandidates':len(mask_candidates),
        'masks':sum(i['category']=='berd' for i in catalog['items']),'skipped':skips}
(Path(__file__).parent/'expansion_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('COMPLETE',json.dumps({k:v for k,v in report.items() if k!='skipped'}),'SKIPPED',len(skips),flush=True)
