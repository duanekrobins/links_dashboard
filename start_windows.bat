@echo off
setlocal
cd /d "%~dp0"
set "CONFIG_ARG="
if exist "config.local.json" set "CONFIG_ARG=--config config.local.json"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 app.py %CONFIG_ARG%
) else (
  python app.py %CONFIG_ARG%
)
if errorlevel 1 (
  echo.
  echo The dashboard did not start. Install Python 3.10 or later, then try again.
)
pause
