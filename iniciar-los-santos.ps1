$ErrorActionPreference='Stop'
$taskServerExe=Join-Path $PSScriptRoot '.runtime\FXServer.exe'
$taskCityData=Join-Path $PSScriptRoot 'servidor-los-santos'
$taskPython='C:\Python313\python.exe'
$taskCapture=Join-Path $PSScriptRoot 'captura_los_santos\service.py'
& (Join-Path $PSScriptRoot 'iniciar-painel.ps1') -SemAbrir
& (Join-Path $PSScriptRoot 'iniciar-captura.ps1')
$taskListener=Get-NetTCPConnection -LocalPort 30121 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($taskListener) {
    $taskInfo=Invoke-RestMethod 'http://127.0.0.1:30121/info.json' -TimeoutSec 3
    if ($taskInfo.resources -notcontains 'cidade_captura') { throw 'A porta 30121 está ocupada por outro serviço.' }
    Write-Host 'Los Santos já está funcionando. F8: connect 127.0.0.1:30121' -ForegroundColor Green
    return
}
Write-Host 'Los Santos original: F8 -> connect 127.0.0.1:30121' -ForegroundColor Green
Write-Host 'A ilha continua em 127.0.0.1:30120. Feche completamente o FiveM ao trocar de mapa.'
Push-Location -LiteralPath $taskCityData
try { & $taskServerExe +set onesync on +exec server.cfg } finally { Pop-Location }
