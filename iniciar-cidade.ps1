param([ValidateSet('ilha','cidade')][string]$Modo='ilha')
$ErrorActionPreference = 'Stop'
$dataPath = Join-Path $PSScriptRoot 'server-data'
$serverExe = Join-Path $PSScriptRoot '.runtime\FXServer.exe'
$secretPath = Join-Path $dataPath 'secrets.cfg'
& (Join-Path $PSScriptRoot 'iniciar-painel.ps1') -SemAbrir
& (Join-Path $PSScriptRoot 'iniciar-captura.ps1')
$taskListener = Get-NetTCPConnection -LocalPort 30120 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($taskListener) {
    $taskExisting = $null
    try { $taskExisting = Invoke-RestMethod 'http://127.0.0.1:30120/info.json' -TimeoutSec 3 } catch { }
    $taskProcess = Get-Process -Id $taskListener.OwningProcess -ErrorAction SilentlyContinue
    if ($taskExisting -and $taskProcess.Path -eq $serverExe) {
        $taskActiveMode = if ($taskExisting.resources -contains 'teste_ilha') { 'ilha' } else { 'cidade' }
        Write-Host ('O servidor ja esta rodando. Modo: '+$taskActiveMode) -ForegroundColor Green
        Write-Host 'No FiveM, abra F8 e digite: connect 127.0.0.1:30120'
        if ($taskActiveMode -ne $Modo) {
            Write-Host 'Feche o servidor atual antes de trocar de modo.' -ForegroundColor Yellow
            exit 1
        }
        return
    }
    Write-Host 'A porta 30120 ja esta ocupada. Nao foi aberta uma segunda copia.' -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path -LiteralPath $serverExe)) { throw 'FXServer nao encontrado em .runtime.' }
if (-not (Test-Path -LiteralPath $secretPath)) {
    Copy-Item -LiteralPath (Join-Path $dataPath 'secrets.example.cfg') -Destination $secretPath
}
$secret = Get-Content -LiteralPath $secretPath -Raw
if ($secret -notmatch '(?m)^\s*sv_licenseKey\s+(?:"cfxk_[^"\s]+"|cfxk_[A-Za-z0-9_+/=-]+)\s*(?:#.*)?$') {
    Write-Host 'Falta cadastrar a chave do servidor.' -ForegroundColor Yellow
    Write-Host 'Crie uma chave em https://portal.cfx.re e preencha server-data\secrets.cfg.'
    exit 1
}
Write-Host 'No FiveM, abra F8 e digite: connect 127.0.0.1:30120' -ForegroundColor Green
Push-Location -LiteralPath $dataPath
$taskConfig = if ($Modo -eq 'cidade') { 'server-cidade.cfg' } else { 'server.cfg' }
Write-Host ('Modo: '+$Modo) -ForegroundColor Cyan
Write-Host 'Ao trocar entre cidade e ilha, feche completamente o FiveM e abra novamente.' -ForegroundColor Yellow
try { & $serverExe +exec $taskConfig } finally { Pop-Location }
