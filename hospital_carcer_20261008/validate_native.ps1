$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll')
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll')
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll')
$taskReport=@()
foreach($taskFile in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'package/stream') -File) {
 $taskClass=switch($taskFile.Extension){'.ydr'{'YdrFile'} '.ydd'{'YddFile'} '.ybn'{'YbnFile'} '.ymap'{'YmapFile'} '.ytyp'{'YtypFile'} default {throw 'Unsupported asset'}}
 $taskAsset=New-Object ('CodeWalker.GameFiles.'+$taskClass)
 $taskAsset.Load([IO.File]::ReadAllBytes($taskFile.FullName))
 if($taskClass -eq 'YdrFile' -and $null -eq $taskAsset.Drawable){throw ('Missing drawable '+$taskFile.Name)}
 $taskReport+=@{file=$taskFile.Name;reader=$taskClass;bytes=$taskFile.Length}
}
@{passed=$true;assets=$taskReport;in_game_verified=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'native_validation.json') -Encoding utf8
Write-Output ('NATIVE_VALIDATED '+$taskReport.Count)
