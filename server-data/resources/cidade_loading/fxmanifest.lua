fx_version 'cerulean'
game 'gta5'

author 'Minha Cidade'
description 'Carregamento com playlist e entrada confirmada pelo jogador'
version '1.0.0'

loadscreen 'web/index.html'
loadscreen_cursor 'yes'
loadscreen_manual_shutdown 'yes'
-- The loadingScreen frame loses input behind other resource frames after startup.
-- Continue in a regular NUI frame, which can own mouse/keyboard focus.
ui_page 'web/index.html?interactive=1'

client_script 'client.lua'
server_script 'diagnostics_server.lua'
files {
    'web/index.html',
    'web/style.css',
    'web/app.js',
    'web/playlist.json',
    'web/assets/background.png',
    'web/audio/*.mp3'
}
