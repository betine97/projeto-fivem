FaunaPolicy={maxAnimals=24,spawnDistance=220,removeDistance=360,monkeyPackMinimum=2}
function FaunaPolicy.behavior(species,members,distance,vertical,wasAttacking)
    if vertical>5 then return 'roam' end
    if species=='macaco' and members<FaunaPolicy.monkeyPackMinimum then return distance<18 and 'flee' or 'roam' end
    local enter=species=='onca_parda' and 20 or 12
    local leave=species=='onca_parda' and 34 or 23
    return distance<(wasAttacking and leave or enter) and 'attack' or 'roam'
end
