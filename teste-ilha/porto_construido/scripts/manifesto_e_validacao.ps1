$ErrorActionPreference='Stop'
$taskOut=Split-Path $PSScriptRoot
$taskRoot=Split-Path (Split-Path $taskOut)
$taskStream=Join-Path $taskOut 'fivem/stream'
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll')
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll')
Add-Type -Path (Join-Path $taskRoot '.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll')
$taskXml=New-Object Xml.XmlDocument
$taskXml.LoadXml('<CPackFileMetaData><MapDataGroups itemType="CMapDataGroup"/><HDTxdBindingArray itemType="CHDTxdAssetBinding"/><imapDependencies itemType="CImapDependency"/><imapDependencies_2 itemType="CImapDependencies"/><itypDependencies_2 itemType="CItypDependencies"/><Interiors itemType="CInteriorBoundsFiles"/></CPackFileMetaData>')
foreach($taskMap in Get-ChildItem -LiteralPath $taskStream -Filter 'pe_bairro_*.ymap' -File){
    $taskName=$taskMap.BaseName
    $taskGroup=$taskXml.CreateElement('Item');$taskGroup.InnerXml='<Name>'+$taskName+'</Name><Bounds/><Flags/><WeatherTypes/><HoursOnOff value="0"/>'
    [void]$taskXml.DocumentElement.SelectSingleNode('MapDataGroups').AppendChild($taskGroup)
    $taskDep=$taskXml.CreateElement('Item');$taskDep.InnerXml='<imapName>'+$taskName+'</imapName><manifestFlags/><itypDepArray><Item>porto_esperanca</Item><Item>ti_nature</Item></itypDepArray>'
    [void]$taskXml.DocumentElement.SelectSingleNode('imapDependencies_2').AppendChild($taskDep)
}
$taskXml.Save((Join-Path $taskOut 'dados/manifesto.xml'))
$taskPso=[CodeWalker.GameFiles.XmlPso]::GetPso($taskXml)
[IO.File]::WriteAllBytes((Join-Path $taskStream '_manifest.ymf'),$taskPso.Save())
$taskResults=@()
foreach($taskFile in Get-ChildItem -LiteralPath $taskStream -File){
    $taskReader=switch($taskFile.Extension){'.ydr'{'YdrFile'} '.ybn'{'YbnFile'} '.ymap'{'YmapFile'} '.ytyp'{'YtypFile'} '.ytd'{'YtdFile'} '.ymf'{'YmfFile'} default{throw 'Tipo inesperado'}}
    $taskAsset=New-Object ('CodeWalker.GameFiles.'+$taskReader)
    if($taskReader -eq 'YmfFile'){$taskAsset.Load([IO.File]::ReadAllBytes($taskFile.FullName),$null)}else{$taskAsset.Load([IO.File]::ReadAllBytes($taskFile.FullName))}
    if($taskReader -eq 'YdrFile' -and $null -eq $taskAsset.Drawable){throw ('Drawable invalido '+$taskFile.Name)}
    if($taskReader -eq 'YbnFile' -and $null -eq $taskAsset.Bounds){throw ('Colisao invalida '+$taskFile.Name)}
    $taskResults+=@{file=$taskFile.Name;bytes=$taskFile.Length;reader=$taskReader}
}
@{passed=$true;assets=$taskResults;in_game_verified=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskOut 'dados/validacao_codewalker.json') -Encoding utf8
Write-Output ('PORTO_NATIVE_VALIDATED '+$taskResults.Count)
