$ErrorActionPreference = 'Stop'
$taskOut = Split-Path $PSScriptRoot
$taskRoot = Split-Path (Split-Path $taskOut)
$taskStaging = Join-Path $taskOut 'qualidade_terreno/stream'
$taskData = Join-Path $taskOut 'qualidade_terreno/dados'
$taskActive = Join-Path $taskRoot 'server-data/resources/teste_ilha/stream'
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll')
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll')
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll')

# Include every existing map and the newly completed eastern beach, without
# adding copies of the other 45 maps to this staging directory.
$taskMaps = @{}
foreach ($taskMap in Get-ChildItem -LiteralPath $taskActive -Filter '*.ymap' -File) { $taskMaps[$taskMap.BaseName] = $taskMap.FullName }
foreach ($taskMap in Get-ChildItem -LiteralPath $taskStaging -Filter '*.ymap' -File) { $taskMaps[$taskMap.BaseName] = $taskMap.FullName }
$taskXml = New-Object Xml.XmlDocument
$taskXml.LoadXml('<CPackFileMetaData><MapDataGroups itemType="CMapDataGroup"/><HDTxdBindingArray itemType="CHDTxdAssetBinding"/><imapDependencies itemType="CImapDependency"/><imapDependencies_2 itemType="CImapDependencies"/><itypDependencies_2 itemType="CItypDependencies"/><Interiors itemType="CInteriorBoundsFiles"/></CPackFileMetaData>')
foreach ($taskName in $taskMaps.Keys | Sort-Object) {
    $taskPhysicsName = $taskName -replace '_map$', ''
    $taskHasPhysics = (Test-Path -LiteralPath (Join-Path $taskActive ($taskPhysicsName + '.ybn'))) -or (Test-Path -LiteralPath (Join-Path $taskStaging ($taskPhysicsName + '.ybn')))
    $taskBounds = if ($taskHasPhysics) { '<Item>' + $taskPhysicsName + '</Item>' } else { '' }
    $taskGroup = $taskXml.CreateElement('Item')
    $taskGroup.InnerXml = '<Name>' + $taskName + '</Name><Bounds>' + $taskBounds + '</Bounds><Flags/><WeatherTypes/><HoursOnOff value="0"/>'
    [void]$taskXml.DocumentElement.SelectSingleNode('MapDataGroups').AppendChild($taskGroup)
    $taskType = if ($taskName -eq 'ti_amostra_natural') { 'ti_nature' } else { 'teste_ilha' }
    $taskDep = $taskXml.CreateElement('Item')
    $taskDep.InnerXml = '<imapName>' + $taskName + '</imapName><manifestFlags/><itypDepArray><Item>' + $taskType + '</Item></itypDepArray>'
    [void]$taskXml.DocumentElement.SelectSingleNode('imapDependencies_2').AppendChild($taskDep)
}
$taskXml.Save((Join-Path $taskData 'manifesto_terreno.xml'))
$taskPso = [CodeWalker.GameFiles.XmlPso]::GetPso($taskXml)
$taskManifest = Join-Path $taskStaging '_manifest.ymf'
[IO.File]::WriteAllBytes($taskManifest, $taskPso.Save())
$taskReader = New-Object CodeWalker.GameFiles.YmfFile
$taskReader.Load([IO.File]::ReadAllBytes($taskManifest), $null)
if ($taskReader.imapDependencies2.Count -ne $taskMaps.Count -or $taskReader.MapDataGroups.Count -ne $taskMaps.Count) { throw 'Incomplete island manifest' }

$taskResults = @()
foreach ($taskFile in Get-ChildItem -LiteralPath $taskStaging -File) {
    $taskType = switch ($taskFile.Extension) { '.ydr' { 'YdrFile' } '.ybn' { 'YbnFile' } '.ymap' { 'YmapFile' } '.ytyp' { 'YtypFile' } '.ytd' { 'YtdFile' } '.ymf' { 'YmfFile' } default { throw 'Unexpected asset type' } }
    $taskAsset = New-Object ('CodeWalker.GameFiles.' + $taskType)
    if ($taskType -eq 'YmfFile') { $taskAsset.Load([IO.File]::ReadAllBytes($taskFile.FullName), $null) } else { $taskAsset.Load([IO.File]::ReadAllBytes($taskFile.FullName)) }
    if ($taskType -eq 'YdrFile' -and $null -eq $taskAsset.Drawable) { throw ('Invalid drawable: ' + $taskFile.Name) }
    if ($taskType -eq 'YbnFile' -and $null -eq $taskAsset.Bounds) { throw ('Invalid collision: ' + $taskFile.Name) }
    $taskResults += @{ file = $taskFile.Name; bytes = $taskFile.Length; reader = $taskType }
}
@{ passed = $true; assets = $taskResults; manifest_maps = $taskMaps.Count; in_game_verified = $false } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskData 'validacao_codewalker.json') -Encoding utf8
Write-Output ('TERRAIN_QUALITY_CODEWALKER_VALIDATED ' + $taskResults.Count + ' assets; ' + $taskMaps.Count + ' maps')
