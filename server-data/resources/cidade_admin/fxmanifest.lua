fx_version 'cerulean'
game 'gta5'
author 'Minha Cidade'
description 'Administracao por ID permanente e ajuda no F8'
dependency 'cidade_acesso'
ui_page 'ui/index.html'
files {
    'ui/index.html', 'ui/style.css', 'ui/app.js', 'ui/catalog.json',
    'ui/fallback.svg', 'ui/vehicles/*', 'ui/weapons/*', 'ui/peds/*',
    'ui/cayo.json', 'ui/cayo/*', 'data/editor_terrain.json'
}
shared_script 'catalogo.lua'
shared_script 'captured_catalog.lua'
server_script 'server.lua'
server_script 'panel_server.lua'
server_script 'island_server.lua'
client_script 'client.lua'
client_script 'panel_client.lua'
client_script 'island_client.lua'
