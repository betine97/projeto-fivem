import json, sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=R/'teste-ilha/cayo_perico';F=P/'fivem';S=F/'stream'
sys.path[:0]=[str(R/'laboratorio_fivem/work/pydeps'),r'C:/Users/erons/Documents/Codex/2026-10-02/projeto-fivem-3d/work/deps']
from szio.rpf import open_rpf
data=F/'data';data.mkdir(exist_ok=True)
points=[list(map(lambda x:float(x.replace(',','.')),line.split())) for line in (P/'solo_validado.tsv').read_text(encoding='utf-8-sig').splitlines()]
destinations={}
for label,index,heading in [('pista',0,90),('porto',2,120),('mansao',3,180)]:
    x,y,z=points[index];destinations[label]=dict(x=x,y=y,z=z+1.15,ground_z=z,heading=heading)
maps=sorted(f.stem for f in S.glob('cv_*.ymap'))
cfg=dict(revision='cayo-vizinha-20261009-1',offset=dict(x=-1300,y=5200,z=0),maps=maps,
    bounds=dict(minX=1750,maxX=4750,minY=-1700,maxY=1700),destinations=destinations,
    sentinels=['h4_mph4_ter01_01','h4_mph4_ter02_terr_01','h4_prop_tree_palm_areca_sap_02','h4_dlc_island_office'])
(data/'config.json').write_text(json.dumps(cfg,indent=2))
types=sorted(f.name for f in S.glob('*.ytyp'))
text="fx_version 'cerulean'\ngame 'gta5'\nauthor 'Minha Cidade'\ndescription 'Cayo Perico original deslocada a leste da ilha autoral'\nversion '1.0.0'\nthis_is_a_map 'yes'\ndependencies { 'teste_ilha', '/gameBuild:2189' }\nfiles { 'data/config.json', 'data/mph4_gtxd.ymt', 'stream/*.ytyp' }\ndata_file 'GTXD_PARENTING_DATA' 'data/mph4_gtxd.ymt'\nclient_script 'client.lua'\nserver_script 'server.lua'\n"
text+=''.join("data_file 'DLC_ITYP_REQUEST' 'stream/"+name+"'\n" for name in types)
(F/'fxmanifest.lua').write_text(text)
q=next(q for q in json.loads((P/'catalogo.json').read_text()) if q['file']=='mph4_gtxd.ymt')
parts=q['archive'].split('|');a=open_rpf(parts[0])
for s in parts[1:]:a=a.open_nested(s)
(data/'mph4_gtxd.ymt').write_bytes(a.read_bytes(q['file']))
print('CONFIG',len(maps),'mapas',len(types),'tipos',destinations,flush=True)
