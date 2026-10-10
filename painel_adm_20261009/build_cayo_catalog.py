from pathlib import Path
import sys,json,csv,re,collections
R=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.gta5 import try_load_asset
P=R/'teste-ilha';dest=R/'server-data/resources/cidade_admin'
types={}
for path in list((P/'cayo_perico/originais/assets').glob('*.ytyp'))+list((P/'identidade_natural/fontes').glob('*.ytyp'))+list((P/'identidade_cayo_total/fontes').glob('*.ytyp')):
    a=try_load_asset(path)
    if a:
        for t in a.archetypes:types[str(t.name)]=t
nature=json.loads((P/'identidade_cayo_total/dados/implantacao.json').read_text(encoding='utf-8-sig'))
rows=list(csv.DictReader((P/'identidade_natural/dados/entidades_cayo.tsv').open(),delimiter='\t'))
names={q['name'] for q in rows if q['lod'] in ['LODTYPES_DEPTH_HD','LODTYPES_DEPTH_ORPHANHD']}
names.update(nature['models'])
grass=json.loads((P/'identidade_cayo_total/dados/rasteira.json').read_text(encoding='utf-8-sig'))
names.update(grass['source_counts'])
def category(n):
    if 'tree' in n or 'palm' in n or 'palmeto' in n:return 'Árvores e palmeiras'
    if any(k in n for k in ['grass','fern','weed','bush','plant','saplin','meadow']):return 'Arbustos, grama e plantas'
    if any(k in n for k in ['rock','stone','boulder']):return 'Pedras e rochas'
    if any(k in n for k in ['water','tank','wtower','pipe','pump']):return 'Água e infraestrutura'
    if any(k in n for k in ['barrier','fence','gate','wall']):return 'Cercas e barreiras'
    if any(k in n for k in ['dock','boat','buoy','pier','mooring']):return 'Porto e costa'
    if any(k in n for k in ['hut','house','barrack','shed','hangar','building']):return 'Construções'
    if any(k in n for k in ['road','sign','lamp','light','pole']):return 'Estradas e iluminação'
    return 'Objetos e decoração'
pretty={'tree':'Árvore','palm':'Palmeira','bush':'Arbusto','rock':'Rocha','grass':'Grama','plant':'Planta','water':'Água','tank':'Tanque','fern':'Samambaia','banana':'Bananeira','mang':'Mangue','frangipani':'Frangipani','umbrella':'Árvore de copa','palmeto':'Palmeira rasteira'}
localized=json.loads((R/'painel_adm_20261009/cayo_names_pt_br.json').read_text(encoding='utf8'))
catalog=[];excluded=[]
for n in sorted(names):
    t=types.get(n)
    if not t or 'Mlo' in type(t).__name__ or re.search(r'(^hash_|_lod|_slod|_combo|_terrain|_ter\d|_placement|_mlo|_occl|_shadow)',n):excluded.append(n);continue
    if not re.fullmatch(r'[a-zA-Z0-9_]{1,64}',n):excluded.append(n);continue
    lo=list(t.bb_min);hi=list(t.bb_max)
    # Large terrain/map slabs belong to the map hierarchy, not the prop editor.
    if max(hi[i]-lo[i] for i in range(3))>180:excluded.append(n);continue
    model=nature['alias_map'].get(n,grass.get('alias_map',{}).get(n,n))
    label=re.sub(r'^(h4_|csx_|prop_|mph4_|mp_h4_|h4_prop_)','',n)
    label=re.sub(r'^(prop_|mph4_)','',label)
    label=' '.join(pretty.get(w,w) for w in label.strip('_').split('_'))
    image='cayo/'+n+'.webp'
    assert (dest/'ui'/image).is_file(), f'Native thumbnail missing: {n}'
    catalog.append(dict(model=model,sourceModel=n,name=localized[n],category=category(n),image=image,bbMin=lo,bbMax=hi,drawDistance=6000 if n in nature['models'] and nature['models'][n]['family'] in ['tree','subcanopy'] else 1800))
payload=dict(revision='editor-ptbr-controles-20261010-1',objects=catalog,bounds=dict(minX=-1278,maxX=1278,minY=-1686,maxY=1686,minZ=-40,maxZ=240),maxPlacements=5000)
(dest/'data').mkdir(exist_ok=True)
(dest/'ui/cayo.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
(R/'painel_adm_20261009/cayo-catalog-report.json').write_text(json.dumps(dict(models=len(catalog),categories=dict(collections.Counter(q['category'] for q in catalog)),excluded=excluded),ensure_ascii=False,indent=2),encoding='utf8')
print('CAYO_CATALOG',len(catalog),collections.Counter(q['category'] for q in catalog))
