Flight = {}
local function clamp(x,a,b) return math.max(a,math.min(b,x)) end
function Flight.smooth(value,target,response,dt)
    return target+(value-target)*math.exp(-response*dt)
end
function Flight.new(heading)
    return {heading=heading, yawTarget=heading, look=0, lookTarget=0, vx=0,vy=0,vz=0,pitch=0,roll=0}
end
function Flight.update(s,input,dt,cfg)
    dt=clamp(dt,0,0.05)
    -- Mouse values are per-frame deltas; keyboard/controller turns are rates.
    s.yawTarget=s.yawTarget-(input.mouseX or 0)*cfg.mouseSensitivity+(input.yaw or 0)*100*dt
    s.lookTarget=clamp(s.lookTarget-(input.mouseY or 0)*cfg.mouseSensitivity,-65,65)
    s.heading=Flight.smooth(s.heading,s.yawTarget,cfg.lookResponse,dt)
    s.look=Flight.smooth(s.look,s.lookTarget,cfg.lookResponse,dt)
    local h,p=math.rad(s.heading),math.rad(s.look)
    local f,side,up=input.forward or 0,input.side or 0,input.up or 0
    local speed=input.boost and cfg.boostSpeed or cfg.speed
    local x=-math.sin(h)*math.cos(p)*f+math.cos(h)*side
    local y=math.cos(h)*math.cos(p)*f+math.sin(h)*side
    local z=math.sin(p)*f+up*cfg.climb/speed
    local length=math.sqrt(x*x+y*y+z*z)
    if length>1 then x,y,z=x/length,y/length,z/length end
    x,y,z=x*speed,y*speed,z*speed
    local response=(f==0 and side==0 and up==0) and cfg.braking or cfg.acceleration
    local decay=math.exp(-response*dt)
    -- Integral, rather than end-of-frame velocity, keeps travel consistent across FPS.
    local move={x=x*dt+(s.vx-x)*(1-decay)/response,
        y=y*dt+(s.vy-y)*(1-decay)/response,z=z*dt+(s.vz-z)*(1-decay)/response}
    s.vx,s.vy,s.vz=x+(s.vx-x)*decay,y+(s.vy-y)*decay,z+(s.vz-z)*decay
    local forwardSpeed=-math.sin(h)*s.vx+math.cos(h)*s.vy
    local sideSpeed=math.cos(h)*s.vx+math.sin(h)*s.vy
    s.pitch=Flight.smooth(s.pitch,-forwardSpeed/speed*cfg.tilt,7,dt)
    s.roll=Flight.smooth(s.roll,-sideSpeed/speed*cfg.tilt,7,dt)
    return move
end

-- A body-radius capsule may advance inside a wider, already checked corridor.
-- Never move ahead of the returned ray/capsule result or reuse a stale corridor.
function Flight.insideCorridor(point,start,finish,margin)
    local x,y,z=finish.x-start.x,finish.y-start.y,finish.z-start.z
    local length=x*x+y*y+z*z
    if length<0.000001 then return false end
    local t=((point.x-start.x)*x+(point.y-start.y)*y+(point.z-start.z)*z)/length
    if t<0 or t>1 then return false end
    local dx,dy,dz=point.x-start.x-t*x,point.y-start.y-t*y,point.z-start.z-t*z
    return dx*dx+dy*dy+dz*dz<=margin*margin
end

function Flight.audioVolume(speed,distance)
    return (0.22+0.53*clamp(speed/16,0,1))*clamp(1-distance/60,0,1)
end
