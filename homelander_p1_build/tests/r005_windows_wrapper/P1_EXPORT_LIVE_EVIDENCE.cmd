@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0P1_EXPORT_LIVE_EVIDENCE.ps1" -Action Export %*
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" echo Evidence export failed with exit code %RC%.
pause
exit /b %RC%
