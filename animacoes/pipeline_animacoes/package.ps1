param([switch]$Install)
$ErrorActionPreference='Stop'
$pipelineExports=Join-Path $PSScriptRoot 'exports'
$converter=Join-Path $PSScriptRoot '../work/convert-ycd.ps1'
$runtime=Join-Path $PSScriptRoot '../../server-data/resources/cidade_core'
$report=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'reports/build.json') -Raw | ConvertFrom-Json
foreach ($entry in $report.clips.PSObject.Properties) {
    $xml=Join-Path $pipelineExports ($entry.Name+'.ycd.xml')
    $binary=Join-Path $pipelineExports ($entry.Name+'.ycd')
    $roundtrip=Join-Path $pipelineExports ($entry.Name+'.roundtrip.xml')
    & $converter -InputPath $xml -OutputPath $binary
    & $converter -InputPath $binary -OutputPath $roundtrip -ToXml
    [xml]$original=Get-Content -LiteralPath $xml -Raw
    [xml]$verified=Get-Content -LiteralPath $roundtrip -Raw
    if ($verified.ClipDictionary.Clips.Item.Count -ne $original.ClipDictionary.Clips.Item.Count) { throw "Clip count changed: $($entry.Name)" }
    if ($verified.ClipDictionary.Animations.Item.Count -ne $original.ClipDictionary.Animations.Item.Count) { throw "Animation count changed: $($entry.Name)" }
    $entry.Value.binary_roundtrip=$true
    if ($Install) { Copy-Item -LiteralPath $binary -Destination (Join-Path $runtime 'stream') }
}
if ($Install) {
    Copy-Item -LiteralPath (Join-Path $pipelineExports 'combat_mounts.lua') -Destination $runtime
}
$report | Add-Member -NotePropertyName installed_on_disk -NotePropertyValue ([bool]$Install) -Force
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'reports/build.json') -Encoding utf8
Write-Output 'V5 packaged, read back and checked. No running resource or server was restarted.'
