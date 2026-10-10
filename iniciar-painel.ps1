param([switch]$SemAbrir)
$ErrorActionPreference = 'Stop'
$cidadePython = 'C:\Python313\python.exe'
$cidadeApp = Join-Path $PSScriptRoot 'painel_acesso\app.py'
$cidadeLog = Join-Path $PSScriptRoot 'painel_acesso\data\painel.log'
$cidadeErro = Join-Path $PSScriptRoot 'painel_acesso\data\painel-error.log'
if (-not (Test-Path -LiteralPath $cidadePython)) { throw 'Python nao encontrado em C:\Python313\python.exe.' }
$cidadeAtivo = $false
try { $cidadeResposta = Invoke-RestMethod 'http://127.0.0.1:8787/health' -TimeoutSec 2; $cidadeAtivo = $cidadeResposta.app -eq 'cidade_acesso' } catch {}
if (-not $cidadeAtivo) {
    New-Item -ItemType Directory -Path (Split-Path $cidadeLog) -Force | Out-Null
    $cidadeProcesso = Start-Process -FilePath $cidadePython -ArgumentList @('-u', ('"' + $cidadeApp + '"')) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput $cidadeLog -RedirectStandardError $cidadeErro -PassThru
    for ($cidadeTentativa = 0; $cidadeTentativa -lt 30; $cidadeTentativa++) {
        Start-Sleep -Milliseconds 200
        try { $cidadeResposta = Invoke-RestMethod 'http://127.0.0.1:8787/health' -TimeoutSec 1; if ($cidadeResposta.app -eq 'cidade_acesso') { $cidadeAtivo = $true; break } } catch {}
        if ($cidadeProcesso.HasExited) { break }
    }
}
if (-not $cidadeAtivo) { throw "Nao foi possivel iniciar o painel na porta 8787. Consulte $cidadeErro" }
if (-not $SemAbrir) { & $cidadePython $cidadeApp --open }
Write-Host 'Painel de acesso pronto: http://127.0.0.1:8787' -ForegroundColor Green
