param([string]$InputPath,[string]$OutputPath,[switch]$ToXml)
$ErrorActionPreference='Stop'
$toolsRoot=Join-Path $PSScriptRoot '../../.downloads/codewalker'
Add-Type -Path "$toolsRoot/sharpdx/lib/netstandard1.1/SharpDX.dll"
Add-Type -Path "$toolsRoot/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll"
Add-Type -Path "$toolsRoot/core/lib/netstandard2.0/CodeWalker.Core.dll"
if ($ToXml) {
 $asset=[CodeWalker.GameFiles.RpfFile]::GetResourceFile[CodeWalker.GameFiles.YcdFile]([IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $InputPath)))
 [IO.File]::WriteAllText($OutputPath,[CodeWalker.GameFiles.YcdXml]::GetXml($asset))
} else {
 $asset=[CodeWalker.GameFiles.XmlYcd]::GetYcd([IO.File]::ReadAllText((Resolve-Path -LiteralPath $InputPath)))
 [IO.File]::WriteAllBytes($OutputPath,$asset.Save())
 $verified=[CodeWalker.GameFiles.RpfFile]::GetResourceFile[CodeWalker.GameFiles.YcdFile]([IO.File]::ReadAllBytes($OutputPath))
 if (-not $verified.ClipDictionary) { throw 'Binary read-back failed' }
 Write-Output "YCD gravado e relido: $OutputPath"
}

