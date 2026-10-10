fx_version 'cerulean'
game 'gta5'
this_is_a_map 'yes'
files { 'stream/cidade_mansao.ytyp', 'auditoria_rotas.json', 'portas_madeira.json', 'luzes_pendentes.json' }
data_file 'DLC_ITYP_REQUEST' 'stream/cidade_mansao.ytyp'
client_script 'client.lua'
client_script 'auditoria_client.lua'
server_script 'auditoria_server.lua'

client_script 'movimento_interior.lua'
client_script 'portas_client.lua'
server_script 'portas_server.lua'

client_script 'luzes_pendentes.lua'

files { 'stream/mansao_decoracao.ytyp', 'decoracao_iluminacao.json' }
data_file 'DLC_ITYP_REQUEST' 'stream/mansao_decoracao.ytyp'
client_script 'iluminacao_decorativa.lua'

files { 'stream/mansao_vasos_autorais.ytyp' }
data_file 'DLC_ITYP_REQUEST' 'stream/mansao_vasos_autorais.ytyp'

files { 'iluminacao_ambiente.json' }

files { 'stream/mansao_cozinha_completa.ytyp' }
data_file 'DLC_ITYP_REQUEST' 'stream/mansao_cozinha_completa.ytyp'

files { 'stream/mansao_referencias.ytyp' }
data_file 'DLC_ITYP_REQUEST' 'stream/mansao_referencias.ytyp'

-- Script-owned props retain their scale and collision and share saved transforms.
files { 'objetos_catalogo.json' }
shared_script 'objetos_shared.lua'
server_script 'objetos_server.lua'
client_script 'objetos_client.lua'

files { 'stream/mansao_piano_tapetes.ytyp' }
data_file 'DLC_ITYP_REQUEST' 'stream/mansao_piano_tapetes.ytyp'
