@echo off
setlocal
where pwsh >nul 2>nul || (echo PowerShell 7 is required & exit /b 1)
pwsh -NoProfile -File "%~dp0backup.ps1" -Account %1
