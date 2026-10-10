local animals,applied={},{}
RegisterNetEvent('fauna_ilha:update',function(rows)if source==65535 and type(rows)=='table' then animals=rows end end)
CreateThread(function()
    while true do
        Wait(500)
        local alive={}
        for _,a in ipairs(animals) do
            alive[a.id]=true
            if NetworkDoesEntityExistWithNetworkId(a.id) then
                local ped=NetToPed(a.id)
                if ped~=0 and NetworkHasControlOfEntity(ped) and not IsEntityDead(ped) then
                    local last=applied[a.id];local now=GetGameTimer()
                    if not last then
                        RequestCollisionAtCoord(a.home[1],a.home[2],a.home[3])
                        SetBlockingOfNonTemporaryEvents(ped,true);SetPedFleeAttributes(ped,0,false)
                        SetPedCombatAttributes(ped,46,true);SetPedCombatAbility(ped,1);SetPedCombatMovement(ped,2)
                        SetPedSeeingRange(ped,35);SetPedHearingRange(ped,25)
                        GiveWeaponToPed(ped,joaat(a.species=='onca_parda' and 'WEAPON_ANIMAL' or 'WEAPON_UNARMED'),1,false,true)
                    end
                    local target=a.target and GetPlayerFromServerId(a.target) or -1
                    target=target~=-1 and GetPlayerPed(target) or 0
                    local signature=a.mode..':'..tostring(target)
                    if not last or last.signature~=signature or now-last.at>8000 then
                        ClearPedTasks(ped)
                        if a.mode=='attack' and target~=0 then TaskCombatPed(ped,target,0,16)
                        elseif a.mode=='flee' and target~=0 then TaskSmartFleePed(ped,target,30,8000,false,false)
                        else
                            local angle=math.random()*math.pi*2;local r=a.mode=='return' and 0 or math.random()*12
                            local x,y=a.home[1]+math.cos(angle)*r,a.home[2]+math.sin(angle)*r
                            local found,z=GetGroundZFor_3dCoord(x,y,a.home[3]+30,false)
                            if (found==true or found==1) and math.abs(z-a.home[3])<4 then TaskGoStraightToCoord(ped,x,y,z,1.0,8000,0,.5)
                            else TaskStandStill(ped,3000) end
                        end
                        applied[a.id]={signature=signature,at=now}
                    end
                else applied[a.id]=nil end
            end
        end
        for id in pairs(applied) do if not alive[id] then applied[id]=nil end end
    end
end)
RegisterCommand('faunadiag',function()
    local loaded=0;for _,a in ipairs(animals) do if NetworkDoesEntityExistWithNetworkId(a.id) then loaded=loaded+1 end end
    print(('[Fauna Ilha] ativos=%d carregados=%d onça-parda=%s macaco=%s'):format(#animals,loaded,tostring(IsModelInCdimage(joaat('a_c_mtlion'))),tostring(IsModelInCdimage(joaat('a_c_chimp')))))
end,false)
