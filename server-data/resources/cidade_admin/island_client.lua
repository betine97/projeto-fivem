local resource=GetCurrentResourceName()
local cfg=json.decode(LoadResourceFile(resource,'ui/cayo.json') or '{}')
local models={};for _,row in ipairs(cfg.objects or {}) do models[row.model]=row end
local function modelHash(name)return CidadeCapturedCatalog.hash(models[name])end
RegisterNetEvent('cidade_admin:capturedCatalog',function(data,images)
    if source~=65535 then return end
    if type(data)=='string' then
        local ok,decoded=pcall(json.decode,data)
        if not ok then return end
        data=decoded
    end
    if type(data)~='table' or type(data.objects)~='table' then return end
    if CidadeCapturedCatalog.merge(data)then
        for _,row in ipairs(data.objects)do models[row.model]=row end
    end
    -- Native SendNuiMessage forwards the ready JSON straight to Chromium.
    -- Do not decode/re-encode thumbnail data in the gameplay frame loop.
    if type(images)=='string' then SendNuiMessage(images)
    else SendNUIMessage({type='capturedCatalog',objects=data.objects,marks=data.marks})end
end)
local world,entities,pending,seq,editor,busy={revision=0,objects={}},{},{},0,nil,false
local generation,saving=0,false
local terrain=json.decode(LoadResourceFile(resource,'data/editor_terrain.json') or 'null')
local function terrainHeight(x,y)
    if not terrain then return end
    local u,v=(x-terrain.x)/terrain.dx,(y-terrain.y)/terrain.dy
    if u<0 or v<0 or u>=terrain.width-1 or v>=terrain.height-1 then return end
    local i,j=math.floor(u),math.floor(v);u=u-i;v=v-j
    local n=j*terrain.width+i+1;local a,b,c,d=terrain.z[n],terrain.z[n+1],terrain.z[n+terrain.width],terrain.z[n+terrain.width+1]
    return u>=v and a+(b-a)*u+(d-b)*v or a+(d-c)*u+(c-a)*v
end
local function say(text)CidadeAdminPanel.message(text)end
local function request(data,cb)
    seq=seq%2147483646+1;pending[seq]={cb=cb,at=GetGameTimer()};TriggerServerEvent('cidade_admin:islandRequest',seq,data)
end
RegisterNetEvent('cidade_admin:islandReply',function(nonce,result)
    if source~=65535 or type(result)~='table' or not pending[nonce] then return end
    local cb=pending[nonce].cb;pending[nonce]=nil;cb(result)
end)
local function drop(id)if entities[id] then DeleteEntity(entities[id].object);entities[id]=nil end end
RegisterNetEvent('cidade_admin:islandWorld',function(data)
    if source~=65535 or type(data)~='table' or type(data.objects)~='table' then return end
    world=data;local valid={}
    for _,row in ipairs(world.objects) do
        valid[row.id]=true
        local old=entities[row.id]
        if old and (old.row.model~=row.model or old.row.x~=row.x or old.row.y~=row.y or old.row.z~=row.z or old.row.heading~=row.heading or old.row.pitch~=row.pitch or old.row.roll~=row.roll or old.row.scale~=row.scale) then drop(row.id) end
    end
    for id in pairs(entities) do if not valid[id] then drop(id) end end
    SendNUIMessage({type='islandWorld',data=world})
end)
local function transform(object,row)
    -- CFX natives read raw float arguments. JSON's integer 1 must not become
    -- an almost-zero up vector, which flattens the object vertically.
    local a=math.rad(row.heading);local s=row.scale+0.0;local c,t=math.cos(a),math.sin(a)
    local x,y=math.rad(row.pitch or 0),math.rad(row.roll or 0)
    local cx,sx,cy,sy=math.cos(x),math.sin(x),math.cos(y),math.sin(y)
    SetEntityMatrix(object,-t*cx*s,c*cx*s,sx*s,(c*cy-t*sx*sy)*s,(t*cy+c*sx*sy)*s,-cx*sy*s,(c*sy+t*sx*cy)*s,(t*sy-c*sx*cy)*s,cx*cy*s,row.x+0.0,row.y+0.0,row.z+0.0)
end
local function load(model)
    local hash=modelHash(model)
    if not IsModelInCdimage(hash) or not IsModelValid(hash) then return end
    RequestModel(hash);local stop=GetGameTimer()+10000
    while not HasModelLoaded(hash) and GetGameTimer()<stop do Wait(20) end
    if HasModelLoaded(hash) then return hash end
    SetModelAsNoLongerNeeded(hash)
end
local function objectAt(row,ghost)
    local object=CreateObjectNoOffset(modelHash(row.model),row.x,row.y,row.z,false,false,false)
    if object==0 then return end
    SetEntityAsMissionEntity(object,true,true);FreezeEntityPosition(object,true);transform(object,row)
    SetEntityLodDist(object,models[row.model].drawDistance or 1800)
    if ghost then SetEntityCollision(object,false,false);SetEntityVisible(object,false,false) end
    return object
end
local function cancelEditor()
    if not editor then return end
    for _,object in ipairs(editor.ghosts) do DeleteEntity(object) end
    if editor.id and entities[editor.id] then SetEntityVisible(entities[editor.id].object,true,false) end
    SetModelAsNoLongerNeeded(modelHash(editor.model));editor=nil
end
local function front(e)
    local p=GetEntityCoords(PlayerPedId())
    if e.followOffset then return vector3(p.x+e.followOffset.x,p.y+e.followOffset.y,p.z) end
    local m=models[e.model];local lo,hi=m.bbMin,m.bbMax
    local radius=math.sqrt((hi[1]-lo[1])^2+(hi[2]-lo[2])^2)*e.scale*.5
    -- Leave room for the entire bounding box, including tall models and groups.
    local distance=math.max(4,radius+2,(hi[3]-lo[3])*e.scale*1.3)+(e.radius or 0)
    local yaw=math.rad(GetGameplayCamRot(2).z)
    local a=math.rad(e.heading);local cx,cy=(lo[1]+hi[1])*.5*e.scale,(lo[2]+hi[2])*.5*e.scale
    return vector3(p.x-math.sin(yaw)*distance-math.cos(a)*cx+math.sin(a)*cy,p.y+math.cos(yaw)*distance-math.sin(a)*cx-math.cos(a)*cy,p.z)
end
local function bottomOffset(e)
    local x,y=math.rad(e.pitch or 0),math.rad(e.roll or 0)
    local coefficients={-math.cos(x)*math.sin(y),math.sin(x),math.cos(x)*math.cos(y)}
    local m=models[e.model];local low=0.0
    for i,value in ipairs(coefficients)do low=low+value*(value>=0 and m.bbMin[i] or m.bbMax[i])end
    return low*e.scale
end
local function updatePreview()
    local e=editor
    if not e then return end
    if not e.locked then e.center=front(e) end
    local p=e.center;local b=cfg.bounds
    if cfg.editRegions then for _,region in ipairs(cfg.editRegions)do if p.x>=region.minX and p.x<=region.maxX and p.y>=region.minY and p.y<=region.maxY then b=region;break end end end
    e.valid=true;e.rows={}
    for i,object in ipairs(e.ghosts) do
        local offset=e.offsets[i];local x,y=p.x+offset.x,p.y+offset.y
        local probe=math.max(p.z+100,b.maxZ+100)
        local expected=terrainHeight(x,y)
        RequestCollisionAtCoord(x,y,expected or p.z)
        local found,gz=GetGroundZFor_3dCoord(x,y,probe,false);found=found==true or found==1
        if not found and expected and expected>0 then found=true;gz=expected end
        local original=e.original;local bottom=bottomOffset(e)
        if original and found and not e.heightInitialized then
            e.height=original.z-(gz-bottom);e.heightInitialized=true
        end
        local z=found and gz-bottom+e.height or (original and original.z or p.z)
        local row={model=e.model,x=x,y=y,z=z,heading=(e.heading+offset.heading)%360,pitch=e.pitch,roll=e.roll,scale=e.scale}
        if not found or x<b.minX or x>b.maxX or y<b.minY or y>b.maxY or z<b.minZ or z>b.maxZ then e.valid=false end
        e.rows[i]=row;transform(object,row);SetEntityVisible(object,found,false)
    end
end
local function begin(data,cb)
    if saving then cb({ok=false,message='A gravação anterior está sendo concluída. Tente novamente em instantes.'});return end
    local model=models[data.model]
    local count=tonumber(data.count) or 1;local radius=tonumber(data.radius) or 0
    if not model or count%1~=0 or count<1 or count>32 or radius<0 or radius>50 or (count>1 and radius<1) then cb({ok=false,message='Escolha um modelo e uma quantidade de 1 a 32.'});return end
    local scale=tonumber(data.scale) or 1
    if scale~=scale or scale<.25 or scale>3 then cb({ok=false,message='A escala deve ficar entre 0,25 e 3.'});return end
    generation=generation+1;local ticket=generation;cancelEditor()
    if data.id then count=1 end
    busy=true
    request({action='begin',model=data.model,id=data.id},function(result)
        if ticket~=generation then cb({ok=false,message='Prévia anterior abandonada.'});return end
        if not result.ok then busy=false;cb(result);return end
        CreateThread(function()
            local hash=load(data.model)
            if ticket~=generation then if hash then SetModelAsNoLongerNeeded(hash) end;cb({ok=false,message='Prévia anterior abandonada.'});return end
            if not hash or not LocalPlayer.state.cidadeAdmin then if hash then SetModelAsNoLongerNeeded(hash) end;busy=false;cb({ok=false,message='Modelo indisponível ou acesso ADM revogado.'});return end
            local original
            for _,row in ipairs(world.objects) do if row.id==data.id then original=row end end
            if data.id and not original then SetModelAsNoLongerNeeded(hash);busy=false;cb({ok=false,message='Objeto não encontrado. Atualize a lista.'});return end
            local p=GetEntityCoords(PlayerPedId())
            editor={model=data.model,id=data.id,revision=result.data.revision,heading=original and original.heading or GetEntityHeading(PlayerPedId()),scale=original and original.scale or scale,height=0,ghosts={},rows={},offsets={},locked=false,radius=count>1 and radius or 0,center=p,original=original,valid=false}
            editor.pitch=original and original.pitch or model.defaultPitch or 0;editor.roll=original and original.roll or model.defaultRoll or 0
            if original then editor.followOffset=vector3(original.x-p.x,original.y-p.y,0) end
            editor.center=front(editor)
            for i=1,count do
                local theta=i*2.399963229728653;local distance=count==1 and 0 or radius*math.sqrt((i-.5)/count)
                editor.offsets[i]={x=math.cos(theta)*distance,y=math.sin(theta)*distance,heading=count==1 and 0 or math.random()*360}
                local row={model=data.model,x=p.x,y=p.y,z=p.z,heading=editor.heading,scale=editor.scale};local obj=objectAt(row,true)
                if obj then editor.ghosts[#editor.ghosts+1]=obj end
            end
            if #editor.ghosts~=count then cancelEditor();busy=false;cb({ok=false,message='Não foi possível criar a prévia.'});return end
            if original and entities[original.id] then SetEntityVisible(entities[original.id].object,false,false) end
            updatePreview()
            CidadeAdminPanel.close();busy=false;cb({ok=true,message=result.message});say('Editor Ilha: o objeto acompanha você. ↑/↓ altura • ←/→ giram • Enter salva • Backspace cancela • F fixa/acompanha • +/- escala. V muda a câmera. Caps Lock retoma um objeto salvo próximo.')
        end)
    end)
end
RegisterNUICallback('islandAction',function(data,cb)
    if not CidadeAdminPanel.isOpen() or not LocalPlayer.state.cidadeAdmin then cb({ok=false,message='Abra o painel com acesso ADM.'});return end
    if type(data)~='table' then cb({ok=false,message='Pedido inválido.'});return end
    if data.action=='begin' then begin(data,cb)
    elseif data.action=='locate' then
        for _,row in ipairs(world.objects) do if row.id==data.id then
            SetNewWaypoint(row.x,row.y);cb({ok=true,message='Local marcado no mapa.'});return
        end end
        cb({ok=false,message='Objeto não encontrado.'})
    elseif data.action=='list' or data.action=='delete' or data.action=='undo' then
        request({action=data.action,id=data.id,revision=world.revision},cb)
    else cb({ok=false,message='Ação inválida.'}) end
end)
CreateThread(function()
    TriggerServerEvent('cidade_admin:islandSync')
    while true do
        Wait(800)
        local cam=GetGameplayCamCoord();local bucket=LocalPlayer.state.cidadeBucket or 0;local created=0
        for _,row in ipairs(world.objects) do
            local dist=#(cam-vector3(row.x,row.y,row.z));local reach=models[row.model] and models[row.model].drawDistance or 1800
            if dist<reach+100 and bucket==0 then
                if not entities[row.id] and not (editor and editor.id==row.id) then
                    local hash=load(row.model)
                    -- Re-read after asynchronous model loading: an edit may have deleted it.
                    local current=false;for _,v in ipairs(world.objects) do if v.id==row.id and v==row then current=true end end
                    if hash and current then local obj=objectAt(row,false);if obj then entities[row.id]={object=obj,row=row};created=created+1 end end
                    if hash then SetModelAsNoLongerNeeded(hash) end
                    if created>=30 then break end
                end
            elseif dist>reach+250 or bucket~=0 then drop(row.id) end
        end
        for nonce,q in pairs(pending) do if GetGameTimer()-q.at>12000 then pending[nonce]=nil;q.cb({ok=false,message='Servidor não respondeu.'}) end end
    end
end)
local function hint(text)
    SetTextFont(0);SetTextScale(.30,.30);SetTextColour(255,255,255,255);SetTextOutline();BeginTextCommandDisplayText('STRING');AddTextComponentSubstringPlayerName(text);EndTextCommandDisplayText(.02,.85)
end
CreateThread(function()
    while true do
        if not editor then Wait(300) else
            Wait(0)
            -- A network reply or cancelarilha may remove it during Wait(0).
            if not editor then goto continue end
            if not LocalPlayer.state.cidadeAdmin or (LocalPlayer.state.cidadeBucket or 0)~=0 or IsEntityDead(PlayerPedId()) then cancelEditor() else
                if IsPauseMenuActive() or IsNuiFocused() then goto continue end
                for _,key in ipairs({201,202,23,174,175,172,173,10,11,96,97,24,25}) do DisableControlAction(0,key,true) end
                DisablePlayerFiring(PlayerId(),true)
                if IsDisabledControlJustPressed(0,202) then cancelEditor();say('Prévia cancelada.');goto continue end
                if IsDisabledControlJustPressed(0,23) then editor.locked=not editor.locked end
                local step=math.min(GetFrameTime(),.05)*((IsControlPressed(0,21) or IsDisabledControlPressed(0,21)) and 180 or 45)
                if IsDisabledControlPressed(0,174) then editor.heading=(editor.heading+step)%360 end
                if IsDisabledControlPressed(0,175) then editor.heading=(editor.heading-step)%360 end
                if IsDisabledControlPressed(0,172) or IsDisabledControlPressed(0,10) then editor.height=editor.height+.02*step end
                if IsDisabledControlPressed(0,173) or IsDisabledControlPressed(0,11) then editor.height=editor.height-.02*step end
                if IsDisabledControlJustPressed(0,96) then editor.scale=math.min(3,editor.scale+.05) end
                if IsDisabledControlJustPressed(0,97) then editor.scale=math.max(.25,editor.scale-.05) end
                updatePreview()
                hint(('EDITOR ILHA | escala %.2f | altura %+.2f | %s~n~%s~n~Enter salva | Backspace cancela | F fixa/acompanha~n~←/→ giram | ↑/↓ altura | +/- escala | V câmera'):format(editor.scale,editor.height,editor.locked and 'fixo' or 'acompanhando',editor.valid and 'Pronto para posicionar' or 'Sem chão válido neste ponto'))
                if not busy and IsDisabledControlJustPressed(0,201) then
                    if not editor.valid then say('Escolha um ponto de chão carregado dentro da ilha.') else
                        local current=editor
                        busy=true;saving=true;request({action='save',id=editor.id,revision=editor.revision,rows=editor.rows},function(result)
                            busy=false;saving=false;say(result.message)
                            if editor==current and (result.ok or result.data and result.data.revision)then cancelEditor()end
                        end)
                    end
                end
            end
        end
        ::continue::
    end
end)
-- Distance to the rotated model bounds lets large objects be selected at their edge.
local function nearestSaved()
    local p=GetEntityCoords(PlayerPedId());local best,distance=nil,6
    for _,row in ipairs(world.objects) do
        local m=models[row.model]
        if m and entities[row.id] then
            local a=math.rad(row.heading);local dx,dy=p.x-row.x,p.y-row.y
            local x=(math.cos(a)*dx+math.sin(a)*dy)/row.scale
            local y=(-math.sin(a)*dx+math.cos(a)*dy)/row.scale
            local z=(p.z-row.z)/row.scale;local lo,hi=m.bbMin,m.bbMax
            local pitch,roll=math.rad(row.pitch or 0),math.rad(row.roll or 0)
            y,z=math.cos(pitch)*y+math.sin(pitch)*z,-math.sin(pitch)*y+math.cos(pitch)*z
            x,z=math.cos(roll)*x-math.sin(roll)*z,math.sin(roll)*x+math.cos(roll)*z
            local function gap(v,l,h)return math.max(l-v,0,v-h) end
            local d=math.sqrt(gap(x,lo[1],hi[1])^2+gap(y,lo[2],hi[2])^2+gap(z,lo[3],hi[3])^2)*row.scale
            if d<distance then best=row;distance=d end
        end
    end
    return best
end
RegisterCommand('editarilhaperto',function()
    if editor or busy or not LocalPlayer.state.cidadeAdmin or (LocalPlayer.state.cidadeBucket or 0)~=0 or CidadeAdminPanel.isOpen() or IsNuiFocused() or IsPauseMenuActive() then return end
    local row=nearestSaved()
    if not row then say('Aproxime-se de um objeto salvo pelo editor da ilha (até 6 metros).');return end
    begin({model=row.model,id=row.id,count=1,radius=0},function(result)if not result.ok then say(result.message) end end)
end,false)
RegisterKeyMapping('editarilhaperto','Ilha: editar objeto salvo próximo','keyboard','CAPITAL')
RegisterCommand('cancelarilha',function()cancelEditor()end,false)
RegisterCommand('editorilhadiag',function()
    local count=0;for _ in pairs(entities) do count=count+1 end
    print(('[Editor Ilha] revisão=%d salvos=%d visíveis=%d capturados=%d | edição=%s'):format(world.revision,#world.objects,count,#CidadeCapturedCatalog.objects,editor and editor.model or 'nenhuma'))
    if editor and editor.ghosts[1]then
        local forward,right,up=GetEntityMatrix(editor.ghosts[1])
        print(('[Editor Ilha] escala=%.2f eixos=%.3f/%.3f/%.3f seguindo=%s chão=%s'):format(editor.scale,#forward,#right,#up,tostring(not editor.locked),tostring(editor.valid)))
    end
end,false)
AddEventHandler('onResourceStop',function(name)
    if name~=resource then return end
    cancelEditor();for id in pairs(entities) do drop(id) end
end)
