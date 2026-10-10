$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$taskOut=Join-Path $taskRoot 'teste-ilha/identidade_cayo_total'
$taskRefs=@("$taskRoot/.downloads/codewalker/sharpdx/lib/netstandard1.1/SharpDX.dll","$taskRoot/.downloads/codewalker/sharpdx.mathematics/lib/netstandard1.1/SharpDX.Mathematics.dll","$taskRoot/.downloads/codewalker/core/lib/netstandard2.0/CodeWalker.Core.dll")
foreach($taskRef in $taskRefs){Add-Type -Path $taskRef}
$taskRefs+=@(Get-ChildItem -LiteralPath "$PSHOME/ref" -Filter '*.dll' | ForEach-Object {$_.FullName})
Add-Type -ReferencedAssemblies $taskRefs -CompilerOptions '/nowarn:1701' -TypeDefinition @'
using System;
using System.IO;
using CodeWalker.GameFiles;
using SharpDX;
public static class IslandCollisionAudit {
 public static int CheckSamples(string folder,string csv) {
  var loaded=new System.Collections.Generic.Dictionary<string,YbnFile>();int count=0;
  foreach(var line in File.ReadAllLines(csv)) {
   var v=line.Split(',');if(v[0]=="tile")continue;
   YbnFile file;if(!loaded.TryGetValue(v[0],out file)){file=new YbnFile();file.Load(File.ReadAllBytes(Path.Combine(folder,v[0]+".ybn")));loaded[v[0]]=file;}
   var culture=System.Globalization.CultureInfo.InvariantCulture;
   float x=float.Parse(v[1],culture),y=float.Parse(v[2],culture),expected=float.Parse(v[3],culture);
   var ray=new Ray(new Vector3(x,y,1000),-Vector3.UnitZ);var hit=file.Bounds.RayIntersect(ref ray,1500);
   if(!hit.Hit || Math.Abs(1000-hit.HitDist-expected)>.035f)throw new Exception("Collision does not match visible terrain: "+line+" actual="+(1000-hit.HitDist));
   count++;
  }
  return count;
 }
 public static int Check(string before,string after) {
  int rays=0;
  foreach(var path in Directory.GetFiles(after,"ti_terreno_*.ybn")) {
   var a=new YbnFile();a.Load(File.ReadAllBytes(Path.Combine(before,Path.GetFileName(path))));
   var b=new YbnFile();b.Load(File.ReadAllBytes(path));
   var lo=a.Bounds.BoxMin;var hi=a.Bounds.BoxMax;
   foreach(float u in new[]{.15f,.5f,.85f}) foreach(float v in new[]{.15f,.5f,.85f}) {
    var p=new Vector3(lo.X+(hi.X-lo.X)*u,lo.Y+(hi.Y-lo.Y)*v,1000);
    var ra=new Ray(p,-Vector3.UnitZ);var rb=new Ray(p,-Vector3.UnitZ);
    var ha=a.Bounds.RayIntersect(ref ra,1500);var hb=b.Bounds.RayIntersect(ref rb,1500);
    if(!hb.Hit) throw new Exception("Missing regraded collision "+path+" at "+p);
    if(hb.HitDist<900 || hb.HitDist>1250) throw new Exception("Collision outside height bounds "+path);
    if(ha.Hit)rays++;
   }
  }
  return rays;
 }
}
'@
$taskXml=[Xml.XmlDocument]::new()
$taskXml.LoadXml('<CPackFileMetaData><MapDataGroups itemType="CMapDataGroup"/><HDTxdBindingArray itemType="CHDTxdAssetBinding"/><imapDependencies itemType="CImapDependency"/><imapDependencies_2 itemType="CImapDependencies"/><itypDependencies_2 itemType="CItypDependencies"/><Interiors itemType="CInteriorBoundsFiles"/></CPackFileMetaData>')
$taskPlanting=Get-Content "$taskOut/dados/implantacao.json" -Raw | ConvertFrom-Json
foreach($taskMap in Get-ChildItem "$taskOut/stream/ni_*.ymap") {
 $taskGroup=$taskXml.CreateElement('Item');$taskGroup.InnerXml='<Name>'+$taskMap.BaseName+'</Name><Bounds/><Flags/><WeatherTypes/><HoursOnOff value="0"/>'
 $taskMeta=$taskPlanting.maps | Where-Object {$_.name -eq $taskMap.BaseName}
 foreach($taskPhysics in $taskMeta.physics){$taskBound=$taskXml.CreateElement('Item');$taskBound.InnerText=$taskPhysics;[void]$taskGroup.SelectSingleNode('Bounds').AppendChild($taskBound)}
 [void]$taskXml.DocumentElement.SelectSingleNode('MapDataGroups').AppendChild($taskGroup)
 $taskDep=$taskXml.CreateElement('Item');$taskParent=if($taskMeta.parent){'<imapDepArray><Item>'+$taskMeta.parent+'</Item></imapDepArray>'}else{''}
 $taskDep.InnerXml='<imapName>'+$taskMap.BaseName+'</imapName><manifestFlags/>'+$taskParent+'<itypDepArray><Item>natureza_integrada</Item><Item>ni_groundcover</Item><Item>h4_mph4_island</Item><Item>porto_esperanca</Item></itypDepArray>'
 [void]$taskXml.DocumentElement.SelectSingleNode('imapDependencies_2').AppendChild($taskDep)
}
$taskXml.Save("$taskOut/dados/manifesto.xml")
$taskPso=[CodeWalker.GameFiles.XmlPso]::GetPso($taskXml)
[IO.File]::WriteAllBytes("$taskOut/stream/_manifest.ymf",$taskPso.Save())
$taskResults=@()
foreach($taskDir in @('stream','terreno','porto_filtrado')) {
 foreach($taskFile in Get-ChildItem "$taskOut/$taskDir" -File) {
  $taskReader=switch($taskFile.Extension){'.ydr'{'YdrFile'} '.ybn'{'YbnFile'} '.ymap'{'YmapFile'} '.ytyp'{'YtypFile'} '.ytd'{'YtdFile'} '.ymf'{'YmfFile'} default{throw 'Unexpected asset'}}
  $taskAsset=New-Object ('CodeWalker.GameFiles.'+$taskReader)
  if($taskReader -eq 'YmfFile'){$taskAsset.Load([IO.File]::ReadAllBytes($taskFile.FullName),$null)}else{$taskAsset.Load([IO.File]::ReadAllBytes($taskFile.FullName))}
  if($taskReader -eq 'YdrFile' -and -not $taskAsset.Drawable){throw ('Invalid drawable '+$taskFile.Name)}
  if($taskReader -eq 'YbnFile' -and -not $taskAsset.Bounds){throw ('Invalid collision '+$taskFile.Name)}
  if($taskReader -eq 'YmapFile' -and -not $taskAsset.CMapData){throw ('Invalid map '+$taskFile.Name)}
  $taskResults+=@{file=$taskDir+'/'+$taskFile.Name;bytes=$taskFile.Length}
 }
}
$taskRays=[IslandCollisionAudit]::CheckSamples("$taskOut/terreno","$taskOut/dados/ground_samples.csv")
@{passed=$true;collision_rays=$taskRays;assets=$taskResults;in_game_verified=$false} | ConvertTo-Json -Depth 6 | Set-Content "$taskOut/dados/validacao_codewalker.json" -Encoding utf8
Write-Output ('NATIVE_VALIDATED assets='+$taskResults.Count+' ground_rays='+$taskRays)
