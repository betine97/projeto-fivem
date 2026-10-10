fx_version 'cerulean'
game 'gta5'
this_is_a_map 'yes'

author 'Cidade local'
description 'Previa em escala real do novo castelo Rockford, com materiais externos convertidos'
version '1.0.0'
dependency 'cidade_castelo_livre'

files { 'stream/crf_castelo_previa.ytyp' }
data_file 'DLC_ITYP_REQUEST' 'stream/crf_castelo_previa.ytyp'

client_script 'client.lua'
server_script 'server.lua'
