"""Check initial entry under delayed/missing floor, model failure and stale camera.

Native mocks verify lifecycle invariants; they do not verify GTA rendering.
"""
from pathlib import Path
import sys,json
O=Path(__file__).resolve().parents[1];R=O.parent.parent
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from lupa import LuaRuntime
source=(R/'server-data/resources/cidade_core/client.lua').read_text(encoding='utf8')
cases=[]
for mode in ['loaded','late_floor','missing_floor','wrong_floor','model_timeout','prepare_error','stale_camera']:
    lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals()
    commands={};threads=[];calls=[];timer=[0];ped=[1];frozen={};gravity={}
    def tab(v):return lua.table_from(v)
    position={'x':-441.6,'y':-87.76,'z':19.15}
    g.RegisterCommand=lambda n,f,*a:commands.__setitem__(n,f)
    g.AddEventHandler=lambda *a:None
    g.CreateThread=lambda f:threads.append(f)
    g.ExecuteCommand=lambda n:commands[n]() if n in commands else None
    g.GetConvar=lambda *a:'ilha';g.GetResourceState=lambda n:'started' if n in ['teste_ilha','porto_esperanca'] else 'stopped'
    g.GetCurrentResourceName=lambda:'cidade_core';g.NetworkIsSessionStarted=lambda:True
    g.PlayerId=lambda:5;g.PlayerPedId=lambda:ped[0]
    g.GetEntityCoords=lambda *a:tab(position)
    g.GetGameplayCamCoord=lambda:tab(position)
    g.GetGameTimer=lambda:timer[0]
    g.GetHashKey=lambda s:123
    g.HasModelLoaded=lambda *a:mode!='model_timeout'
    g.IsPedInAnyVehicle=lambda *a:False
    g.DoesEntityExist=lambda *a:True
    g.IsScreenFadedOut=lambda:mode=='stale_camera'
    g.IsScreenFadingOut=lambda:False
    g.IsPlayerSwitchInProgress=lambda:mode=='stale_camera'
    g.IsGameplayCamRendering=lambda:mode!='stale_camera'
    g.HasCollisionLoadedAroundEntity=lambda *a:True # Deliberately true even without a floor.
    def ground(*a):
        return (mode not in ['missing_floor'] and (mode!='late_floor' or timer[0]>=400),30.0 if mode=='wrong_floor' else 18.0)
    g.GetGroundZFor_3dCoord=ground
    def native(name,*args):
        calls.append((name,args))
        if name=='FreezeEntityPosition':frozen[args[0]]=args[1]
        if name=='SetEntityHasGravity':gravity[args[0]]=args[1]
        if name in ['SetPlayerModel','NetworkResurrectLocalPlayer']:ped[0]+=1
        if name=='SetEntityCoordsNoOffset':position.update(zip(['x','y','z'],args[1:4]))
    def wait(ms):
        # Every yielding setup step must protect the current ped from falling.
        if not any(n=='DoScreenFadeIn' for n,_ in calls):
            assert frozen.get(ped[0]) is True and gravity.get(ped[0]) is False,(mode,ped[0],calls[-3:])
        timer[0]+=max(ms,1)
    g.Wait=wait
    names=['BeginTextCommandThefeedPost','AddTextComponentSubstringPlayerName','EndTextCommandThefeedPostTicker',
           'FreezeEntityPosition','SetEntityHasGravity','SetEntityInvincible','SetEntityVelocity',
           'TriggerEvent','RequestModel','SetPlayerModel','SetModelAsNoLongerNeeded',
           'SetPedDefaultComponentVariation','RequestIpl','SetEntityCoordsNoOffset',
           'NetworkResurrectLocalPlayer','SetEntityCollision','ClearPedTasksImmediately',
           'SetEntityHeading','SetFocusPosAndVel','NewLoadSceneStartSphere','RequestCollisionAtCoord',
           'SetEntityMaxHealth','SetEntityHealth','SetMaxWantedLevel','ClearPlayerWantedLevel',
           'NewLoadSceneStop','ShutdownLoadingScreen','ShutdownLoadingScreenNui',
           'StopPlayerSwitch','RenderScriptCams','ClearFocus','SetGameplayCamRelativeHeading',
           'SetGameplayCamRelativePitch','SetEntityVisible','SetPlayerControl',
           'DoScreenFadeIn','SetPlayerInvincible','TriggerServerEvent','print']
    for name in names:setattr(g,name,lambda *a,n=name:native(n,*a))
    g.json=tab({'encode':lambda *a:'{}'})
    # FiveM exposes exports both as a callable registration table and as
    # resource namespaces. Model both forms so the real client.lua is tested.
    g.exports=lua.eval('setmetatable({teste_ilha={getSpawn=function() return {x=-441.6,y=-87.76,z=19.15,heading=90,model="a_m_y_business_01"} end,prepareSpawn=function() end},spawnmanager={setAutoSpawn=function() end}},{__call=function(t,n,f)t[n]=f end})')
    def prepare(*a):
        assert frozen.get(ped[0]) and gravity.get(ped[0]) is False
        wait(100)
        if mode=='prepare_error':raise RuntimeError('preparation failed')
    g.exports.teste_ilha.prepareSpawn=prepare
    lua.execute(source)
    # Run the actual startup thread, then its dispatched entry routine.
    threads[0]();threads[-1]()
    safe=mode in ['loaded','late_floor','stale_camera']
    assert any(n=='ShutdownLoadingScreen' for n,a in calls)
    assert any(n=='ShutdownLoadingScreenNui' for n,a in calls)
    assert any(n=='RenderScriptCams' and a[0] is False for n,a in calls)
    assert any(n=='DoScreenFadeIn' for n,a in calls)
    assert frozen.get(ped[0]) is (not safe),(mode,frozen)
    assert gravity.get(ped[0]) is safe,(mode,gravity)
    assert any(n=='TriggerEvent' and a[0]=='playerSpawned' for n,a in calls) is safe
    if safe:assert abs(position['z']-19.15)<.001
    if mode=='stale_camera':assert any(n=='StopPlayerSwitch' for n,a in calls)
    # A failure must not leave the retry lock set.
    before=len(threads);commands['recuperartela']();threads[-1]()
    assert len(threads)>before
    cases.append({'name':mode,'passed':True})
(O/'dados/testes_entrada.json').write_text(json.dumps({'passed':True,'cases':cases,'uses_native_mocks':True,'in_game_verified':False},indent=2))
print('ISLAND_ENTRY_TESTS_PASSED',len(cases))
