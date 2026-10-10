$ErrorActionPreference = 'Stop'
$lightingRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Add-Type -Path (Join-Path $lightingRoot '.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll')
Add-Type -Path (Join-Path $lightingRoot '.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll')
Add-Type -Path (Join-Path $lightingRoot '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll')
$lightingResults = @()
foreach ($lightingName in @('mansao_teto','mansao_pendentes','mansao_spot_embutido')) {
    $lightingFile = New-Object CodeWalker.GameFiles.YdrFile
    $lightingFile.Load([IO.File]::ReadAllBytes((Join-Path $PSScriptRoot "package/stream/$lightingName.ydr")))
    if ($null -eq $lightingFile.Drawable) { throw "Missing drawable $lightingName" }
    $lightingResults += [pscustomobject]@{
        model = $lightingName
        lights = $lightingFile.Drawable.LightAttributes.EntriesCount
        geometryModels = @($lightingFile.Drawable.AllModels).Count
        nativeLoaded = $true
    }
}
$lightingResults | Format-Table
if ($lightingResults[0].lights -ne 107 -or $lightingResults[1].lights -ne 9 -or $lightingResults[2].lights -ne 0) { throw 'Independent light count mismatch' }
$lightingResults | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'codewalker_verification.json') -Encoding utf8
