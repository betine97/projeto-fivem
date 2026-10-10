$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$taskOut=Join-Path $taskRoot 'teste-ilha/cayo_perico'
Add-Type -Path "$taskRoot/.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll"
Add-Type -Path "$taskRoot/.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll"
Add-Type -Path "$taskRoot/.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll"
$taskSelected=Get-Content "$taskOut/mapas_selecionados.json" -Raw | ConvertFrom-Json
$taskSelection=@{};foreach($taskName in $taskSelected){$taskSelection[[IO.Path]::GetFileNameWithoutExtension($taskName)]=$true}
# Register installed filenames before resolving PSO hashes, including unknown source map hashes.
foreach($taskFile in Get-ChildItem "$taskOut/originais/mapas","$taskOut/originais/assets","$taskOut/originais/colisoes" -File){[void][CodeWalker.GameFiles.JenkIndex]::Ensure($taskFile.BaseName.ToLowerInvariant())}
$taskXml=[Xml.XmlDocument]::new()
$taskXml.LoadXml('<CPackFileMetaData><MapDataGroups itemType="CMapDataGroup"/><HDTxdBindingArray itemType="CHDTxdAssetBinding"/><imapDependencies itemType="CImapDependency"/><imapDependencies_2 itemType="CImapDependencies"/><itypDependencies_2 itemType="CItypDependencies"/><Interiors itemType="CInteriorBoundsFiles"/></CPackFileMetaData>')
$taskSeen=@{}
foreach($taskFile in Get-ChildItem "$taskOut/originais/manifestos/*.ymf"){
    $taskYmf=[CodeWalker.GameFiles.YmfFile]::new();$taskYmf.Load([IO.File]::ReadAllBytes($taskFile.FullName),$null)
    $taskText=[CodeWalker.GameFiles.MetaXml]::GetXml($taskYmf,[ref]([string]$taskXmlName=''))
    $taskDoc=[Xml.XmlDocument]::new();$taskDoc.LoadXml($taskText)
    foreach($taskSection in $taskDoc.DocumentElement.ChildNodes){
        $taskDest=$taskXml.DocumentElement.SelectSingleNode($taskSection.Name)
        if($null -eq $taskDest){throw ('Unknown manifest section: '+$taskSection.Name)}
        foreach($taskItem in $taskSection.SelectNodes('Item')){
            $taskCopy=$taskXml.ImportNode($taskItem,$true)
            $taskMapNode=if($taskSection.Name -eq 'MapDataGroups'){$taskCopy.SelectSingleNode('Name')}elseif($taskSection.Name -like 'imapDependencies*'){$taskCopy.SelectSingleNode('imapName')}else{$null}
            if($taskMapNode){
                $taskMapName=$taskMapNode.InnerText.ToLowerInvariant()
                if(-not $taskSelection.ContainsKey($taskMapName)){continue}
                $taskMapNode.InnerText='cv_'+$taskMapName
            }
            # Dependency records are shared across source archives; deduplicate identical entries.
            $taskKey=$taskSection.Name+'|'+$taskCopy.OuterXml
            if(-not $taskSeen.ContainsKey($taskKey)){
                [void]$taskDest.AppendChild($taskCopy);$taskSeen[$taskKey]=$true
            }
        }
    }
}
$taskXml.Save("$taskOut/manifesto.xml")
$taskPso=[CodeWalker.GameFiles.XmlPso]::GetPso($taskXml)
[IO.File]::WriteAllBytes("$taskOut/fivem/stream/_manifest.ymf",$taskPso.Save())
$taskRead=[CodeWalker.GameFiles.YmfFile]::new();$taskRead.Load([IO.File]::ReadAllBytes("$taskOut/fivem/stream/_manifest.ymf"),$null)
if(-not $taskRead.Pso){throw 'Manifest invalid'}
Write-Host ('MANIFESTO_VALIDADO records='+$taskSeen.Count)
