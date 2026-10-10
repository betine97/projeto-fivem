$ErrorActionPreference='Stop'
$taskCaptureScript=Join-Path $PSScriptRoot 'captura_los_santos\service.py'
try {
    $taskHealth=Invoke-RestMethod 'http://127.0.0.1:8788/health' -TimeoutSec 2
    if ($taskHealth.app -eq 'captura_los_santos' -and $taskHealth.ok) {
        Write-Host 'Captura de objetos pronta em Los Santos e Cayo Perico.' -ForegroundColor Green
        return
    }
} catch {}
$taskCaptureProcess=Start-Process -FilePath 'C:\Python313\python.exe' -ArgumentList @('-u',('"'+$taskCaptureScript+'"')) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'captura_los_santos\service.log') -RedirectStandardError (Join-Path $PSScriptRoot 'captura_los_santos\service-error.log') -PassThru
for ($taskAttempt=0;$taskAttempt -lt 40;$taskAttempt++) {
    Start-Sleep -Milliseconds 200
    try {
        $taskHealth=Invoke-RestMethod 'http://127.0.0.1:8788/health' -TimeoutSec 1
        if ($taskHealth.app -eq 'captura_los_santos' -and $taskHealth.ok) { Write-Host 'Captura pronta. F8: capturarobjeto' -ForegroundColor Green;return }
    } catch {}
    if ($taskCaptureProcess.HasExited) { break }
}
throw 'Falha ao iniciar a captura. Consulte captura_los_santos/service-error.log.'
