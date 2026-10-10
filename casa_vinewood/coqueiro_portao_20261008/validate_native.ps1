$ErrorActionPreference='Stop'
$taskRoot=Split-Path (Split-Path $PSScriptRoot)
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll')
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll')
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll')
$taskCount=0
foreach($taskFile in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'package/stream') -File) {
 $taskClass=if($taskFile.Extension -eq '.ydr'){'YdrFile'}else{'YtypFile'}
 $taskAsset=New-Object ('CodeWalker.GameFiles.'+$taskClass)
 $taskAsset.Load([IO.File]::ReadAllBytes($taskFile.FullName))
 if($taskClass -eq 'YdrFile') {
  if($null -eq $taskAsset.Drawable){throw 'Missing drawable'}
  if($taskAsset.Drawable.BoundingBoxMax.Y -lt .066){throw 'Gate details excluded from bounding box'}
 }
 $taskCount++
}
@{passed=$true;native_assets=$taskCount} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'native_validation.json') -Encoding utf8
Write-Output ('NATIVE_VALIDATED '+$taskCount)
