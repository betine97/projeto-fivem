param([switch]$ProbeOnly)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$taskOut=Join-Path $taskRoot 'teste-ilha/cayo_perico'
$taskRefs=@("$taskRoot/.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll","$taskRoot/.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll","$taskRoot/.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll")
foreach($taskRef in $taskRefs){Add-Type -Path $taskRef}
$taskRefs+=@(Get-ChildItem -LiteralPath "$PSHOME/ref" -Filter '*.dll' | ForEach-Object {$_.FullName})
Add-Type -Path (Join-Path $PSScriptRoot 'RelocarCayo.cs') -ReferencedAssemblies $taskRefs -CompilerOptions '/nowarn:1701'
$taskStream=Join-Path $taskOut 'fivem/stream'
[void][IO.Directory]::CreateDirectory($taskStream)
if(-not $ProbeOnly){
    $taskSelection=Get-Content "$taskOut/mapas_selecionados.json" -Raw | ConvertFrom-Json
    [RelocarCayo]::Maps("$taskOut/originais/mapas",$taskStream,[string[]]$taskSelection) | Set-Content "$taskOut/mapas_relocados.tsv"
    Write-Host 'MAPAS_RELOCADOS'
    [RelocarCayo]::BoundsFiles("$taskOut/originais/colisoes",$taskStream) | Set-Content "$taskOut/colisoes_relocadas.tsv"
    Write-Host 'COLISOES_RELOCADAS'
}
[RelocarCayo]::ProbeGround("$taskOut/originais/colisoes",$taskStream) | Set-Content "$taskOut/solo_validado.tsv"
Write-Host 'SOLO_VALIDADO'
