from pathlib import Path
import json,shutil,datetime
P=Path(__file__).resolve().parents[1];R=P.parent;S=R/'server-data';B=P/'backup_ativacao'
for relative in ['server-data/server.cfg','server-data/resources/cidade_core/client.lua','iniciar-cidade.ps1']:
 src=R/relative;out=B/relative;out.parent.mkdir(parents=True,exist_ok=True)
 if not out.exists():shutil.copy2(src,out)
# Retain the authored top-down map in the game UI, with its camera footprint.
shutil.copy2(P/'previews/ilha_mapa_superior.png',P/'fivem/ui/mapa.png')
(P/'fivem/data/mapa.json').write_text(json.dumps({'minX':-1650,'maxX':1650,'minY':-1650*1400/1800,'maxY':1650*1400/1800}))
original=(B/'server-data/server.cfg').read_text(encoding='utf-8-sig')
(S/'server-cidade.cfg').write_text('setr cidade_modo cidade\n'+original,encoding='utf-8')
keep=[]
maps={'cidade_mansao','cidade_laboratorio','cidade_castelo_livre','cidade_castelo_previa','cidade_hospital_carcer'}
for line in original.splitlines():
 if line.strip().startswith('#'):continue
 if line.strip().startswith('ensure ') and line.split()[1] in maps:continue
 if 'sv_hostname ' in line:line='sv_hostname "Teste Ilha | Mundo independente"'
 if 'sets sv_projectName ' in line:line='sets sv_projectName "Teste Ilha"'
 if 'sets sv_projectDesc ' in line:line='sets sv_projectDesc "Ilha autoral com praias, montanhas e rio"'
 if line.strip()=='ensure cidade_core':keep.append('ensure teste_ilha')
 keep.append(line)
(S/'server-ilha.cfg').write_text('# Mundo exclusivo da ilha. Cidade original em server-cidade.cfg.\nsetr cidade_modo ilha\n'+'\n'.join(keep).strip()+'\n',encoding='utf-8')
(S/'server.cfg').write_text('# Inicio padrao: ilha. Use iniciar-cidade-original.cmd para a cidade.\nexec server-ilha.cfg\n',encoding='utf-8')
client=R/'server-data/resources/cidade_core/client.lua';text=client.read_text(encoding='utf-8-sig')
old="    exports.spawnmanager:setAutoSpawn(false)\n    exports.spawnmanager:spawnPlayer(spawn, function()"
new="""    exports.spawnmanager:setAutoSpawn(false)
    local islandMode=GetConvar('cidade_modo','cidade')=='ilha'
    if islandMode then
        local deadline=GetGameTimer()+15000
        while GetResourceState('teste_ilha')~='started' and GetGameTimer()<deadline do Wait(100) end
        if GetResourceState('teste_ilha')~='started' then
            print('[Teste Ilha] ERRO: recurso da ilha nao iniciou. Inicio na cidade bloqueado; reconecte apos corrigir o servidor.')
            return
        end
        spawn=exports.teste_ilha:getSpawn()
        exports.teste_ilha:prepareSpawn()
    end
    exports.spawnmanager:spawnPlayer(spawn, function()"""
if 'local islandMode=' not in text:
 assert old in text,'Spawn original nao localizado';text=text.replace(old,new,1)
oldmsg="        message('Bem-vindo! Abra F8 e digite ajuda para ver os comandos.')"
newmsg="""        if islandMode then
            local ped=PlayerPedId();FreezeEntityPosition(ped,true)
            local deadline=GetGameTimer()+15000
            while not HasCollisionLoadedAroundEntity(ped) and GetGameTimer()<deadline do
                RequestCollisionAtCoord(spawn.x,spawn.y,spawn.z);Wait(50)
            end
            if HasCollisionLoadedAroundEntity(ped) then
                FreezeEntityPosition(ped,false)
                message('Bem-vindo a ilha! F8: admin | voar | ilha | mapailha. Voce iniciou na pista de pouso.')
            else
                print('[Teste Ilha] ERRO: colisao da pista ainda nao carregou. Personagem protegido de queda. F8: ilha para tentar novamente; ilhadiag para diagnosticar.')
            end
        else
            message('Bem-vindo! Abra F8 e digite ajuda para ver os comandos.')
        end"""
if 'Bem-vindo a ilha!' not in text:
 assert oldmsg in text;text=text.replace(oldmsg,newmsg,1)
client.write_text(text,encoding='utf-8')
shutil.copytree(P/'fivem',S/'resources/teste_ilha',dirs_exist_ok=True)
launcher=R/'iniciar-cidade.ps1';s=launcher.read_text(encoding='utf-8-sig')
if '[ValidateSet' not in s:
 s="param([ValidateSet('ilha','cidade')][string]$Modo='ilha')\n"+s
 s=s.replace("try { & $serverExe +exec server.cfg } finally { Pop-Location }","$taskConfig = if ($Modo -eq 'cidade') { 'server-cidade.cfg' } else { 'server.cfg' }\nWrite-Host ('Modo: '+$Modo) -ForegroundColor Cyan\ntry { & $serverExe +exec $taskConfig } finally { Pop-Location }")
 launcher.write_text(s,encoding='utf-8-sig')
for name,mode in [('iniciar-ilha.cmd','ilha'),('iniciar-cidade-original.cmd','cidade')]:
 (R/name).write_text('@echo off\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar-cidade.ps1" -Modo '+mode+'\npause\n',encoding='ascii')
(P/'iniciar-ilha.cmd').write_text('@echo off\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\\iniciar-cidade.ps1" -Modo ilha\npause\n',encoding='ascii')
(P/'nativo/instalacao.json').write_text(json.dumps({'installed_at':datetime.datetime.now().astimezone().isoformat(),'default_mode':'ilha','installed_resource':'server-data/resources/teste_ilha','city_mode_config':'server-data/server-cidade.cfg','spawn':json.loads((P/'fivem/data/config.json').read_text())['spawn'],'in_game_verified':False},indent=2));print('ISLAND_INSTALLED_DEFAULT_SPAWN',flush=True)
