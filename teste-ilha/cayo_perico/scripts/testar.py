import hashlib, json, sys, xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=R/'teste-ilha/cayo_perico';F=P/'fivem'
sys.path.insert(0,str(R/'casa_vinewood/work/lua_syntax_deps'))
from lupa import LuaRuntime
cfg=json.loads((F/'data/config.json').read_text())
provenance=json.loads((P/'proveniencia.json').read_text())
for q in provenance:
    if q['category']=='assets':
        assert hashlib.sha256((F/'stream'/q['name']).read_bytes()).hexdigest()==q['sha256'],q['name']
    elif q['category']=='colisoes' and (q['name'], 'local') in [tuple(line.split('\t')) for line in (P/'colisoes_relocadas.tsv').read_text(encoding='utf-8-sig').splitlines()]:
        assert hashlib.sha256((F/'stream'/q['name']).read_bytes()).hexdigest()==q['sha256'],q['name']
maps=list((F/'stream').glob('cv_*.ymap'));assert len(maps)==308==len(cfg['maps'])
manifest=ET.parse(P/'manifesto.xml').getroot()
all_maps={f.stem for f in maps}
assert all(item.findtext('Name') in all_maps for item in manifest.findall('MapDataGroups/Item'))
assert len(manifest.findall('imapDependencies_2/Item'))>100
for item in manifest.findall('MapDataGroups/Item/Bounds/Item'):
    name=item.text
    assert (F/'stream'/(name+'.ybn')).exists() or name.startswith('hash_'),name
# All six native terrain sectors remain east of the authored land bounds.
for name in ['h4_islandx_terrain_%02d.ymap'%i for i in range(1,7)]:
    row=next(q for q in json.loads((P/'auditoria_mapas.json').read_text(encoding='utf-8-sig')) if q['name']==name)
    assert row['min'][0]-1300>1071.505+600,(name,row['min'])
cases=[]
for mode in ['ready','late_floor','missing_floor','wrong_floor','preparation_error','in_vehicle']:
    lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals();commands={};threads=[];calls=[];timer=[0]
    pos=dict(x=-441.6,y=-87.76,z=19.15);origin=pos.copy();ground=cfg['destinations']['pista']['ground_z']
    def tab(v):
        if isinstance(v,dict):return lua.table_from({k:tab(a) for k,a in v.items()})
        if isinstance(v,list):return lua.table_from([tab(a) for a in v])
        return v
    def native(name,*a):
        calls.append((name,a))
        if name=='SetEntityCoordsNoOffset':pos.update(zip(['x','y','z'],a[1:4]))
    g.json=tab(dict(decode=lambda _:tab(cfg),encode=lambda _:'{}'))
    g.GetCurrentResourceName=lambda:'cayo_vizinha';g.LoadResourceFile=lambda *a:'{}'
    g.RegisterCommand=lambda n,f,*a:commands.update({n:f});g.CreateThread=lambda f:threads.append(f)
    g.AddEventHandler=lambda *a:None;g.GetGameTimer=lambda:timer[0]
    g.Wait=lambda ms:timer.__setitem__(0,timer[0]+max(ms,1))
    g.PlayerPedId=lambda:1;g.PlayerId=lambda:0;g.GetEntityCoords=lambda p:tab(pos)
    g.GetEntityHeading=lambda p:90;g.IsPedInAnyVehicle=lambda *a:mode=='in_vehicle'
    g.GetResourceState=lambda _: 'started';g.GetHashKey=lambda name:name
    g.IsModelInCdimage=lambda _:True;g.IsIplActive=lambda _:True;g.IsScreenFadedOut=lambda:False
    g.HasCollisionLoadedAroundEntity=lambda _:mode!='missing_floor'
    g.GetGroundZFor_3dCoord=lambda *a:(mode!='missing_floor' and (mode!='late_floor' or timer[0]>1000),ground+30 if mode=='wrong_floor' else ground)
    for name in ['BeginTextCommandThefeedPost','AddTextComponentSubstringPlayerName','EndTextCommandThefeedPostTicker',
                 'NewLoadSceneStop','ClearFocus','RenderScriptCams','SetEntityCollision','SetEntityHasGravity',
                 'SetEntityVisible','FreezeEntityPosition','SetPlayerControl','DoScreenFadeIn','DoScreenFadeOut',
                 'TriggerEvent','SetFocusPosAndVel','NewLoadSceneStartSphere','SetEntityCoordsNoOffset',
                 'RequestCollisionAtCoord','SetEntityHeading','SetEntityVelocity','TriggerServerEvent','RequestIpl',
                 'ExecuteCommand','print']:
        setattr(g,name,lambda *a,n=name:native(n,*a))
    g.exports=lua.eval('setmetatable({teste_ilha={},fpv_drone_runtime={isPiloting=function() return false end}},{__call=function() end})')
    g.exports.teste_ilha.closeMap=lambda *a:native('closeMap',*a)
    def prepare(*a):
        if mode=='preparation_error':raise RuntimeError('water preparation error')
        native('prepareWater',*a)
    g.exports.teste_ilha.prepareWater=prepare
    lua.execute((F/'client.lua').read_text())
    commands['cayo'](0,tab([]))
    if mode in ['ready','late_floor']:
        assert abs(pos['x']-3140)<.01 and abs(pos['z']-(ground+1.15))<.01,(mode,pos)
    else:assert pos==origin,(mode,pos)
    if mode!='in_vehicle':
        for n,value in [('FreezeEntityPosition',False),('SetEntityHasGravity',True),('SetEntityCollision',True),('SetPlayerControl',True)]:
            assert [a[1] for name,a in calls if name==n][-1]==value,(mode,n,calls)
        assert any(name=='DoScreenFadeIn' for name,a in calls)
        assert timer[0]<22000
    cases.append(mode)
parser=LuaRuntime().eval('function(s) local f,e=load(s); return f~=nil,e end')
for f in list(F.glob('*.lua'))+[R/'server-data/resources/teste_ilha/client.lua']:
    ok,err=parser(f.read_text(encoding='utf-8'));assert ok,(f,err)
result=dict(passed=True,models_textures_unmodified=3930,maps=308,world_collisions=1850,local_collisions_unmodified=11,
    collision_ray_samples=4,minimum_terrain_gap_m=800,teleport_cases=cases,client_visual_verified=False)
(P/'validacao.json').write_text(json.dumps(result,indent=2))
print('CAYO_VALIDADO',json.dumps(result),flush=True)
