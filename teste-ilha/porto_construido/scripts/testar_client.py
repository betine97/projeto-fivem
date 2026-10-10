"""Exercise teleport success, failure rollback, vehicles and cleanup using native mocks."""
import sys,json
from pathlib import Path
O=Path(__file__).resolve().parents[1];R=O.parent.parent;sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from lupa import LuaRuntime
cfg=json.loads((O/'fivem/data/config.json').read_text())
cases=[]
for mode in ['success','collision_failure','prepare_failure','vehicle']:
    lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals();calls=[];commands={};events={}
    def tab(v):
        if isinstance(v,dict):return lua.table_from({k:tab(x) for k,x in v.items()})
        if isinstance(v,list):return lua.table_from([tab(x) for x in v])
        return v
    g.json=lua.table_from(dict(decode=lambda _:tab(cfg),encode=lambda _: '{}'))
    g.GetCurrentResourceName=lambda:'porto_esperanca';g.LoadResourceFile=lambda *a:''
    g.RegisterCommand=lambda n,f,*a:commands.__setitem__(n,f)
    g.AddEventHandler=lambda n,f:events.__setitem__(n,f)
    g.CreateThread=lambda f:None;g.PlayerPedId=lambda:7;g.PlayerId=lambda:1
    g.GetEntityCoords=lambda ped:tab(dict(x=-441,y=-87,z=19.15));g.GetEntityHeading=lambda ped:90
    g.IsPedInAnyVehicle=lambda *a:mode=='vehicle';g.GetResourceState=lambda n:'stopped'
    g.exports=lua.eval('{teste_ilha={prepareSpawn=function() end}}')
    if mode=='prepare_failure':g.exports=lua.eval('{teste_ilha={prepareSpawn=function() error("failed water export") end}}')
    timer=[0];g.GetGameTimer=lambda:timer[0]
    def wait(ms):timer[0]+=ms
    g.Wait=wait;g.GetHashKey=lambda n:n;g.GetGroundZFor_3dCoord=lambda *a:(mode=='success',4.83)
    g.HasCollisionLoadedAroundEntity=lambda p:mode=='success'
    for name in ['BeginTextCommandThefeedPost','AddTextComponentSubstringPlayerName','EndTextCommandThefeedPostTicker','ClearFocus','NewLoadSceneStop','ShutdownLoadingScreen','ShutdownLoadingScreenNui','RenderScriptCams','SetEntityVisible','SetPlayerControl','SetEntityCollision','SetEntityHasGravity','FreezeEntityPosition','DoScreenFadeIn','DoScreenFadeOut','TriggerEvent','RequestIpl','RequestModel','SetFocusPosAndVel','NewLoadSceneStartSphere','SetEntityCoordsNoOffset','RequestCollisionAtCoord','SetEntityHeading','SetEntityVelocity','SetModelAsNoLongerNeeded','print']:
        setattr(g,name,lambda *a,n=name:calls.append((n,a)))
    lua.execute((O/'fivem/client.lua').read_text());commands['porto']()
    if mode=='success':
        assert any(n=='SetEntityCoordsNoOffset' and abs(a[1]-242)<.01 and abs(a[3]-5.98)<.01 for n,a in calls)
    elif mode!='vehicle':
        assert any(n=='SetEntityCoordsNoOffset' and a[1:4]==(-441,-87,19.15) for n,a in calls),mode
    if mode!='vehicle':
        assert any(n=='FreezeEntityPosition' and a==(7,False) for n,a in calls),mode
        assert any(n=='SetPlayerControl' and a==(1,True,0) for n,a in calls),mode
        assert any(n=='SetEntityHasGravity' and a==(7,True) for n,a in calls),mode
        assert 'onClientResourceStop' in events
        # Busy is released, so a second invocation must run as well.
        count=len(calls);commands['porto']();assert len(calls)>count
    else:assert not any(n=='SetEntityCoordsNoOffset' for n,a in calls)
    cases.append(dict(name=mode,passed=True))
for file in ['client.lua','server.lua']:
    lua=LuaRuntime();syntax=lua.eval('function(s) return load(s) ~= nil end')((O/'fivem'/file).read_text());assert syntax
    cases.append(dict(name='syntax_'+file,passed=True))
(O/'dados/testes_client.json').write_text(json.dumps(dict(passed=True,cases=cases,uses_native_mocks=True,in_game_verified=False),indent=2));print('CLIENT_TESTS_PASSED',len(cases))
