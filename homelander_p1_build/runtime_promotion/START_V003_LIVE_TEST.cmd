@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0START_V003_LIVE_TEST.ps1"
set RC=%ERRORLEVEL%
echo.
if "%RC%"=="0" (
  echo Observer finished with complete log evidence. No authoritative PASS was recorded.
) else (
  echo Live test did not complete cleanly. Exit code: %RC%
)
echo.
pause
exit /b %RC%
