param([switch]$Elevado)
$ErrorActionPreference = 'Stop'
$cidadeLog = Join-Path $PSScriptRoot 'liberar-amigos.log'
$cidadeAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $cidadeAdmin) {
    if ($Elevado) { throw 'O Windows nao concedeu permissao de administrador.' }
    Write-Host 'Confirme a solicitacao do Windows para liberar TCP/UDP 30120.' -ForegroundColor Yellow
    try {
        $cidadeProcesso = Start-Process -FilePath 'powershell.exe' -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "{0}" -Elevado' -f $PSCommandPath) -Verb RunAs -WindowStyle Hidden -Wait -PassThru
        if (Test-Path -LiteralPath $cidadeLog) { Get-Content -LiteralPath $cidadeLog | Write-Host }
        exit $cidadeProcesso.ExitCode
    } catch {
        Write-Host ('Nao foi possivel liberar: ' + $_.Exception.Message) -ForegroundColor Red
        exit 1
    }
}
try {
$cidadeExe = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '.runtime\FXServer.exe')).Path
foreach ($cidadeProtocolo in @('TCP', 'UDP')) {
    $cidadeNome = "MinhaCidade-FiveM-30120-$cidadeProtocolo"
    if (-not (Get-NetFirewallRule -Name $cidadeNome -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -Name $cidadeNome -DisplayName "Minha Cidade FiveM 30120 $cidadeProtocolo" -Direction Inbound -Action Allow -Protocol $cidadeProtocolo -LocalPort 30120 -Program $cidadeExe -Profile Any | Out-Null
    } else {
        Set-NetFirewallRule -Name $cidadeNome -Enabled True -Direction Inbound -Action Allow -Profile Any | Out-Null
    }
}
$cidadeResultado = 'SUCESSO: porta 30120 TCP/UDP liberada para o FXServer. Painel continua privado neste PC.'
$cidadeResultado | Set-Content -LiteralPath $cidadeLog -Encoding UTF8
Write-Host $cidadeResultado -ForegroundColor Green
} catch {
    $cidadeResultado = 'ERRO: ' + $_.Exception.Message
    $cidadeResultado | Set-Content -LiteralPath $cidadeLog -Encoding UTF8
    Write-Host $cidadeResultado -ForegroundColor Red
    exit 1
}
