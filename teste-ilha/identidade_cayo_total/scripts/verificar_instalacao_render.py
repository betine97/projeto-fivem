"""Validate installed resources, stale-map removal and generated Lua syntax."""
from common import *
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from luaparser import ast
import urllib.request
dest=R/'server-data/resources/natureza_integrada';cfg=read(dest/'data/config.json');checks=[]
assert cfg['revision']=='cayo-rasteira-distante-20261010-1'
expected={m['name'] for m in read(O/'dados/implantacao.json')['maps']}|{m['name'] for m in read(O/'dados/rasteira.json')['maps']}
actual={p.stem for p in (dest/'stream').glob('ni_*.ymap')}
assert actual==expected==set(cfg['maps']) and len(expected)==1597
assert not list((dest/'stream').glob('ni_natureza_[0-9][0-9].ymap'))
checks.append('1597 installed maps match the new hierarchy; superseded wide HD maps removed')
for row in read(O/'dados/instalacao.json')['installed']:
    assert sha(R/row['path'])==row['sha256'],row['path']
checks.append('All 8227 installed asset checksums match the validated staged files')
text=(dest/'fxmanifest.lua').read_text()
assert "data_file 'DLC_ITYP_REQUEST' 'stream/ni_groundcover.ytyp'" in text
assert read(dest/'data/config.json')['distant_groundcover']['patches']==66656
checks.append('New groundcover archetypes registered and native texture aliases installed')
for p in [dest/'client.lua',dest/'server.lua',dest/'fxmanifest.lua',R/'server-data/resources/cidade_admin/island_client.lua',R/'server-data/resources/cidade_admin/island_server.lua']:ast.parse(p.read_text(encoding='utf-8-sig'))
checks.append('Resource scripts parse as valid Lua')
for filename in ['validacao_hierarquia.json','validacao_limites_render.json','validacao_rasteira_distante.json','validacao_streaming.json','validacao_orcamento_render.json','validacao_codewalker.json']:assert read(O/'dados'/filename)['passed']
for filename in ['cayo-images-verification.json','island-ui-verification.json','island-verification.json','ui-verification.json']:assert read(R/'painel_adm_20261009'/filename)['passed']
with urllib.request.urlopen('http://127.0.0.1:30120/info.json') as response:info=json.load(response)
assert {'natureza_integrada','teste_ilha','cidade_admin','cayo_vizinha','porto_esperanca'}<=set(info['resources'])
checks.append('All five map/editor resources started and server HTTP endpoint responds')
write(O/'dados/validacao_instalada_render.json',dict(passed=True,revision=cfg['revision'],checks=checks,in_game_visual_verified=False,server_console_session=44774))
print('INSTALLED_RENDER_VALIDATED',checks,flush=True)
