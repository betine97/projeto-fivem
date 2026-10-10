"""Exercise actual wardrobe callbacks, including independent clothing and appearance."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'personagens/calca_tatica/test_deps'))
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
commands={};callbacks={};events={};messages={};deleted={};models={[1]=10};player=1;counter=10
frozen={};focus=false;cameraActive=false;headReady={};headPending={};headings={};headFeatures={};tagRequests={}
local realRep=string.rep
local identityBlob=string.pack('<i4xxxxi4xxxxi4xxxxi4xxxxi4xxxxi4xxxxfxxxxfxxxxfxxxxi4xxxx',5,12,0,3,9,0,0.25,0.75,0.0,0)
string.rep=function(value,count)if value==string.char(0) and count==80 then return identityBlob end return realRep(value,count) end
Citizen={InvokeNative=function(hash,ped,buffer)assert(#buffer==80);return true end,ReturnResultAnyway=function()end}
collections={'','Male_Heist','mp_m_heist3','mp_m_valentines_02','male_apt01','female_apt01'}
wardrobes={[1]={components={[11]={12,2,0},[4]={7,1,0}},props={[0]={3,0}},tattoos={'old'}}}
function wardrobe(p) if not wardrobes[p] then wardrobes[p]={components={},props={},tattoos={}} end return wardrobes[p] end
LocalPlayer={state={set=function(self,k,v)self[k]=v end}}
exports={cidade_core={changeCharacter=function(self,model)player=2;models[2]=model;return true end}}
function joaat(name) if name=='mp_m_freemode_01' then return 10 elseif name=='mp_f_freemode_01' then return 20 else return name end end
function RegisterCommand(n,f)commands[n]=f end
function RegisterNUICallback(n,f)callbacks[n]=f end
function RegisterNetEvent(n,f)events[n]=f end
function AddEventHandler(n,f)events[n]=f end
function CreateThread(f)end
function SetTimeout(ms,f)end
function Wait(ms)for p,count in pairs(headPending) do headPending[p]=count-1;if count<=1 then headReady[p]=true;headPending[p]=nil end end end
function GetGameTimer()return 1000 end
function PlayerPedId()return player end
function PlayerId()return 0 end
function GetResourceState()return 'missing' end
function IsEntityDead()return false end
function IsPedInAnyVehicle()return false end
function IsPauseMenuActive()return false end
function IsNuiFocused()return focus end
function GetEntityCoords()return {x=1,y=2,z=3} end
function GetEntityHeading(p)return headings[p] or 90 end
function IsEntityPositionFrozen(p)return frozen[p] or false end
function FreezeEntityPosition(p,v)frozen[p]=v end
function GetEntityModel(p)return models[p] end
function RequestModel()end
function HasModelLoaded()return true end
function SetModelAsNoLongerNeeded()end
function ClonePed(p)counter=counter+1;models[counter]=models[p];return counter end
function CreatePed(_,m)counter=counter+1;models[counter]=m;return counter end
function DoesEntityExist(p)return models[p]~=nil end
function DeleteEntity(p)deleted[p]=true;models[p]=nil end
function SetEntityHeading(p,value)headings[p]=value end
function SetEntityAsMissionEntity()end
function SetEntityCoordsNoOffset()end
function SetEntityCollision()end
function SetEntityVisible()end
function ResetEntityAlpha()end
function SetEntityInvincible()end
function SetBlockingOfNonTemporaryEvents()end
function ClearPedTasksImmediately()end
function SetCurrentPedWeapon()end
function SetPedDefaultComponentVariation()end
function SetPedHeadBlendData(p,...)headReady[p]=false;headPending[p]=2;wardrobe(p).identity={...} end
function HasPedHeadBlendFinished(p)return headReady[p]==true end
function GetPedFaceFeature(_,index)return index==1 and 0.2 or 0 end
function SetPedFaceFeature(p,index,value)if not headFeatures[p] then headFeatures[p]={} end headFeatures[p][index]=value end
function GetPedEyeColor()return 0 end
function SetPedEyeColor()end
function CreateCam()return 101 end
function GetPedBoneCoords(_,bone,_,_,offset) return {x=1,y=2,z=(bone==31086 and 3.8 or 2.0)+offset} end
function GetAspectRatio()return 16/9 end
function SetCamCoord(_,x,y,z)cameraZ=z end
function PointCamAtCoord(_,x,y,z)targetZ=z end
function SetCamFov()end
function RenderScriptCams(active)cameraActive=active end
function DestroyCam()end
function SetNuiFocus(v)focus=v end
function SendNUIMessage(m)messages[#messages+1]=m end
function TriggerServerEvent(name,...)if name=='cidade_acervo:tags' then tagRequests[#tagRequests+1]={...} elseif name=='cidade_acervo:request' then requestedToken=(...) end end
function TriggerEvent()end
function GetCurrentResourceName()return 'cidade_acervo' end
function GetPedCollectionsCount()return #collections end
function GetPedCollectionName(_,i)return collections[i+1] end
function IsPedCollectionComponentVariationValid(_,_,_,index,texture)return index>=0 and index<20 and texture<5 end
function GetNumberOfPedCollectionPropDrawableVariations()return 20 end
function GetNumberOfPedCollectionPropTextureVariations()return 5 end
function SetPedCollectionComponentVariation(p,slot,collection,index,texture)
 lastComponent={p,slot,collection,index,texture};wardrobe(p).components[slot]={index,texture,0}
 if forceDependencies and slot==4 and collection=='Male_Heist' then wardrobe(p).components[11]={18,0,0};wardrobe(p).props[0]={18,0} end
end
function SetPedCollectionPropIndex(p,slot,collection,index,texture)lastProp={p,slot,collection,index,texture};wardrobe(p).props[slot]={index,texture} end
function GetPedDrawableVariation(p,id)return wardrobe(p).components[id] and wardrobe(p).components[id][1] or 0 end
function GetPedTextureVariation(p,id)return wardrobe(p).components[id] and wardrobe(p).components[id][2] or 0 end
function GetPedPaletteVariation()return 0 end
function GetPedPropIndex(p,id)return wardrobe(p).props[id] and wardrobe(p).props[id][1] or -1 end
function GetPedPropTextureIndex(p,id)return wardrobe(p).props[id] and wardrobe(p).props[id][2] or 0 end
function SetPedComponentVariation(p,id,d,t,pa)appliedTo=p;wardrobe(p).components[id]={d,t,pa} end
function ClearAllPedProps(p)wardrobe(p).props={} end
function ClearPedProp(p,id)wardrobe(p).props[id]=nil end
function SetPedPropIndex(p,id,d,t)appliedPropTo=p;wardrobe(p).props[id]={d,t} end
function SetPedHairTint(p,color)assert(headReady[p],'Hair tint requires initialized head blend');wardrobe(p).hairColor=color end
function GetPedHairColor(p)return wardrobe(p).hairColor end
function SetPedHeadOverlay(p,slot,value,opacity)assert(headReady[p],'Beard requires initialized head blend');wardrobe(p)['overlay'..slot]=value;wardrobe(p)['opacity'..slot]=opacity end
function SetPedHeadOverlayColor(p,slot,_,color)wardrobe(p)['overlayColor'..slot]=color end
function GetPedHeadOverlayData(p,slot)return true,wardrobe(p)['overlay'..slot],1,wardrobe(p)['overlayColor'..slot],0,wardrobe(p)['opacity'..slot] end
function ClearPedDecorations(p)wardrobe(p).tattoos={};wardrobe(p).overlay1=255;wardrobe(p).hairColor=-1 end
function AddPedDecorationFromHashes(p,collection,overlay)table.insert(wardrobe(p).tattoos,{collection,overlay}) end
function GetNumberOfPedDrawableVariations()return 4 end
function GetPedCollectionNameFromDrawable()return '' end
function GetPedCollectionLocalIndexFromDrawable(_,_,i)return i end
function GetNumHairColors()return 4 end
function GetPedHairRgbColor()return 10,20,30 end
function GetPedHeadOverlayNum()return 29 end
function GetPedDecorationZoneFromHashes(_,overlay)return overlay=='invalid' and 7 or 0 end
function GetLabelText()return 'NULL' end
function BeginTextCommandThefeedPost()end
function AddTextComponentSubstringPlayerName()end
function EndTextCommandThefeedPostTicker()end
function invoke(name,data)local result;callbacks[name](data or {},function(r)result=r end);return result end
''')
resource=ROOT/'server-data/resources/cidade_acervo'
lua.execute((resource/'client.lua').read_text(encoding='utf-8-sig'))
lua.execute('''
commands.roupas()
assert(wardrobe(counter).identity[1]==5 and wardrobe(counter).identity[2]==12 and wardrobe(counter).identity[7]==0.25 and headFeatures[counter][1]==0.2)
assert(focus and cameraActive and frozen[1] and LocalPlayer.state.wardrobeBusy)
assert(cameraZ==targetZ and cameraZ<3.2 and cameraZ>2.5)
assert(GetPedDrawableVariation(counter,11)==15 and GetPedDrawableVariation(counter,4)==1 and GetPedDrawableVariation(counter,6)==1)
assert(GetPedPropIndex(counter,0)==-1 and wardrobe(counter).overlay1==255 and #wardrobe(counter).tattoos==0)
assert(GetPedDrawableVariation(1,11)==12 and GetPedPropIndex(1,0)==3 and #wardrobe(1).tattoos==1)
local items={
 {id='shirt',sex='male',category='jbib',collection='mp_m_freemode_01_male_heist',index=9,textureIndex=0},
 {id='shirt2',sex='male',category='jbib',collection='mp_m_freemode_01_male_heist',index=8,textureIndex=0},
 {id='pants',sex='male',category='lowr',collection='mp_m_freemode_01_male_heist',index=7,textureIndex=0},
 {id='hat',sex='male',category='p_head',collection='mp_m_freemode_01_p_mp_m_heist3',index=1,textureIndex=2},
 {id='bad',sex='male',category='lowr',collection='missing',index=1},
 {id='female',sex='female',category='lowr',collection='mp_f_freemode_01',index=1}
}
local data={hair={},tattoos={
 {id='tat1',sex='male',collection='native',overlay='tattoo1',zone='torso'},
 {id='tat2',sex='male',collection='native',overlay='tattoo2',zone='torso'},
 {id='badTat',sex='male',collection='native',overlay='invalid',zone='torso'}
}}
events['cidade_acervo:items'](1,items,{},data)
assert(not invoke('select',{id='not-a-favorite'}).ok and not invoke('select',{id='female'}).ok and not invoke('select',{id='bad'}).ok)
assert(invoke('select',{id='shirt'}).ok and lastComponent[3]=='Male_Heist')
assert(invoke('select',{id='hat'}).ok and lastProp[3]=='mp_m_heist3')
forceDependencies=true
local pants=invoke('select',{id='pants'})
assert(pants.ok and pants.chosen.jbib=='shirt' and pants.chosen.p_head=='hat' and pants.chosen.lowr=='pants')
assert(GetPedDrawableVariation(counter,11)==9 and GetPedPropIndex(counter,0)==1)
assert(invoke('appearance',{kind='hair',value=3}).ok)
assert(invoke('appearance',{kind='beard',value=7}).ok)
assert(invoke('appearance',{kind='beardColor',value=2}).ok)
assert(invoke('appearance',{kind='hairColor',value=3}).ok)
assert(wardrobe(counter).hairColor==3 and wardrobe(counter).overlayColor1==2 and wardrobe(counter).opacity1==1)
assert(invoke('appearance',{kind='tattoo',value='tat1'}).ok)
assert(invoke('appearance',{kind='tattoo',value='tat2'}).ok and #wardrobe(counter).tattoos==2)
assert(not invoke('appearance',{kind='tattoo',value='badTat'}).ok)
assert(not invoke('appearance',{kind='hair',value=4}).ok and not invoke('appearance',{kind='hair',value=1.2}).ok)
local second=invoke('select',{id='shirt2'})
assert(second.chosen.jbib=='shirt2' and second.chosen.p_head=='hat' and second.chosen.lowr=='pants')
assert(GetPedDrawableVariation(counter,2)==3 and wardrobe(counter).overlay1==7 and #wardrobe(counter).tattoos==2)
local remove=invoke('select',{id='pants'})
assert(remove.removed and remove.chosen.lowr==nil and remove.chosen.jbib=='shirt2' and remove.chosen.p_head=='hat')
assert(GetPedDrawableVariation(counter,4)==1 and GetPedDrawableVariation(counter,11)==8)
assert(invoke('appearance',{kind='tattoo',value='tat1'}).ok and #wardrobe(counter).tattoos==1)
assert(invoke('view',{view='head'}).ok and cameraZ>3.5)
assert(invoke('rotate',{angle=270}).ok and headings[counter]==0)
assert(invoke('rotate',{angle=360}).ok and headings[counter]==90)
assert(not invoke('rotate',{angle=-1}).ok and not invoke('rotate',{angle=0/0}).ok)
local savedTags
callbacks.tags({id='shirt',tags={'OK'}},function(result)savedTags=result end)
local tagReq=tagRequests[#tagRequests]
assert(not savedTags and tagReq[3]=='shirt')
events['cidade_acervo:tagsSaved'](tagReq[1],tagReq[2],tagReq[3],{ok=true,tags={'OK'}})
assert(savedTags.ok and savedTags.tags.shirt[1]=='OK')
assert(not invoke('tags',{id='unknown',tags={'OK'}}).ok)
local reset=invoke('reset')
assert(reset.rotation==0 and headings[counter]==90)
assert(reset.ok and next(reset.chosen)==nil and next(reset.appearance.tattoos)==nil and reset.appearance.beard==255 and reset.appearance.hair==0)
assert(GetPedDrawableVariation(counter,11)==15 and GetPedPropIndex(counter,0)==-1 and GetPedDrawableVariation(counter,2)==0 and #wardrobe(counter).tattoos==0)
assert(invoke('select',{id='shirt'}).ok and invoke('select',{id='hat'}).ok and invoke('select',{id='pants'}).ok)
events['cidade_acervo:items'](1,{items[1],items[4]}, {}, data)
assert(GetPedDrawableVariation(counter,11)==9 and GetPedDrawableVariation(counter,4)==1 and GetPedPropIndex(counter,0)==1)
assert(invoke('appearance',{kind='beard',value=6}).ok and invoke('appearance',{kind='tattoo',value='tat2'}).ok)
assert(invoke('apply').ok and wardrobe(1).identity[1]==5 and GetPedDrawableVariation(1,11)==9 and wardrobe(1).overlay1==6 and #wardrobe(1).tattoos==1)
assert(not focus and not cameraActive and not frozen[1] and not LocalPlayer.state.wardrobeBusy)
commands.roupas()
assert(invoke('sex',{sex='female'}).ok and models[counter]==20 and GetPedDrawableVariation(counter,4)==15)
events['cidade_acervo:items'](3,{items[6]})
assert(invoke('select',{id='female'}).ok and invoke('apply').ok and player==2 and appliedTo==2)
assert(not focus and not cameraActive)
commands.roupas()
assert(invoke('reset').ok and invoke('apply').ok) -- Applying underwear without selecting a garment is allowed.
commands.roupas()
local oldTop=GetPedDrawableVariation(2,11)
assert(invoke('close').ok and GetPedDrawableVariation(2,11)==oldTop and not frozen[2] and not focus)
commands.roupas();events.onResourceStop('cidade_acervo')
assert(not focus and not cameraActive and not frozen[2])
''')
compile_lua=lua.eval('function(code) local f,e=load(code); assert(f,e) end')
compile_lua((resource/'server.lua').read_text(encoding='utf-8-sig'))
print('PASS: underwear baseline, independent slots and forced dependencies, multi-select, individual removal, complete reset, appearance validation and apply, favorite refresh, female model, camera, cancel cleanup')
import json
lua.globals().exclusiveItems=lua.table_from(json.loads((resource/'exclusives.json').read_text(encoding='utf-8'))['items'],recursive=True)
lua.execute('''
for _,item in ipairs(exclusiveItems) do collections[#collections+1]=item.collection end
commands.roupas();assert(invoke('sex',{sex='male'}).ok)
local shirt,pants=exclusiveItems[1],exclusiveItems[2]
local stock={id='shirt',sex='male',category='jbib',collection='mp_m_freemode_01_male_heist',index=9,textureIndex=0}
local hat={id='hat',sex='male',category='p_head',collection='mp_m_freemode_01_p_mp_m_heist3',index=1,textureIndex=2}
events['cidade_acervo:items'](requestedToken,{shirt,pants,stock,hat})
assert(GetPedDrawableVariation(counter,3)==15)
assert(invoke('select',{id=pants.id}).ok and invoke('select',{id=shirt.id}).ok)
assert(GetPedDrawableVariation(counter,3)==0 and GetPedDrawableVariation(counter,4)==0)
assert(invoke('select',{id=hat.id}).ok) -- A hat must remain when switching/removing the shirt.
local removed=invoke('select',{id=shirt.id})
assert(removed.removed and removed.chosen.lowr==pants.id and GetPedDrawableVariation(counter,3)==15)
assert(GetPedDrawableVariation(counter,4)==0 and GetPedPropIndex(counter,0)==1)
assert(invoke('select',{id=shirt.id}).ok and GetPedDrawableVariation(counter,3)==0)
assert(invoke('select',{id=stock.id}).ok and GetPedDrawableVariation(counter,3)==15)
assert(invoke('select',{id=shirt.id}).ok)
assert(invoke('reset').ok and GetPedDrawableVariation(counter,3)==15 and GetPedDrawableVariation(counter,4)==1)
local valid=IsPedCollectionComponentVariationValid
IsPedCollectionComponentVariationValid=function(p,slot,c,index,t)if slot==3 then return false end return valid(p,slot,c,index,t) end
assert(not invoke('select',{id=shirt.id}).ok and GetPedDrawableVariation(counter,11)==15 and GetPedDrawableVariation(counter,3)==15)
IsPedCollectionComponentVariationValid=valid
assert(invoke('select',{id=shirt.id}).ok and invoke('select',{id=pants.id}).ok)
local applied=invoke('apply');assert(applied.ok and GetPedDrawableVariation(player,3)==0 and GetPedDrawableVariation(player,4)==0)
commands.roupas()
events['cidade_acervo:items'](requestedToken,exclusiveItems)
assert(invoke('select',{id=pants.id}).ok)
for _,item in ipairs(exclusiveItems) do
 if item.category=='jbib' then
  local result=invoke('select',{id=item.id})
  assert(result.ok and result.chosen.jbib==item.id and result.chosen.lowr==pants.id)
  assert(GetPedDrawableVariation(counter,3)==0 and GetPedDrawableVariation(counter,4)==0)
 end
end
local activeShirt=nil
for _,item in ipairs(exclusiveItems) do if item.category=='jbib' then activeShirt=item.id end end
for _,item in ipairs(exclusiveItems) do
 if item.category=='lowr' then
  local result=invoke('select',{id=item.id})
  if result.removed then result=invoke('select',{id=item.id}) end
  assert(result.ok and result.chosen.lowr==item.id and result.chosen.jbib==activeShirt)
  assert(GetPedDrawableVariation(counter,3)==0 and GetPedDrawableVariation(counter,11)==0)
 end
end
assert(invoke('reset').ok and GetPedDrawableVariation(counter,3)==15)
assert(invoke('close').ok)
print('PASS: actual exclusive manifests, combined shirt/jeans, compatible arms, stock switch, individual removal, reset, failed dependency is atomic, applied outfit')
''')
