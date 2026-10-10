$ErrorActionPreference='Stop'
$taskProject=Split-Path $PSScriptRoot
$taskWorkspace=Split-Path $taskProject
Add-Type -Path (Join-Path $taskWorkspace '.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll')
Add-Type -Path (Join-Path $taskWorkspace '.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll')
Add-Type -Path (Join-Path $taskWorkspace '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll')
$taskRows=@()
foreach($taskFile in Get-ChildItem -LiteralPath (Join-Path $taskProject 'fivem/stream') -File) {
    $taskReader=switch($taskFile.Extension){'.ydr'{'YdrFile'} '.ybn'{'YbnFile'} '.ymap'{'YmapFile'} '.ytyp'{'YtypFile'} '.ytd'{'YtdFile'} '.ymf'{'YmfFile'} default{throw 'Tipo inesperado'}}
    $taskAsset=New-Object ('CodeWalker.GameFiles.'+$taskReader)
    if($taskReader -eq 'YmfFile'){$taskAsset.Load([IO.File]::ReadAllBytes($taskFile.FullName),$null)}else{$taskAsset.Load([IO.File]::ReadAllBytes($taskFile.FullName))}
    if($taskReader -eq 'YdrFile' -and $null -eq $taskAsset.Drawable){throw ('Drawable invalido: '+$taskFile.Name)}
    if($taskReader -eq 'YbnFile' -and $null -eq $taskAsset.Bounds){throw ('Colisao invalida: '+$taskFile.Name)}
    $taskRows+=@{file=$taskFile.Name;reader=$taskReader;bytes=$taskFile.Length}
}
@{passed=$true;assets=$taskRows;in_game_verified=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskProject 'nativo/validacao_codewalker.json') -Encoding utf8
Write-Output ('ISLAND_NATIVE_VALIDATED '+$taskRows.Count)
