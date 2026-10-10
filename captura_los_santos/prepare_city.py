"""Update only the isolated city's scripts/configuration, preserving capture data."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent;CITY=ROOT/'servidor-los-santos'
for name in ('secrets.cfg','acesso.cfg','permissoes-amigos.cfg'):
    shutil.copy2(ROOT/'server-data'/name,CITY/name)
for name in ('cidade_admin','cidade_acesso','cidade_captura'):
    shutil.copytree(ROOT/'server-data/resources'/name,CITY/'resources'/name,dirs_exist_ok=True)
p=CITY/'resources/cidade_admin/fxmanifest.lua'
p.write_text(p.read_text(encoding='utf8').replace("server_script 'island_server.lua'",'').replace("client_script 'island_client.lua'",''),encoding='utf8')
p=CITY/'resources/cidade_admin/panel_client.lua'
p.write_text(p.read_text(encoding='utf8').replace("RegisterCommand('editorilha',function()open('cayo')end,false)","RegisterCommand('editorilha',function()message('Use editorilha no servidor das ilhas: 127.0.0.1:30120. Aqui use capturarobjeto.')end,false)"),encoding='utf8')
print('LOS_SANTOS_PREPARADO',flush=True)
