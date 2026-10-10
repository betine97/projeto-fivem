fx_version 'cerulean'
game 'gta5'
this_is_a_map 'yes'
author 'Minha Cidade'
description 'Identidade Cayo em toda a ilha, cidade principal e quatro vilarejos'
version '1.0.0'
dependencies { 'teste_ilha', 'cayo_vizinha', 'porto_esperanca' }
files { 'data/config.json', 'stream/natureza_integrada.ytyp', 'stream/ni_groundcover.ytyp' }
data_file 'DLC_ITYP_REQUEST' 'stream/natureza_integrada.ytyp'
data_file 'DLC_ITYP_REQUEST' 'stream/ni_groundcover.ytyp'
client_script 'client.lua'
server_script 'server.lua'
