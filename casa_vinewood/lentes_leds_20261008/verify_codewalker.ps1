$ErrorActionPreference = 'Stop'
$lightingRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Add-Type -Path (Join-Path $lightingRoot '.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll')
Add-Type -Path (Join-Path $lightingRoot '.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll')
Add-Type -Path (Join-Path $lightingRoot '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll')
$expected = @{ 'mansao_spot_embutido.ydr'=0; 'mansao_pendentes.ydr'=9; 'mansao_spots_led.ydr'=20; 'mansao_tv.ydr'=3 }
$lightingResults = foreach ($lightingPath in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'package/stream') -Filter *.ydr) {
    $lightingFile = New-Object CodeWalker.GameFiles.YdrFile
    $lightingFile.Load([IO.File]::ReadAllBytes($lightingPath.FullName))
    if ($null -eq $lightingFile.Drawable) { throw "Missing drawable $($lightingPath.Name)" }
    $lightingCount = $lightingFile.Drawable.LightAttributes.EntriesCount
    if ($lightingCount -ne $expected[$lightingPath.Name]) { throw "Wrong light count $($lightingPath.Name)" }
    [pscustomobject]@{ model=$lightingPath.Name; lights=$lightingCount; nativeLoaded=$true; shaders=$lightingFile.Drawable.ShaderGroup.ShadersCount; systemBytes=$lightingFile.RpfFileEntry.SystemSize; graphicsBytes=$lightingFile.RpfFileEntry.GraphicsSize }
}
if ($lightingResults.Count -ne 4) { throw 'Missing staged models' }
$lightingResults | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'codewalker_verification.json') -Encoding utf8
$lightingResults | Format-Table
