$ErrorActionPreference='Stop'
$taskDir=$PSScriptRoot
$taskRoot=Split-Path (Split-Path $taskDir)
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll')
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll')
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll')
$taskVerification=Get-Content -LiteralPath (Join-Path $taskDir 'verification.json') -Raw | ConvertFrom-Json
$taskCount=0
$taskBear=$null
foreach($taskRelative in $taskVerification.install_files) {
 if(-not $taskRelative.StartsWith('stream/')) { continue }
 $taskPath=Join-Path $taskDir $taskRelative
 $taskClass=switch([IO.Path]::GetExtension($taskPath)) { '.ydr' {'YdrFile'} '.ybn' {'YbnFile'} '.ytyp' {'YtypFile'} '.ymap' {'YmapFile'} default {throw 'Unexpected asset type'} }
 $taskAsset=New-Object ('CodeWalker.GameFiles.'+$taskClass)
 $taskAsset.Load([IO.File]::ReadAllBytes($taskPath))
 if($taskClass -eq 'YdrFile' -and $null -eq $taskAsset.Drawable) { throw ('No drawable: '+$taskRelative) }
 if($taskRelative -eq 'stream/mansao_tapete_urso.ydr') {
  $taskBear=@{sphereRadius=$taskAsset.Drawable.BoundingSphereRadius; minX=$taskAsset.Drawable.BoundingBoxMin.X; maxX=$taskAsset.Drawable.BoundingBoxMax.X}
  if($taskBear.sphereRadius -lt 2.3 -or $taskBear.minX -gt -1.87 -or $taskBear.maxX -lt 1.87) {throw 'The serialized rug bounds exclude its silhouette'}
 }
 $taskCount++
}
if($taskCount -ne $taskVerification.assets_loaded) {throw 'Validation count mismatch'}
@{passed=$true;validated=$taskCount;bearDrawable=$taskBear} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskDir 'codewalker_validation.json') -Encoding utf8
Write-Output ('CODEWALKER_VALIDATED '+$taskCount)
