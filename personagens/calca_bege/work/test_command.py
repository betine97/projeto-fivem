"""Exercise the installed /calcabege command against stateful native mocks."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'laboratorio_fivem/work/test_deps'))
from lupa import LuaRuntime

source = (root / 'server-data/resources/cidade_roupas/client.lua').read_text()

MOCKS = r'''
commands={}; components={}; props={}; setCalls={}; switchCalls=0
currentModel='mp_m_freemode_01'; failSwitch=false; dead=false; vehicle=false
collections={'','Male_Heist','Male_Apt01'}
faceBlendToken='unchanged native face'; LocalPlayer={state={}}
for i=0,11 do components[i]={i+10,i+1,2} end
for i=0,7 do props[i]={i==0 and 3 or -1,1} end
function joaat(s) return s end
function RegisterCommand(name,f) commands[name]=f end
function ExecuteCommand(name) commands[name]() end
function PlayerPedId() return 1 end
function GetEntityModel() return currentModel end
function IsEntityDead() return dead end
function IsPedInAnyVehicle() return vehicle end
function GetPedDrawableVariation(_,id) return components[id][1] end
function GetPedTextureVariation(_,id) return components[id][2] end
function GetPedPaletteVariation(_,id) return components[id][3] end
function GetPedPropIndex(_,id) return props[id][1] end
function GetPedPropTextureIndex(_,id) return props[id][2] end
function GetPedCollectionsCount() return #collections end
function GetPedCollectionName(_,i) return collections[i+1] end
function SetPedCollectionComponentVariation(_,id,c,d,t,p)
    setCalls[#setCalls+1]={id,c,d,t,p}
    components[id]={d,t,p}
    if simulateJacketDependencies and id==11 and d==9 then
        components[7]={15,0,0}; components[8]={16,0,0}
    end
end
function SetPedComponentVariation(_,id,d,t,p) components[id]={d,t,p} end
function SetPedPropIndex(_,id,d,t) props[id]={d,t} end
function ClearAllPedProps() for i=0,7 do props[i]={-1,0} end end
function SetPedHeadBlendData() error('Face blend must not be reset') end
function SetPedDefaultComponentVariation() error('Freemode must not be reset') end
function BeginTextCommandThefeedPost() end
function AddTextComponentSubstringPlayerName() end
function EndTextCommandThefeedPostTicker() end
function print() end
exports={cidade_core={changeCharacter=function(_,model)
    switchCalls=switchCalls+1
    if failSwitch then return false end
    currentModel=model
    return true
end}}
'''

def case(label, body):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('assert(load(...))', source)
    lua.execute(MOCKS)
    lua.execute(source)
    lua.execute(body)
    print(f'PASS: {label}')

case('native face, hair and model preserved; only trousers; bare feet; restore', r'''
local head={table.unpack(components[0])}
local hair={table.unpack(components[2])}
commands.calcabege()
assert(currentModel=='mp_m_freemode_01' and switchCalls==0)
assert(components[0][1]==head[1] and components[2][1]==hair[1])
assert(faceBlendToken=='unchanged native face')
local calls={}
for _,item in ipairs(setCalls) do
    assert(item[1]~=0 and item[1]~=2)
    calls[item[1]]=item
end
for id,d in pairs({[1]=0,[3]=15,[7]=0,[8]=15,[9]=0,[10]=0,[11]=15}) do
    assert(calls[id][2]=='' and calls[id][3]==d)
end
assert(calls[4][2]=='Male_Heist' and calls[4][3]==8)
assert(calls[6][2]=='Male_Apt01' and calls[6][3]==1)
assert(props[0][1]==-1)
commands.roupaanterior()
assert(switchCalls==0 and props[0][1]==3 and props[0][2]==1)
for id=0,11 do assert(components[id][1]==id+10 and components[id][2]==id+1 and components[id][3]==2) end
''')

case('full collection names and repeated equip', r'''
collections={'','mp_m_freemode_01_male_heist','mp_m_freemode_01_male_apt01'}
commands.calcabege();commands.calcabege()
assert(components[4][1]==8 and components[6][1]==1)
commands.roupaanterior()
assert(components[4][1]==14 and components[7][1]==17)
''')

case('mixed case names and full prefixes preserve the native returned spelling', r'''
collections={'','MP_M_FREEMODE_01_MaLe_HeIsT','mP_m_FrEeMoDe_01_MALE_Apt01'}
commands.calcabege()
assert(setCalls[8][2]=='MP_M_FREEMODE_01_MaLe_HeIsT' and setCalls[8][3]==8)
assert(setCalls[9][2]=='mP_m_FrEeMoDe_01_MALE_Apt01' and setCalls[9][3]==1)
assert(components[0][1]==10 and components[2][1]==12 and switchCalls==0)
commands.roupaanterior();assert(components[4][1]==14)
''')

case('legacy lowercase collection names continue working', r'''
collections={'','male_heist','male_apt01'}
commands.calcabege()
assert(setCalls[8][2]=='male_heist' and setCalls[8][3]==8)
assert(setCalls[9][2]=='male_apt01' and setCalls[9][3]==1)
commands.roupaanterior();assert(components[4][1]==14)
''')

case('white and guard remain available; chain restores original outfit/model', r'''
currentModel='a_m_y_business_01'
commands.macacaobranco();assert(currentModel=='mp_m_freemode_01' and components[4][1]==7)
commands.guardavermelho();assert(currentModel=='guardalab')
commands.calcabege();assert(currentModel=='mp_m_freemode_01' and components[4][1]==8)
commands.roupaanterior();assert(currentModel=='a_m_y_business_01')
assert(components[4][1]==14 and components[4][2]==5 and props[0][1]==3)
''')

case('missing collection rolls back; missing apartment falls back to native sandals', r'''
collections={'','male_apt01'}
commands.calcabege();assert(components[4][1]==14 and props[0][1]==3)
collections={'','male_heist'}
commands.calcabege()
assert(components[6][1]==5)
commands.roupaanterior();assert(components[4][1]==14)
''')

case('model load failure and unsafe states make no outfit change', r'''
currentModel='a_m_y_business_01';failSwitch=true
commands.calcabege();assert(currentModel=='a_m_y_business_01' and #setCalls==0)
commands.roupaanterior();assert(switchCalls==1)
failSwitch=false
LocalPlayer.state.labElevatorBusy=true;commands.calcabege();assert(switchCalls==1)
LocalPlayer.state.labElevatorBusy=false;vehicle=true;commands.calcabege();assert(switchCalls==1)
vehicle=false;dead=true;commands.calcabege();assert(switchCalls==1)
''')

print('CALCA_BEGE_COMMAND_OK')

case('shirt with approved trousers keeps native face and restores original outfit', r'''
commands.camisaestampada()
assert(currentModel=='mp_m_freemode_01' and switchCalls==0)
assert(components[0][1]==10 and components[2][1]==12)
assert(components[4][1]==8 and components[11][1]==9)
assert(components[7][1]==0 and components[8][1]==15)
commands.calcabege();assert(components[11][1]==15 and components[4][1]==8)
commands.roupaanterior();assert(components[4][1]==14 and components[11][1]==21)
''')

case('complete outfit adds shoes and wrist mesh and restores prior components', r'''
commands.conjuntocompleto()
assert(currentModel=='mp_m_freemode_01' and switchCalls==0)
assert(components[0][1]==10 and components[2][1]==12)
assert(components[4][1]==8 and components[11][1]==9)
assert(components[6][1]==1 and components[7][1]==1)
assert(setCalls[#setCalls][2]=='Male_Heist')
commands.camisaestampada();assert(components[7][1]==0)
commands.roupaanterior();assert(components[6][1]==16 and components[7][1]==17)
''')

case('shirt stock dependencies cannot leave a tie or undershirt', r'''
simulateJacketDependencies=true
commands.conjuntocompleto()
assert(components[7][1]==1 and components[8][1]==15)
commands.camisaestampada()
assert(components[7][1]==0 and components[8][1]==15)
commands.roupaanterior()
assert(components[7][1]==17 and components[8][1]==18)
''')

case('person2 switches model, selects its full outfit and restores the original', r'''
commands.person2()
assert(currentModel=='person2' and switchCalls==1)
for _,id in ipairs({0,2,3,4,11}) do assert(components[id][1]==0 and components[id][2]==0) end
for i=0,7 do assert(props[i][1]==-1) end
commands.person2();assert(switchCalls==1)
commands.roupaanterior()
assert(currentModel=='mp_m_freemode_01' and switchCalls==2)
for id=0,11 do assert(components[id][1]==id+10 and components[id][2]==id+1 and components[id][3]==2) end
assert(props[0][1]==3 and props[0][2]==1)
''')

case('person2 load failure leaves the player unchanged and permits a retry', r'''
failSwitch=true
commands.person2()
assert(currentModel=='mp_m_freemode_01' and props[0][1]==3 and components[3][1]==13)
commands.roupaanterior();assert(switchCalls==1)
failSwitch=false;commands.person2();assert(currentModel=='person2' and switchCalls==2)
commands.roupaanterior();assert(currentModel=='mp_m_freemode_01' and switchCalls==3)
''')
