fx_version 'cerulean'
game 'gta5'
author 'Minha Cidade'
description 'Primeiro personagem e comandos locais de desenvolvimento'
version '0.1.0'
dependency 'spawnmanager'
dependency 'cidade_admin'
client_scripts { 'client.lua', 'vehicles.lua', 'sandbox.lua', 'combat_mounts.lua', 'combat_weapon.lua', 'posture_movement.lua', 'prone.lua', 'cover.lua', 'sertao_turret.lua', 'characters.lua' }
files { 'data/cartelking_peds.meta' }
data_file 'PED_METADATA_FILE' 'data/cartelking_peds.meta'

files { 'data/sertao_vehicles.meta', 'data/sertao_variations.meta', 'stream/sertao_props.ytyp', 'data/jeepmilitar_vehicles.meta', 'data/jeepmilitar_variations.meta' }
data_file 'VEHICLE_METADATA_FILE' 'data/jeepmilitar_vehicles.meta'
data_file 'VEHICLE_VARIATION_FILE' 'data/jeepmilitar_variations.meta'
data_file 'DLC_ITYP_REQUEST' 'stream/sertao_props.ytyp'
data_file 'VEHICLE_METADATA_FILE' 'data/sertao_vehicles.meta'
data_file 'VEHICLE_VARIATION_FILE' 'data/sertao_variations.meta'
