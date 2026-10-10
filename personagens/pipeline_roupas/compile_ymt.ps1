param(
    [Parameter(Mandatory=$true)][string]$SourceXml,
    [Parameter(Mandatory=$true)][string]$OutputYmt,
    [Parameter(Mandatory=$true)][string]$RoundTripXml
)
$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
foreach ($library in @(
    '.downloads/codewalker/sharpdx/lib/net45/SharpDX.dll',
    '.downloads/codewalker/sharpdx.mathematics/lib/net45/SharpDX.Mathematics.dll',
    '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll'
)) {
    [void][Reflection.Assembly]::LoadFrom((Join-Path $workspace $library))
}
$document = [Xml.XmlDocument]::new()
$document.Load([IO.Path]::GetFullPath($SourceXml))
$bytes = [CodeWalker.GameFiles.XmlMeta]::GetRSCData($document)
if (-not $bytes -or $bytes.Length -lt 16) { throw 'Compilação YMT vazia.' }
[IO.File]::WriteAllBytes([IO.Path]::GetFullPath($OutputYmt), $bytes)
$loaded = [CodeWalker.GameFiles.YmtFile]::new()
$loaded.Load([IO.File]::ReadAllBytes([IO.Path]::GetFullPath($OutputYmt)))
$name = ''
$roundTrip = [CodeWalker.GameFiles.MetaXml]::GetXml($loaded, [ref]$name)
if (-not $roundTrip.Contains('CPedVariationInfo')) { throw 'YMT não reabriu como roupa.' }
[IO.File]::WriteAllText([IO.Path]::GetFullPath($RoundTripXml), $roundTrip, [Text.UTF8Encoding]::new($false))
Write-Output ('YMT compilado e reaberto: ' + $bytes.Length + ' bytes')
