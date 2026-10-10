$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
Add-Type -Path "$taskRoot/.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll"
Add-Type -Path "$taskRoot/.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll"
Add-Type -Path "$taskRoot/.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll"
$taskOut=Join-Path $taskRoot 'teste-ilha/cayo_perico'
$taskMaps=@(Get-ChildItem "$taskOut/originais/mapas/*.ymap" | ForEach-Object {
    $m=[CodeWalker.GameFiles.YmapFile]::new();$m.Name=$_.Name;$m.Load([IO.File]::ReadAllBytes($_.FullName))
    [pscustomobject]@{name=$_.Name;flags=$m.CMapData.flags;content=$m.CMapData.contentFlags;min=@($m.CMapData.entitiesExtentsMin.X,$m.CMapData.entitiesExtentsMin.Y,$m.CMapData.entitiesExtentsMin.Z);max=@($m.CMapData.entitiesExtentsMax.X,$m.CMapData.entitiesExtentsMax.Y,$m.CMapData.entitiesExtentsMax.Z);entities=$m.AllEntities.Count;mlo=$m.MloEntities.Count;grass=$m.GrassInstanceBatches.Count;containers=$m.CMapData.containerLods.Count1;props=$m.CMapData.instancedData.PropInstanceList.Count1;physics=@($m.physicsDictionaries | ForEach-Object {$_.Hash})}
})
$taskMaps | ConvertTo-Json -Depth 8 | Set-Content "$taskOut/auditoria_mapas.json"
$taskBounds=@(Get-ChildItem "$taskOut/originais/colisoes/*.ybn" | ForEach-Object {
    $b=[CodeWalker.GameFiles.YbnFile]::new();$b.Name=$_.Name;$b.Load([IO.File]::ReadAllBytes($_.FullName));$v=$b.Bounds
    [pscustomobject]@{name=$_.Name;min=@($v.BoxMin.X,$v.BoxMin.Y,$v.BoxMin.Z);max=@($v.BoxMax.X,$v.BoxMax.Y,$v.BoxMax.Z);type=$v.Type.ToString();children=$v.Children.data_items.Count}
})
$taskBounds | ConvertTo-Json -Depth 8 | Set-Content "$taskOut/auditoria_colisoes.json"
Write-Host ('AUDITADOS mapas='+$taskMaps.Count+' colisoes='+$taskBounds.Count)
