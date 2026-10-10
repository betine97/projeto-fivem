$ErrorActionPreference='Stop'
$taskRoot=Split-Path (Split-Path $PSScriptRoot)
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll')
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll')
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll')
$taskCount=0
foreach($taskFile in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'package/stream') -File) {
 $taskClass=if($taskFile.Extension -eq '.ydr'){'YdrFile'}else{'YbnFile'}
 $taskAsset=New-Object ('CodeWalker.GameFiles.'+$taskClass)
 $taskAsset.Load([IO.File]::ReadAllBytes($taskFile.FullName))
 if($taskClass -eq 'YdrFile' -and $null -eq $taskAsset.Drawable){throw 'Missing drawable'}
 if($taskClass -eq 'YbnFile' -and $null -eq $taskAsset.Bounds){throw 'Missing bounds'}
 $taskCount++
}
@{passed=$true;native_assets=$taskCount} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'native_validation.json') -Encoding utf8
Write-Output ('NATIVE_VALIDATED '+$taskCount)
