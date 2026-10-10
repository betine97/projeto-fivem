Motor = {}
function Motor.step(current, target, angle, dt, response, sign)
    dt = math.max(0, dt)
    local decay = math.exp(-response * dt)
    local nextRpm = target + (current-target)*decay
    -- Exact integral of exponential spin response: consistent at 30/60/144 Hz.
    local rpmSeconds = target*dt + (current-target)*(1-decay)/response
    return nextRpm, (angle + sign*rpmSeconds*6) % 360
end
function Motor.damageBand(speed)
    if speed < 2 then return 'none' elseif speed < 5 then return 'light'
    elseif speed < 10 then return 'medium' else return 'severe' end
end
