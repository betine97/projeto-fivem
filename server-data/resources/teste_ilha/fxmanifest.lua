fx_version 'cerulean'
game 'gta5'
author 'Teste Ilha'
description 'Ilha autoral, mundo independente e entrada na pista de pouso'
version '1.0.0'
this_is_a_map 'yes'
replace_level_meta 'ilha'
files { 'ilha.meta', 'data/images.meta', 'data/water.xml', 'data/config.json', 'data/mapa.json', 'stream/teste_ilha.ytyp', 'ui/index.html', 'ui/mapa.png' }
data_file 'DLC_ITYP_REQUEST' 'stream/teste_ilha.ytyp'
files { 'stream/ti_nature.ytyp' }
files { 'data/mapas_originais.json' }
data_file 'DLC_ITYP_REQUEST' 'stream/ti_nature.ytyp'
data_file 'WATER_FILE' 'data/water.xml'
ui_page 'ui/index.html'
client_script 'client.lua'
dependency 'spawnmanager'
