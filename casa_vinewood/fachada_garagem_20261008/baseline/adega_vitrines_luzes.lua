-- Local fill for the model's recessed LED channels, with distance culling.
local origin=vector3(-976.1010131835938,676.7308959960938,157.8350372314453)
local lights={
 {p=vector3(9.799,-1.215,.64),range=1.85,intensity=1.12},
 {p=vector3(10.410,-1.215,.64),range=1.85,intensity=1.12},
 {p=vector3(13.194,-1.215,.64),range=1.85,intensity=1.12},
 {p=vector3(13.800,-1.215,.64),range=1.85,intensity=1.12},
 {p=vector3(11.802,-1.185,1.955),range=1.20,intensity=1.05},
 {p=vector3(11.802,-1.185,1.375),range=1.20,intensity=1.05},
 {p=vector3(11.802,-1.185,.770),range=1.20,intensity=1.05},
 {p=vector3(11.079,-1.438,-.400),range=.55,intensity=.70},
}
CreateThread(function()
 local fade=0.0
 while true do
  local p=GetEntityCoords(PlayerPedId())-origin
  local near=#(p-vector3(11.8,-1.40,.6))<15.0 and p.y<-.90 and p.z<2.4
  if near or fade>0 then
   fade=math.max(0.0,math.min(1.0,fade+(near and 1 or -1)*GetFrameTime()*3.0))
   for _,l in ipairs(lights) do
    local q=origin+l.p
    DrawLightWithRange(q.x,q.y,q.z,255,197,117,l.range,l.intensity*fade)
   end
   Wait(0)
  else Wait(750) end
 end
end)
