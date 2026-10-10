"""Checks real Lua wrist mount + diagnostic geometry with synthetic transforms.

Does not pretend these synthetic wrist matrices are captured FiveM samples.
"""
import ast
import hashlib
import json
import math
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'personagens/calca_tatica/test_deps'))
from lupa.lua54 import LuaRuntime
tree=ast.parse((HERE/'test_runtime_v6.py').read_text(encoding='utf8'))
bootstrap=next(ast.literal_eval(n.value.args[0]) for n in tree.body
               if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
               and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='execute')
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute(bootstrap)
lua.execute(r'''
S.wrist={vector3(1,0,0),vector3(0,1,0),vector3(0,0,1)}
S.up=vector3(0,0,1)
function GetPedBoneCoords(_,bone,x,y,z)
 if bone==18905 then return vector3(4,5,6) end
 return vector3(1,2,3)+S.wrist[1]*x+S.wrist[2]*y+S.wrist[3]*z
end
function GetEntityMatrix()return vector3(0,1,0),vector3(1,0,0),S.up,vector3(0,0,0) end
function CreateWeaponObject()return 2 end
function SetEntityMatrix(_,...)S.matrix={...} end
function SetPedCurrentWeaponVisible(_,visible)S.visible=visible end
function HasPedGotWeaponComponent()return false end
function GetPedWeaponTintIndex()return 0 end
''')
mount_source=ROOT/'server-data/resources/cidade_core/combat_mounts.lua'
source=ROOT/'server-data/resources/cidade_core/combat_weapon.lua'
lua.execute(mount_source.read_text(encoding='utf8'))
lua.execute(source.read_text(encoding='utf8'))
S=lua.globals().S;V=lua.globals().vector3
weapon=lua.globals().CidadeCombatWeapon

def multiply(a,b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

def dot(a,b):return sum(x*y for x,y in zip(a,b))

cases=0;max_error=0
for gun in (101,102):
    mount=lua.globals().CidadeCombatMounts[gun]
    # basis[i] is a weapon-axis column expressed in right-wrist space.
    basis=[[mount.basis[j+1][i+1] for j in range(3)] for i in range(3)]
    transpose=[[basis[j][i] for j in range(3)] for i in range(3)]
    for yaw,pitch,ped_tilt in ((0,0,0),(95,0,0),(240,60,0),(350,-40,0),(60,30,15),(170,-5,-10)):
        y,p,t=map(math.radians,(yaw,pitch,ped_tilt))
        rz=[[math.cos(y),-math.sin(y),0],[math.sin(y),math.cos(y),0],[0,0,1]]
        # Positive angle elevates the longitudinal gun X axis.
        ry=[[math.cos(p),0,-math.sin(p)],[0,1,0],[math.sin(p),0,math.cos(p)]]
        target=multiply(rz,ry)
        wrist=multiply(target,transpose)
        S.wrist=lua.table_from([V(*[wrist[i][j] for i in range(3)]) for j in range(3)])
        S.up=V(math.sin(t),0,math.cos(t))
        assert weapon.create(1,gun)
        assert S.visible is False and weapon.update()
        sample=weapon.inspect()
        axis=[target[i][0] for i in range(3)]
        expected=math.degrees(math.asin(dot(axis,[math.sin(t),0,math.cos(t)])))
        err=abs(sample.barrelPitch-expected)
        max_error=max(max_error,err)
        assert err<.0001,(sample.barrelPitch,expected)
        assert abs(sample.worldBarrelPitch-pitch)<.0001
        assert abs(sample.basisLength-1)<.000001
        assert [sample.rightWrist[i] for i in (1,2,3)]==[1,2,3]
        assert [sample.leftWrist[i] for i in (1,2,3)]==[4,5,6]
        # Existing visual mount orientation/translation remains correct.
        assert max(abs(S.matrix[4+i]-axis[i]) for i in range(3))<.000001
        offset=[mount.position[i] for i in (1,2,3)]
        at=[i+1+dot(wrist[i],offset) for i in range(3)]
        assert max(abs(S.matrix[10+i]-at[i]) for i in range(3))<.000001
        weapon.destroy();assert S.visible is True and weapon.inspect() is None
        cases+=1
assert weapon.create(1,101)
S.wrist=lua.table_from([V(0,0,0) for _ in range(3)])
assert weapon.inspect().invalidBasis
weapon.destroy()
report={'game_tested':False,'synthetic_transforms':True,'cases':cases,
        'both_weapon_mounts':True,'ped_relative_pitch':True,'world_pitch':True,
        'invalid_basis_safe':True,'mount_update_preserved':True,
        'max_pitch_error_degrees':max_error,
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(HERE/'weapon_trace_v7_checks.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('V7_WEAPON_TRACE_TESTS_OK',json.dumps(report))
