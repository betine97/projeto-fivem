"""Regressions for held C, stationary idle, four-way prone and fast crouch.

Reuse the strict native simulator; these are controller checks, not a live GTA
physics/rendering test. Binary mover displacement is checked separately.
"""
import ast,json,math,sys,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];CORE=ROOT/'server-data/resources/cidade_core'
sys.path.insert(0,str(ROOT/'personagens/calca_tatica/test_deps'))
from lupa.lua54 import LuaRuntime
old=ast.parse((HERE.parent/'test_runtime.py').read_text(encoding='utf8'))
bootstrap_tree=ast.parse((HERE.parents[1]/'pipeline_animacoes/revisao_mao_esquerda/test_runtime_v6.py').read_text(encoding='utf8'))
bootstrap=next(ast.literal_eval(n.value.args[0]) for n in bootstrap_tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='execute')
names={'encode','setup','tick','settle','command','logs','check_errors','pose','standing'}
exec(compile(ast.Module(body=[n for n in old.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'strict_simulator','exec'),globals())
original_setup=setup
def setup():
    lua,S,M=original_setup()
    lua.execute('''
function GetAnimDuration(d,c)
 if d=='cidade_deitado_move_v11' then return c=='rastejar_bwd' and 31/30 or .9 end
 return 1.0
end
local originalTime=GetEntityAnimCurrentTime
function GetEntityAnimCurrentTime(p,d,c)
 local t=S.primary
 if t and t.dict==d and t.clip==c and t.flags&524288~=0 then return ((S.now-t.started)/(GetAnimDuration(d,c)*1000))%1 end
 return originalTime(p,d,c)
end
local originalRay=StartExpensiveSynchronousShapeTestLosProbe
function StartExpensiveSynchronousShapeTestLosProbe(x,y,z,xx,yy,zz,...)
 local h=originalRay(x,y,z,xx,yy,zz,...);S.rays[h].x=xx;return h
end
local originalResult=GetShapeTestResult
function GetShapeTestResult(h)
 local r=S.rays[h]
 if r and r.floor and S.stepFloor then
  local x=(S.pressed[35] and 1 or 0)-(S.pressed[34] and 1 or 0)
  local y=(S.pressed[32] and 1 or 0)-(S.pressed[33] and 1 or 0)
  return 2,true,vector3(r.x,r.y,(r.x*x+r.y*y>.15) and 1 or 0),vector3(0,0,1)
 end
 return originalResult(h)
end
''')
    return lua,S,M
checks=[];directions={32:'fwd',33:'bwd',34:'left',35:'right'}
for w in (101,102,103,900):
    lua,S,M=setup();S.weapon=w
    command(lua,S,'+cidade_ajoelhar');settle(lua,80);assert M.active and M.holdingC
    command(lua,S,'+cidade_ajoelhar');settle(lua,80);assert M.active,'Repeated down toggled crouch'
    for name,args in [('arma',('carabina','120')),('desarmar',()),('arma',('fuzil','120'))]:
        command(lua,S,name,args);settle(lua,80);assert M.active and S.movement=='move_ped_crouched'
    command(lua,S,'-cidade_ajoelhar');tick(lua)
    assert not M.active and not M.holdingC and S.movement is None and S.maxBlend==3
    command(lua,S,'+cidade_ajoelhar');settle(lua,80);assert M.active
    command(lua,S,'-cidade_ajoelhar');tick(lua);check_errors(S)
checks.append('C down/up independent of weapon, repeated down idempotent, draw/holster preserved, release restores standing')
lua,S,M=setup();S.missingSet=True
command(lua,S,'+cidade_ajoelhar');assert M.pending and M.holdingC
pending=S.commandThread;command(lua,S,'-cidade_ajoelhar');assert not M.pending
S.missingSet=False;lua.globals().oldPending=pending
lua.execute('local ok,e=coroutine.resume(oldPending);assert(ok,e)');settle(lua,80);assert not M.active
checks.append('C released during asset loading cancels the pending entry')
for w in (101,102,103):
    lua,S,M=setup();S.weapon=w;command(lua,S,'cidade_deitar');settle(lua,80)
    if w==103:
        pose(S,'parado');assert S.primary.flags&524288==0
    assert not M.crawling
    # Cached forward input must not move an idle keyboard player.
    S.normal[31]=-1;S.normal[30]=1;settle(lua,1200);assert not M.crawling
    for key,direction in directions.items():
        S.pressed[key]=True;settle(lua,100)
        assert M.crawling and M.crawlDirection==direction,(w,direction,logs(S)[-8:])
        assert S.primary.dict=='cidade_deitado_move_v11' and S.primary.clip=='rastejar_'+direction
        assert S.primary.flags&524288 and S.primary.flags&1 and S.primary.speed==1
        assert S.heading==0,'A/D turned instead of translating sideways'
        if w!=103:
            t=pose(S,'mira_rastejar_'+('bwd' if direction=='bwd' else 'fwd'),upper=True)
            assert t.flags&48==48
        count=len(S.tasks);settle(lua,1100);assert M.crawling and len(S.tasks)==count
        S.pressed[key]=False;tick(lua);assert not M.crawling
        settle(lua,80);pose(S,'parado' if w==103 else 'mira')
        assert S.primary.flags&524288==0 and S.secondary is None
    # Opposing movement keys cancel, including stale nonzero analog axes.
    S.pressed[32]=True;S.pressed[33]=True;settle(lua,80);assert not M.crawling
    S.pressed[32]=False;S.pressed[33]=False
    for name,args in [('arma',('fuzil','120')),('desarmar',()),('arma',('carabina','120'))]:
        command(lua,S,name,args);settle(lua,150);assert not M.crawling
    command(lua,S,'+cidade_ajoelhar');settle(lua,80);assert M.active
    command(lua,S,'-cidade_ajoelhar');settle(lua,80);standing(S,M);check_errors(S)
checks.append('idle with stale axes stays still; independent W/S/A/D, both rifles and unarmed; release stops the mover; opposing keys cancel')
for w in (101,102,103):
    lua,S,M=setup();S.weapon=w;command(lua,S,'+cidade_ajoelhar');settle(lua,80)
    S.pressed[21]=True
    for key,direction in directions.items():
        S.pressed[key]=True;settle(lua,100)
        clip='rapido_'+('livre_' if w==103 else 'armado_')+direction
        assert M.active and S.primary and S.primary.clip==clip,(w,direction,logs(S)[-8:])
        assert S.primary.dict=='cidade_agachado_move_v11' and S.primary.flags&524288
        count=len(S.tasks);settle(lua,1200);assert len(S.tasks)==count
        for k in (24,25,37,45):assert not S.disabled['0:'+str(k)],k
        S.pressed[key]=False;tick(lua);assert S.primary is None and M.active
    # Shift release and C release must each stop only their own mover task.
    S.pressed[32]=True;settle(lua,100);assert S.primary
    S.pressed[21]=False;tick(lua);assert S.primary is None and M.active
    S.pressed[21]=True;settle(lua,100);assert S.primary
    before=S.clear
    S.nativeReload=True;tick(lua);assert S.primary is None and M.active and S.clear==before
    S.nativeReload=False;settle(lua,100);assert S.primary
    command(lua,S,'-cidade_ajoelhar');tick(lua);assert S.primary is None and not M.active
    check_errors(S)
checks.append('Shift selects actual fast mover clips for all four directions armed/unarmed; movement/Shift/C release stops them; weapon controls remain native')
for crouched in (False,True):
  for direction,key in ((v,k) for k,v in directions.items()):
    for failure in ('wall','noFloor','stepFloor','slope','probeStuck','probeInvalid'):
        lua,S,M=setup();S.weapon=103
        command(lua,S,'+cidade_ajoelhar' if crouched else 'cidade_deitar');settle(lua,80)
        S[failure]=True;S.pressed[key]=True;S.pressed[21]=crouched;settle(lua,1000)
        assert not M.crawling and (not S.primary or S.primary.flags&524288==0),(crouched,direction,failure)
        check_errors(S)
checks.append('route probes gate both prone and fast crouch in every direction; pending/invalid/floor/obstacle queries fail closed')
for key in directions:
    lua,S,M=setup();command(lua,S,'cidade_deitar');settle(lua,80)
    S.pressed[key]=True;settle(lua,100);assert M.crawling
    for name,args in [('desarmar',()),('arma',('fuzil','120')),('arma',('carabina','120'))]:
        command(lua,S,name,args);settle(lua,150);assert M.crawling
    S.just=45;tick(lua);settle(lua,80)
    # A full magazine needs no reload; reduce it and try again.
    S.clip=20;S.just=45;tick(lua);settle(lua,80);assert not M.crawling;pose(S,'recarga')
    S.pressed[key]=False;settle(lua,2300);assert not M.crawling;pose(S,'mira')
    check_errors(S)
checks.append('draw/holster/rifle switch during each prone direction; reload pauses movement and release prevents automatic resumption')
# Retain the substantial aim/fire/reload suite from v10 unchanged.
body=old.body
start=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='reload_cycles' for t in n.targets))
end=next(i for i in range(start+1,len(body)) if isinstance(body[i],ast.Expr) and isinstance(body[i].value,ast.Call) and isinstance(body[i].value.func,ast.Attribute) and body[i].value.func.attr=='append')+1
exec(compile(ast.Module(body=body[start:end],type_ignores=[]),'retained_fire_reload_tests','exec'),globals())
for crouched in (False,True):
  for failure in ('dead','vehicle','ragdoll','swimming','paused','nui','noclip','ped_changed','stop','resource'):
    lua,S,M=setup();command(lua,S,'+cidade_ajoelhar' if crouched else 'cidade_deitar');settle(lua,80)
    S.pressed[32]=True;S.pressed[21]=True;settle(lua,100)
    if failure=='ped_changed':S.actor=3
    elif failure in ('stop','resource'):lua.globals().TriggerEvent('cidade:stopProne' if failure=='stop' else 'onResourceStop','cidade_core')
    else:S[failure]=True
    tick(lua);assert not M.active and not M.crawling and S.primary is None
    check_errors(S)
checks.append('twenty exit/interruption conditions stop locomotion and restore controls')
lua,S,M=setup();S.missingDict='cidade_agachado_move_v11'
command(lua,S,'+cidade_ajoelhar');settle(lua,5100);assert not M.active and not M.pending and not M.holdingC
lua,S,M=setup();S.missingDict='cidade_deitado_move_v11'
command(lua,S,'cidade_deitar');settle(lua,5100);assert S.primary is None and S.creates==0
checks.append('missing authored locomotion assets time out without latching posture or controls')
lua,S,M=setup();before=len(S.tasks)
for name in ('cidade_cobertura','cobertura','coberturainfo'):command(lua,S,name)
settle(lua,80);assert len(S.tasks)==before and not lua.globals().CidadeCover.active and S.disabled['0:44']
checks.append('cover remains removed and native cover input disabled')
report={'revision':M.revision,'game_tested':False,'strict_native_mocks':True,'checks':checks,
        'source_sha256':{n:hashlib.sha256((CORE/n).read_bytes()).hexdigest() for n in ('prone.lua','posture_movement.lua','sandbox.lua','cover.lua')}}
(HERE/'runtime_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('V11_RUNTIME_OK',json.dumps(checks,ensure_ascii=False))
