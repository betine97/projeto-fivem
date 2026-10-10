$ErrorActionPreference = 'Stop'
$castleRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Add-Type -Path (Join-Path $castleRoot '.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll')
Add-Type -Path (Join-Path $castleRoot '.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll')
Add-Type -Path (Join-Path $castleRoot '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll')
$castleResults = foreach ($castlePath in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'package/stream')) {
    $castleType = switch ($castlePath.Extension) { '.ydr' {'YdrFile'} '.ytd' {'YtdFile'} '.ytyp' {'YtypFile'} '.ymap' {'YmapFile'} default {throw 'Unexpected file'} }
    $castleFile = New-Object "CodeWalker.GameFiles.$castleType"
    $castleFile.Load([IO.File]::ReadAllBytes($castlePath.FullName))
    if ($castleType -eq 'YdrFile' -and $null -eq $castleFile.Drawable) { throw "Missing drawable $castlePath" }
    [pscustomobject]@{file=$castlePath.Name;nativeLoaded=$true;bytes=$castlePath.Length;systemBytes=$castleFile.RpfFileEntry.SystemSize;graphicsBytes=$castleFile.RpfFileEntry.GraphicsSize}
}
$castleResults | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'codewalker_verificacao.json') -Encoding utf8
$castleResults | Format-Table
