dofile('server-data/resources/fpv_drone_runtime/config.lua')
dofile('server-data/resources/fpv_drone_runtime/flight.lua')
local function near(a,b,tolerance) assert(math.abs(a-b)<(tolerance or 0.00001), tostring(a)..' != '..tostring(b)) end
local function simulate(input,seconds,fps,s)
    s=s or Flight.new(0)
    local p={x=0,y=0,z=0}
    for i=1,seconds*fps do
        local d=Flight.update(s,input,1/fps,Config)
        p.x,p.y,p.z=p.x+d.x,p.y+d.y,p.z+d.z
    end
    return p,s
end
local baseline=simulate({forward=1},3,60)
for _,fps in ipairs({30,144}) do near(simulate({forward=1},3,fps).y,baseline.y) end
local _,s=simulate({forward=1},3,60)
near(s.vy,16,0.001); assert(s.pitch < -30)
local first=Flight.update(Flight.new(0),{forward=1},1/60,Config)
assert(first.y>0 and first.y<16/60, 'Acceleration must start gently')
local stop,stopped=simulate({},3,60,s)
assert(stop.y>0 and stopped.vy<0.001, 'Braking should coast smoothly then hover')
local _,boost=simulate({forward=1,boost=true},3,60)
near(boost.vy,28,0.001)
assert(simulate({side=-1},1,60).x<0)
assert(simulate({side=1},1,60).x>0)
assert(simulate({forward=-1},1,60).y<0)
assert(simulate({up=1},1,60).z>0)
assert(simulate({up=-1},1,60).z<0)
local mouse=Flight.new(0)
Flight.update(mouse,{mouseX=1,mouseY=-1},1/60,Config)
local aimed=simulate({forward=1},1,60,mouse)
assert(aimed.x>0 and aimed.z>0, 'W must follow mouse heading and elevation')
local _,left=simulate({yaw=1},1,60); assert(left.heading>0)
local _,right=simulate({yaw=-1},1,60); assert(right.heading<0)
local _,diagonal=simulate({forward=1,side=1,up=1},3,60)
assert(math.sqrt(diagonal.vx^2+diagonal.vy^2+diagonal.vz^2)<=16.001)
local a,b={x=0,y=0,z=0},{x=0,y=2,z=0}
assert(Flight.insideCorridor({x=0.05,y=1,z=0},a,b,0.08))
assert(not Flight.insideCorridor({x=0.2,y=1,z=0},a,b,0.08))
assert(not Flight.insideCorridor({x=0,y=3,z=0},a,b,0.08))
near(Flight.audioVolume(0,0),0.22)
near(Flight.audioVolume(16,0),0.75)
near(Flight.audioVolume(16,60),0)
assert(Flight.audioVolume(0,0)<Flight.audioVolume(1,0))
print('OK: all axes, smooth acceleration/braking, boost, tilt, mouse steering, FPS consistency, collision corridor, hover audio')
