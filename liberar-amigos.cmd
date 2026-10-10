@echo off
title Minha Cidade - Liberar amigos
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0liberar-amigos.ps1"
if errorlevel 1 echo Falha ao liberar. Confira a mensagem acima e liberar-amigos.log.
echo.
echo Seu PC: connect 127.0.0.1:30120
echo Amigos no Radmin VPN: connect 26.30.45.250:30120
echo.
pause
