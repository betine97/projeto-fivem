$ErrorActionPreference='Stop'
$taskProject=Split-Path $PSScriptRoot
$taskWorkspace=Split-Path $taskProject
Add-Type -Path (Join-Path $taskWorkspace '.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll')
Add-Type -Path (Join-Path $taskWorkspace '.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll')
Add-Type -Path (Join-Path $taskWorkspace '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll')
$taskStream=Join-Path $taskProject 'fivem/stream'
$taskXml=New-Object Xml.XmlDocument
$taskXml.LoadXml('<CPackFileMetaData><MapDataGroups itemType="CMapDataGroup"/><HDTxdBindingArray itemType="CHDTxdAssetBinding"/><imapDependencies itemType="CImapDependency"/><imapDependencies_2 itemType="CImapDependencies"/><itypDependencies_2 itemType="CItypDependencies"/><Interiors itemType="CInteriorBoundsFiles"/></CPackFileMetaData>')
foreach($taskFile in Get-ChildItem -LiteralPath $taskStream -Filter '*.ymap' -File) {
    $taskName=$taskFile.BaseName
    $taskPhysicsName=$taskName -replace '_map$',''
    $taskBounds=if(Test-Path -LiteralPath (Join-Path $taskStream ($taskPhysicsName+'.ybn'))) { '<Item>'+$taskPhysicsName+'</Item>' } else { '' }
    $taskGroup=$taskXml.CreateElement('Item')
    $taskGroup.InnerXml='<Name>'+$taskName+'</Name><Bounds>'+$taskBounds+'</Bounds><Flags/><WeatherTypes/><HoursOnOff value="0"/>'
    [void]$taskXml.DocumentElement.SelectSingleNode('MapDataGroups').AppendChild($taskGroup)
    $taskType=if($taskName -eq 'ti_amostra_natural'){'ti_nature'}else{'teste_ilha'}
    $taskDep=$taskXml.CreateElement('Item')
    $taskDep.InnerXml='<imapName>'+$taskName+'</imapName><manifestFlags/><itypDepArray><Item>'+$taskType+'</Item></itypDepArray>'
    [void]$taskXml.DocumentElement.SelectSingleNode('imapDependencies_2').AppendChild($taskDep)
}
$taskXml.Save((Join-Path $taskProject 'amostra_natural/manifesto.xml'))
$taskPso=[CodeWalker.GameFiles.XmlPso]::GetPso($taskXml)
$taskPath=Join-Path $taskStream '_manifest.ymf'
[IO.File]::WriteAllBytes($taskPath,$taskPso.Save())
$taskReader=New-Object CodeWalker.GameFiles.YmfFile
$taskReader.Load([IO.File]::ReadAllBytes($taskPath),$null)
if($taskReader.imapDependencies2.Count -ne 45 -or $taskReader.MapDataGroups.Count -ne 45){throw 'Manifesto incompleto'}
Write-Output ('ISLAND_MANIFEST_READY '+$taskReader.imapDependencies2.Count)
