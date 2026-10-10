"""Execute the real loading/core Lua together with simulated FiveM natives.

Checks manual entry, native collision failures, retry, cleanup and both modes.
This does not assert in-game rendering or CEF behavior.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'casa_vinewood/work/lua_syntax_deps'))
from lupa import LuaRuntime

BOOT = r'''
S={now=0,ped=1,collision=true,network=true,active=true,loading=true,mode='ilha',
 position={x=0,y=0,z=0},threads={},events={},commands={},callbacks={},exportFns={},
 frozen={},control=true,shutdowns=0,resource='cidade_loading',spawnFinished=false}
function nativeFlag(value) if S.numeric then return value and 1 or 0 end;return value end
json={encode=function() return '{}' end}
function GetGameTimer()return S.now end
function Wait(ms)return coroutine.yield(ms or 0)end
function CreateThread(fn)table.insert(S.threads,{co=coroutine.create(fn),wake=S.now,resource=S.resource})end
function AddEventHandler(name,fn)S.events[name]=S.events[name] or {};table.insert(S.events[name],fn)end
function TriggerEvent(name,...)for _,fn in ipairs(S.events[name] or {})do fn(...)end end
function RegisterCommand(name,fn)S.commands[name]=fn end
function ExecuteCommand(name)if S.commands[name]then S.commands[name]()end end
function RegisterNUICallback(name,fn)S.callbacks[name]=fn end
function GetCurrentResourceName()return S.resource end
function GetResourceState(name)
 if name=='cidade_loading'then return S.loading and 'started' or 'stopped'end
 if name=='cidade_core' or name=='teste_ilha'then return 'started'end
 return 'stopped'
end
function GetConvar()return S.mode end
function GetIsLoadingScreenActive()return nativeFlag(S.active) end
function NetworkIsSessionStarted()return nativeFlag(S.network) end
function NetworkIsPlayerActive()return nativeFlag(S.network) end
function PlayerPedId()return S.ped end
function PlayerId()return 0 end
function DoesEntityExist(p)return nativeFlag(p and p>0) end
function HasCollisionLoadedAroundEntity()return nativeFlag(S.collision) end
function IsEntityDead()return nativeFlag(S.dead==true) end
function IsPedInAnyVehicle()return false end
function IsPlayerSwitchInProgress()return false end
function IsScreenFadedOut()return false end
function IsScreenFadingOut()return false end
function IsGameplayCamRendering()return true end
function GetGameplayCamCoord()return S.position end
function GetEntityCoords()return S.position end
function GetGroundZFor_3dCoord()return S.collision,S.spawn.z-1.15 end
function GetHashKey()return 1 end
function HasModelLoaded()return true end
function SetPlayerModel()S.ped=S.ped+1 end
function SetEntityCoordsNoOffset(_,x,y,z)S.position={x=x,y=y,z=z}end
function FreezeEntityPosition(p,v)S.frozen[p]=v end
function SetEntityHasGravity(_,v)S.gravity=v end
function SetEntityInvincible(_,v)S.invincible=v end
function SetPlayerControl(_,v)S.control=v end
function SetNuiFocus(focus,cursor)S.nuiFocus=focus;S.cursor=cursor;S.focusCalls=(S.focusCalls or 0)+1 end
function SendNUIMessage(message)S.lastUiMessage=message end
function ShutdownLoadingScreenNui()S.shutdowns=S.shutdowns+1 end
function ShutdownLoadingScreen()S.active=false end
function print()end
exports=setmetatable({
 teste_ilha={getSpawn=function()return S.spawn end,prepareSpawn=function()return true end},
 spawnmanager={setAutoSpawn=function()end,spawnPlayer=function(_,p,cb)S.position=p;cb()end},
}, {__call=function(_,name,fn)
 S.exportFns[S.resource]=S.exportFns[S.resource] or {};S.exportFns[S.resource][name]=fn
end,__index=function(_,name)return S.exportFns[name]end})
-- Irrelevant display/health/camera native calls are recorded as no-ops.
setmetatable(_G,{__index=function(_,name)
 if name:match('^[A-Z]') then local fn=function()end;rawset(_G,name,fn);return fn end
end})
function tick(ms)
 local stop=S.now+ms
 while S.now<stop do
  for _,t in ipairs(S.threads)do
   if coroutine.status(t.co)~='dead' and t.wake<=S.now then
    S.resource=t.resource
    local ok,delay=coroutine.resume(t.co)
    if not ok then error(delay)end
    t.wake=S.now+(tonumber(delay) or 0)
   end
  end
  S.now=S.now+50
 end
end
function callback(name,data)
 S.resource='cidade_loading';S.response=nil
 S.callbacks[name](data or {},function(value)S.response=value end)
 return S.response
end
'''

cases = []
def environment(mode='ilha', collision=True, loading=True, active=True, numeric=False):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(BOOT)
    state = lua.globals().S
    spawn = json.loads((ROOT/'server-data/resources/teste_ilha/data/config.json').read_text())['spawn']
    state.spawn = lua.table_from(spawn)
    state.mode, state.collision, state.loading, state.active = mode, collision, loading, active
    state.numeric = numeric
    for resource in (['cidade_loading'] if loading else []) + ['cidade_core']:
        state.resource = resource
        lua.execute((ROOT/f'server-data/resources/{resource}/client.lua').read_text(encoding='utf-8-sig'))
    return lua, state

def status(lua):
    return lua.globals().callback('loadingStatus')

for mode in ['ilha','cidade']:
    lua, s = environment(mode)
    assert not lua.globals().callback('loadingAdvance')['ok']
    lua.globals().tick(50)
    lua.globals().tick(5000)
    assert status(lua)['ready'] and status(lua)['holding'], mode
    assert s.shutdowns == 0 and not s.control and s.frozen[s.ped], mode
    lua.globals().tick(60000)
    assert s.shutdowns == 0 and status(lua)['holding']
    assert lua.globals().callback('loadingAdvance')['ok']
    assert not lua.globals().callback('loadingAdvance')['ok']
    lua.globals().tick(450)
    assert s.shutdowns == 0 and not s.control
    lua.globals().tick(250)
    assert s.shutdowns == 1 and s.control and not s.frozen[s.ped] and s.gravity
    assert not status(lua)['holding']
    cases.append(f'{mode}: impede entrada antecipada, espera sem timeout, aceita um clique e libera o personagem')

lua, s = environment(collision=False)
lua.globals().tick(25000)
assert status(lua)['failed'] and not status(lua)['ready'] and s.shutdowns == 0
assert s.frozen[s.ped] and not s.control
s.collision = True
assert lua.globals().callback('loadingRetry')['ok']
lua.globals().tick(5000)
assert status(lua)['ready'] and s.shutdowns == 0
cases.append('solo ausente mantém proteção e nova tentativa recupera o spawn')

lua, s = environment()
lua.globals().tick(5000)
s.collision = False
assert not lua.globals().callback('loadingAdvance')['ok']
assert status(lua)['failed'] and s.shutdowns == 0
cases.append('perda de colisão entre pronto e clique bloqueia a liberação')

lua, s = environment()
lua.globals().tick(5000)
s.resource = 'cidade_loading'
lua.globals().TriggerEvent('onClientResourceStop','cidade_loading')
assert s.control and not s.frozen[s.ped] and s.shutdowns == 1
cases.append('parada do recurso limpa foco e proteção sem deixar o jogador preso')

lua, s = environment(loading=False)
lua.globals().tick(5000)
assert s.shutdowns > 0 and s.control and not s.frozen[s.ped]
cases.append('servidor sem o recurso mantém o fluxo anterior')

lua, s = environment(active=False)
lua.globals().tick(5000)
assert not status(lua)['holding'] and s.control and not s.frozen[s.ped]
cases.append('reiniciar um recurso em uma sessão já aberta não prende o jogador sem tela')

lua, s = environment(numeric=True)
lua.globals().tick(5000)
assert status(lua)['ready'] is True and status(lua)['holding'] is True
s.collision = False
assert not lua.globals().callback('loadingAdvance')['ok']
assert status(lua)['failed'] is True and status(lua)['ready'] is False
s.collision = True
s.dead = True
assert lua.globals().exports.cidade_loading.markReady() is False
s.dead = False
assert lua.globals().exports.cidade_loading.markReady() is True
cases.append('nativos 1/0 viram booleanos JSON; colisão zero e personagem morto continuam bloqueados')

lua, s = environment(active=False, numeric=True)
lua.globals().tick(5000)
assert status(lua)['holding'] is False and s.control
cases.append('loading nativo zero não congela uma sessão já aberta')

lua, s = environment()
lua.globals().tick(5000)
assert lua.globals().callback('loadingUiReady')['ok']
assert s.shutdowns == 0 and not s.nuiFocus
handoff = lua.table_from({'progress':95,'audio':lua.table_from({'index':1,'time':12.75,'volume':.67,'muted':True,'paused':True})})
assert lua.globals().callback('loadingHandoff',handoff)['ok']
assert s.lastUiMessage.eventName == 'cidadeLoadingActivate'
assert s.lastUiMessage.audio.time == 12.75 and s.lastUiMessage.audio.paused
assert s.shutdowns == 0 and not s.control
assert lua.globals().callback('loadingUiActive')['ok']
lua.globals().tick(200)
assert s.shutdowns == 1 and s.nuiFocus and s.cursor and s.focusCalls == 1
assert status(lua)['holding'] and not s.control and s.frozen[s.ped]
lua.globals().tick(5000)
assert s.focusCalls == 1  # Never re-focus every frame and swallow clicks.
assert lua.globals().callback('loadingAdvance')['ok']
lua.globals().tick(700)
assert s.shutdowns == 1 and s.control and not s.nuiFocus and not s.cursor
assert s.lastUiMessage.eventName == 'cidadeLoadingClose'
cases.append('transferência mantém áudio/proteção, aguarda interface visível e dá foco uma vez; clique libera e limpa')

lua, s = environment()
lua.globals().tick(5000)
lua.globals().callback('loadingUiReady')
lua.globals().tick(1800)
assert s.lastUiMessage.eventName == 'cidadeLoadingActivate'
assert status(lua)['holding'] and not s.control and s.shutdowns == 0
lua.globals().callback('loadingUiActive')
lua.globals().tick(200)
assert s.nuiFocus and s.shutdowns == 1 and status(lua)['holding']
cases.append('sem resposta do áudio a interface ainda abre, sem avanço automático do personagem')

lua = LuaRuntime()
syntax = lua.eval('function(s) local f,e=load(s);return f~=nil,e end')
for relative in ['cidade_loading/client.lua','cidade_loading/fxmanifest.lua','cidade_core/client.lua','porto_esperanca/client.lua']:
    ok, error = syntax((ROOT/'server-data/resources'/relative).read_text(encoding='utf-8-sig'))
    assert ok, error
cases.append('sintaxe de todos os Lua alterados')

media = [
 ('C:/Users/erons/AppData/Local/Temp/codex-clipboard-fbd7dcab-5721-41e9-a0ee-d2b8344614e6.png','assets/background.png'),
 ('C:/Users/erons/Downloads/YTDown.com_YouTube_Media_ilfYnhXD-bE_Breaking-Bad-Main-Title-Theme-Extended_001_1080p.mp3','audio/faixa-01.mp3'),
 ('C:/Users/erons/Downloads/YTDown.com_YouTube_Media_ilfYnhXD-bE_Breaking-Bad-Main-Title-Theme-Extended_001_1080p_2.mp3','audio/faixa-02.mp3'),
 ('C:/Users/erons/Downloads/YTDown.com_YouTube_Media_ilfYnhXD-bE_Breaking-Bad-Main-Title-Theme-Extended_001_1080p_1.mp3','audio/faixa-03.mp3'),
]
hashes=[]
for original, copied in media:
    a=hashlib.sha256(Path(original).read_bytes()).hexdigest()
    b=hashlib.sha256((ROOT/'server-data/resources/cidade_loading/web'/copied).read_bytes()).hexdigest()
    assert a==b
    hashes.append({'source':original,'asset':copied,'sha256':a})
cases.append('background e três músicas copiados sem alteração')
for mode in ['ilha','cidade']:
    cfg=(ROOT/f'server-data/server-{mode}.cfg').read_text(encoding='utf-8-sig')
    assert cfg.count('ensure cidade_loading')==1
    assert cfg.index('ensure cidade_loading') < cfg.index('ensure cidade_core')
cases.append('recurso inicia antes do personagem nos dois modos')
out=ROOT/'carregamento_cidade_20261009/verificacao/fluxo.json'
out.write_text(json.dumps({'passed':True,'cases':cases,'media':hashes,'native_mocks':True,'in_game_verified':False},ensure_ascii=False,indent=2),encoding='utf-8')
print('FLOW_PASS',len(cases))
