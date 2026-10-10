-- Fixed native lights. Restrict optical cleanup to the interior camera.
local config=json.decode(LoadResourceFile(GetCurrentResourceName(),'iluminacao_ambiente.json'))
local profile=config.clean_postfx
local enabled=profile and profile.enabled
local index=-1
local inside=false
local available={}
local conflict=false

local function polygonContains(x,y,polygon)
    local result=false
    local j=#polygon
    for i=1,#polygon do
        local a,b=polygon[i],polygon[j]
        if (a[2]>y)~=(b[2]>y) and x<(b[1]-a[1])*(y-a[2])/(b[2]-a[2])+a[1] then result=not result end
        j=i
    end
    return result
end
local function interiorCamera()
    if not profile then return false end
    local c=GetGameplayCamCoord()
    local x,y,z=c.x-config.origin[1],c.y-config.origin[2],c.z-config.origin[3]
    if z<profile.z_min or z>profile.z_max then return false end
    for _,polygon in ipairs(profile.interior_polygons) do
        if polygonContains(x,y,polygon) then return true end
    end
    return false
end
local function release()
    -- Never clear a replacement owned by another script.
    if index>=0 and GetExtraTimecycleModifierIndex()==index then ClearExtraTimecycleModifier() end
end
local function update()
    local previousInside=inside
    inside=interiorCamera()
    local extra=GetExtraTimecycleModifierIndex()
    if inside and not previousInside then
        print(('[Mansao luz] Entrada: clima hashes %s -> %s; filtro principal %s; extra anterior %s.'):format(
            tostring(GetPrevWeatherTypeHashName()),tostring(GetNextWeatherTypeHashName()),
            tostring(GetTimecycleModifierIndex()),tostring(extra)))
    end
    if not enabled or not inside or index<0 then release();conflict=false;return end
    if extra<0 then SetExtraTimecycleModifier(profile.modifier);conflict=false
    elseif extra~=index then
        if not conflict then print('[Mansao luz] Filtro secundario ocupado; nitidez local aguardando, sem substituir outro recurso.') end
        conflict=true
    end
end
local function name(i)
    if i<0 then return 'nenhum' end
    return (GetTimecycleModifierNameByIndex(i) or '?')..' ['..i..']'
end
local function weatherName(hash)
    for _,v in ipairs({'EXTRASUNNY','CLEAR','NEUTRAL','SMOG','FOGGY','OVERCAST','CLOUDS','CLEARING','RAIN','THUNDER','SNOW','BLIZZARD','SNOWLIGHT','XMAS','HALLOWEEN'}) do
        if GetHashKey(v)==hash then return v end
    end
    return tostring(hash)
end
local function status(_,args)
    local mode=args and args[1]
    if mode=='limpo' then enabled=true;update()
    elseif mode=='original' then enabled=false;update() end
    print(('[Mansao luz] PERFIL v9: %d spots quentes, %d pendentes amarelos; destaques dourados, paredes e sombras locais.'):format(config.native_ceiling_count,config.native_pendant_count))
    print('[Mansao luz] Nitidez local: '..(GetExtraTimecycleModifierIndex()==index and index>=0 and 'ativa' or 'inativa')..'; camera interna: '..tostring(inside))
    print('[Mansao luz] Filtro principal: '..name(GetTimecycleModifierIndex())..'; secundario: '..name(GetExtraTimecycleModifierIndex()))
    print('[Mansao luz] Clima observado: '..weatherName(GetPrevWeatherTypeHashName())..' -> '..weatherName(GetNextWeatherTypeHashName()))
    print('[Mansao luz] Comparar filtro: luzmansao original / luzmansao limpo. Luzes fisicas constantes; clima e nevoa nao alterados.')
end
RegisterCommand('luzmansao',status,false)
RegisterCommand('mansaoluzes',status,false)

CreateThread(function()
    if not profile then return end
    -- A clean modifier changes only these optical variables, never weather,
    -- fog, exposure, colour grading, primary filters, or interior/MLO data.
    local ok,errorText=pcall(function()
        local supported={}
        for i=0,GetTimecycleVarCount()-1 do supported[GetTimecycleVarNameByIndex(i)]=true end
        index=GetTimecycleModifierIndexByName(profile.modifier)
        if index<0 then index=CreateTimecycleModifier(profile.modifier) end
        if index<0 then error('Nao foi possivel criar o perfil optico') end
        for variable,value in pairs(profile.variables) do
            if supported[variable] then SetTimecycleModifierVar(profile.modifier,variable,value,value);available[variable]=value end
        end
        if next(available)==nil then error('Nenhuma variavel optica suportada') end
    end)
    if not ok then
        release()
        if index>=0 then RemoveTimecycleModifier(profile.modifier) end
        index=-1
        print('[Mansao luz] Perfil optico indisponivel: '..tostring(errorText))
        return
    end
    print('[Mansao luz] Perfil v9 carregado: bloom e desfoque locais controlados, sem modificar o clima.')
    while true do update();Wait(250) end
end)
AddEventHandler('onResourceStop',function(resource)
    if resource~=GetCurrentResourceName() then return end
    release()
    if index>=0 then RemoveTimecycleModifier(profile.modifier);index=-1 end
end)
