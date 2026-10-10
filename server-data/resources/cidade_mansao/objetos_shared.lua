-- Pure transform/validation helpers. Coordinates are model pivots, not mesh centres.
CidadeObjetos = {}
local M = CidadeObjetos
function M.finite(n, limit) return type(n)=='number' and n==n and math.abs(n)<(limit or 100000) end
function M.vec(v, limit)
    return type(v)=='table' and M.finite(v[1],limit) and M.finite(v[2],limit) and M.finite(v[3],limit)
end
function M.pose(t)
    return type(t)=='table' and M.vec(t.p) and M.finite(t.h,100000)
end
function M.copy(t) return {p={t.p[1],t.p[2],t.p[3]},h=t.h} end
function M.distance(a,b) return math.sqrt((a[1]-b[1])^2+(a[2]-b[2])^2+(a[3]-b[3])^2) end
local function rotate(v,c,s) return {c*v[1]-s*v[2],s*v[1]+c*v[2],v[3]} end
function M.basis(d,h)
    local a=math.rad(h); local c,s=math.cos(a),math.sin(a)
    local b=d.basis or {{0,1,0},{1,0,0},{0,0,1}} -- forward, right, up
    return rotate(b[1],c,s),rotate(b[2],c,s),rotate(b[3],c,s)
end
function M.offset(d,t,v)
    local f,r,u=M.basis(d,t.h); local s=d.s
    return {r[1]*v[1]*s[1]+f[1]*v[2]*s[2]+u[1]*v[3]*s[3],
        r[2]*v[1]*s[1]+f[2]*v[2]*s[2]+u[2]*v[3]*s[3],
        r[3]*v[1]*s[1]+f[3]*v[2]*s[2]+u[3]*v[3]*s[3]}
end
function M.world(d,t,v)
    local o=M.offset(d,t,v); return {t.p[1]+o[1],t.p[2]+o[2],t.p[3]+o[3]}
end
function M.center(d,t)
    return M.world(d,t,{(d.lo[1]+d.hi[1])/2,(d.lo[2]+d.hi[2])/2,(d.lo[3]+d.hi[3])/2})
end
function M.surfaceDistance(d,t,p)
    local f,r,u=M.basis(d,t.h); local v={p[1]-t.p[1],p[2]-t.p[2],p[3]-t.p[3]}
    local axes={r,f,u}; local sum=0
    for i=1,3 do
        local q=(v[1]*axes[i][1]+v[2]*axes[i][2]+v[3]*axes[i][3])/d.s[i]
        local delta=math.max(d.lo[i]-q,0,q-d.hi[i])*d.s[i]; sum=sum+delta*delta
    end
    return math.sqrt(sum)
end
function M.closest(d,t,p)
    local f,r,u=M.basis(d,t.h); local v={p[1]-t.p[1],p[2]-t.p[2],p[3]-t.p[3]}
    local axes={r,f,u}; local localPoint={}
    for i=1,3 do
        local q=(v[1]*axes[i][1]+v[2]*axes[i][2]+v[3]*axes[i][3])/d.s[i]
        localPoint[i]=math.max(d.lo[i],math.min(d.hi[i],q))
    end
    return M.world(d,t,localPoint)
end
function M.turn(d,t,delta)
    local center=M.center(d,t); local n=M.copy(t); n.h=(n.h+delta)%360
    local offset=M.offset(d,n,{(d.lo[1]+d.hi[1])/2,(d.lo[2]+d.hi[2])/2,(d.lo[3]+d.hi[3])/2})
    n.p={center[1]-offset[1],center[2]-offset[2],center[3]-offset[3]}; return n
end
function M.generic(d,protected)
    if type(d)~='table' or type(d.model)~='number' or not M.finite(d.model,4294967297) or d.model%1~=0 or protected[d.model] then return false end
    if not M.pose(d) or not M.vec(d.lo,100) or not M.vec(d.hi,100) or not M.vec(d.s,11) or type(d.basis)~='table' then return false end
    for i=1,3 do
        if d.s[i]<0.05 or d.lo[i]>=d.hi[i] or (d.hi[i]-d.lo[i])*d.s[i]>12 then return false end
        if not M.vec(d.basis[i],1.01) then return false end
        local v=d.basis[i]; if math.abs(v[1]^2+v[2]^2+v[3]^2-1)>0.01 then return false end
    end
    if (d.hi[3]-d.lo[3])*d.s[3]>4.0 then return false end
    for i=1,2 do for j=i+1,3 do
        local a,b=d.basis[i],d.basis[j]; if math.abs(a[1]*b[1]+a[2]*b[2]+a[3]*b[3])>0.01 then return false end
    end end
    return true
end
function M.genericId(d)
    return ('mapa:%s:%d:%d:%d'):format(d.model,math.floor(d.p[1]*100+0.5),math.floor(d.p[2]*100+0.5),math.floor(d.p[3]*100+0.5))
end
