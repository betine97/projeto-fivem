$ErrorActionPreference='Stop'
[Threading.Thread]::CurrentThread.CurrentCulture=[Globalization.CultureInfo]::InvariantCulture
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$taskOutput=Split-Path $PSScriptRoot
[void][IO.Directory]::CreateDirectory("$taskOutput/dados")
$taskRefs=@("$taskRoot/.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll","$taskRoot/.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll","$taskRoot/.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll")
foreach($taskRef in $taskRefs){Add-Type -Path $taskRef}
foreach($taskLine in [IO.File]::ReadAllLines("$taskRoot/laboratorio_fivem/work/assets_index.txt")) {
    [void][CodeWalker.GameFiles.JenkIndex]::Ensure([IO.Path]::GetFileNameWithoutExtension(($taskLine -split '\|')[-1]))
}
foreach($taskFile in Get-ChildItem "$taskRoot/teste-ilha/cayo_perico/originais/assets" -File) { [void][CodeWalker.GameFiles.JenkIndex]::Ensure($taskFile.BaseName) }
$taskRows=[Collections.Generic.List[string]]::new()
$taskRows.Add("map`tname`tx`ty`tz`tsx`tsz`tlod`tflags")
$taskSelection=Get-Content "$taskRoot/teste-ilha/cayo_perico/mapas_selecionados.json" -Raw | ConvertFrom-Json
foreach($taskName in $taskSelection) {
    $taskMap=[CodeWalker.GameFiles.YmapFile]::new()
    $taskMap.Load([IO.File]::ReadAllBytes("$taskRoot/teste-ilha/cayo_perico/originais/mapas/$taskName"))
    foreach($taskEntity in $taskMap.AllEntities) {
        $taskDef=$taskEntity._CEntityDef
        $taskRows.Add(($taskName,$taskDef.archetypeName.ToString(),$taskEntity.Position.X,$taskEntity.Position.Y,$taskEntity.Position.Z,$taskDef.scaleXY,$taskDef.scaleZ,$taskDef.lodLevel.ToString(),$taskDef.flags -join "`t"))
    }
}
[IO.File]::WriteAllLines("$taskOutput/dados/entidades_cayo.tsv",$taskRows)
Write-Output ('CAYO_ENTITY_CATALOG '+($taskRows.Count-1))
