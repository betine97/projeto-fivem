local mt={}
local function vec(x,y,z)return setmetatable({x=x,y=y,z=z},mt)end
mt.__add=function(a,b)return vec(a.x+b.x,a.y+b.y,a.z+b.z)end
mt.__sub=function(a,b)return vec(a.x-b.x,a.y-b.y,a.z-b.z)end
mt.__mul=function(a,n)return vec(a.x*n,a.y*n,a.z*n)end
local exists,visible,created,deleted,fail=true,true,0,0,false
local matrix,tint,components
local events={}
function AddEventHandler(n,f)events[n]=f end
function GetCurrentResourceName()return 'cidade_core' end
function GetEntityCoords()return vec(10,20,30)end
function GetPedBoneCoords(_,_,x,y,z)return vec(10-y,20+x,30+z)end
function GetCurrentPedWeaponEntityIndex()return 2 end
function DoesEntityExist(e)return e==1 or e==2 or (e==7 and exists)end
function CreateWeaponObject()created=created+1;return fail and 0 or 7 end
function DeleteEntity(e)assert(e==7);deleted=deleted+1 end
function SetPedCurrentWeaponVisible(p,v,deselect)assert(p==1 and not deselect);visible=v end
function SetEntityAsMissionEntity()end
function SetEntityCollision(_,v)assert(not v)end
function FreezeEntityPosition(_,v)assert(v)end
function SetWeaponObjectTintIndex(_,value)tint=value end
function GetPedWeaponTintIndex()return 4 end
function HasPedGotWeaponComponent(_,_,c)return c=='COMPONENT_AT_AR_SUPP' end
function GiveWeaponComponentToWeaponObject(_,c)components=c end
function joaat(v)return v end
function SetEntityMatrix(e,...)assert(e==7);matrix={...}end
dofile('server-data/resources/cidade_core/combat_weapon.lua')
dofile('server-data/resources/cidade_core/combat_mounts.lua')
local weapon='WEAPON_CARBINERIFLE'
assert(CidadeCombatWeapon.create(1,weapon))
assert(not visible and tint==4 and components=='COMPONENT_AT_AR_SUPP')
assert(CidadeCombatWeapon.entity(1)==7)
local mount=CidadeCombatMounts[weapon]
assert(math.abs(matrix[10]-(10-mount.position[2]))<1e-6)
assert(math.abs(matrix[11]-(20+mount.position[1]))<1e-6)
assert(math.abs(matrix[12]-(30+mount.position[3]))<1e-6)
for start=1,7,3 do
 local norm=matrix[start]^2+matrix[start+1]^2+matrix[start+2]^2
 assert(math.abs(norm-1)<.00001,'Weapon axes must remain unit length')
end
-- Matrix is derived entirely from wrist; no native reload/blocked-weapon angle.
local previous=table.concat(matrix,',');CidadeCombatWeapon.update();assert(previous==table.concat(matrix,','))
CidadeCombatWeapon.destroy();assert(visible and deleted==1 and CidadeCombatWeapon.entity(1)==2)
assert(CidadeCombatWeapon.create(1,weapon));events.onResourceStop('cidade_core');assert(visible and deleted==2)
assert(CidadeCombatWeapon.create(1,weapon));exists=false;assert(not CidadeCombatWeapon.update());CidadeCombatWeapon.destroy();assert(visible);exists=true
assert(CidadeCombatWeapon.create(1,'WEAPON_ASSAULTRIFLE'))
local assault=CidadeCombatMounts['WEAPON_ASSAULTRIFLE']
assert(math.abs(matrix[12]-(30+assault.position[3]))<1e-6)
assert(math.abs(assault.position[2]-mount.position[2])>.04,'AK needs its own grip mount')
assert(not CidadeCombatWeapon.create(1,'WEAPON_RPG') and visible,'Reject unsupported grip, restore native rifle')
fail=true;assert(not CidadeCombatWeapon.create(1,weapon));assert(visible)
print('OK: authored wrist mount, orthonormal transform, cosmetics, failure and cleanup')
