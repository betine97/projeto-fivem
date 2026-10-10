$ErrorActionPreference = 'Stop'
$catalogDirectory = Join-Path $PSScriptRoot 'dist'
$listener = Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue
if (-not $listener) {
    $pythonExecutable = (Get-Command python).Source
    Start-Process -FilePath $pythonExecutable -ArgumentList @(('"' + (Join-Path $PSScriptRoot 'server.py') + '"')) -WorkingDirectory $catalogDirectory -WindowStyle Hidden
    Start-Sleep -Milliseconds 800
}
Start-Process 'http://127.0.0.1:8766/'
