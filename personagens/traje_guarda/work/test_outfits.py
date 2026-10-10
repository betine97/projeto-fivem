from pathlib import Path
import sys
sys.path.insert(0,str(Path('laboratorio_fivem/work/test_deps').resolve()))
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
for file in ['server-data/resources/cidade_roupas/client.lua','server-data/resources/cidade_roupas/fxmanifest.lua','server-data/resources/cidade_core/characters.lua']:
    lua.execute('assert(load(...))',Path(file).read_text())
lua.execute('''
commands={}; currentModel='a_m_y_business_01'; calls={}; comps={}; props={}; failed=false
LocalPlayer={state={}}
function joaat(s)return s end
function RegisterCommand(n,f)commands[n]=f end
function ExecuteCommand(n)commands[n]()end
function PlayerPedId()return 1 end
function GetEntityModel()return currentModel end
function IsEntityDead()return false end
function IsPedInAnyVehicle()return false end
function GetPedDrawableVariation(_,i)return i+10 end
function GetPedTextureVariation(_,i)return i+1 end
function GetPedPaletteVariation()return 2 end
function GetPedPropIndex(_,i)return i==0 and 3 or -1 end
function GetPedPropTextureIndex()return 1 end
function GetPedCollectionsCount()return 2 end
function GetPedCollectionName(_,i)return i==0 and '' or 'male_heist' end
function SetPedCollectionComponentVariation(_,id,c,d,t,p)calls[id]={c,d,t,p}end
function SetPedComponentVariation(_,id,d,t,p)comps[id]={d,t,p}end
function SetPedPropIndex(_,id,d,t)props[id]={d,t}end
function ClearAllPedProps()end
function BeginTextCommandThefeedPost()end
function AddTextComponentSubstringPlayerName()end
function EndTextCommandThefeedPostTicker()end
exports={cidade_core={changeCharacter=function(_,model)
 if failed then return false end
 currentModel=model; return true
end}}
''')
lua.execute(Path('server-data/resources/cidade_roupas/client.lua').read_text())
lua.execute('''
commands.macacaobranco()
assert(currentModel=='mp_m_freemode_01')
for id,drawable in pairs({[11]=8,[4]=7,[3]=0,[6]=0,[1]=20}) do
 assert(calls[id][1]=='male_heist' and calls[id][2]==drawable)
end
commands.guardavermelho();assert(currentModel=='guardalab')
commands.roupaanterior();assert(currentModel=='a_m_y_business_01')
assert(comps[11][1]==21 and comps[11][2]==12 and comps[11][3]==2)
assert(props[0][1]==3 and props[0][2]==1)
failed=true;commands.guardavermelho();failed=false
commands.roupaanterior();assert(currentModel=='a_m_y_business_01')
LocalPlayer.state.labElevatorBusy=true;commands.guardavermelho();assert(currentModel=='a_m_y_business_01')
''')
print('OUTFIT_COMMANDS_OK: equip, chain, restore, load failure, elevator lock')
