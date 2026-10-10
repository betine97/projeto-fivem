$ErrorActionPreference = 'Stop'
$lightingRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Add-Type -Path (Join-Path $lightingRoot '.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll')
Add-Type -Path (Join-Path $lightingRoot '.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll')
Add-Type -Path (Join-Path $lightingRoot '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll')
$lightingResults = foreach ($lightingPath in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'package/stream') -Filter *.ydr) {
    $lightingFile = New-Object CodeWalker.GameFiles.YdrFile
    $lightingFile.Load([IO.File]::ReadAllBytes($lightingPath.FullName))
    if ($null -eq $lightingFile.Drawable) { throw "Missing drawable $($lightingPath.Name)" }
    [pscustomobject]@{ model=$lightingPath.Name; lights=$lightingFile.Drawable.LightAttributes.EntriesCount; nativeLoaded=$true }
}
$lightingRoof = $lightingResults | Where-Object model -eq 'mansao_teto.ydr'
$lightingPendants = $lightingResults | Where-Object model -eq 'mansao_pendentes.ydr'
if ($lightingRoof.lights -ne 88 -or $lightingPendants.lights -ne 9 -or ($lightingResults | Measure-Object -Property lights -Sum).Sum -ne 97) { throw 'Independent light count mismatch' }
$lightingResults | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'codewalker_verification.json') -Encoding utf8
$lightingResults | Format-Table
