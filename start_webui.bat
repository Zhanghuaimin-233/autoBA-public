@echo off
setlocal EnableExtensions
rem chdir to this bat's folder (safe on double-click or any cwd)
rem Keep this file pure ASCII with CRLF line endings: cmd parses .bat in the OEM
rem codepage, so UTF-8 Chinese comments break line parsing ("'?cd' is not recognized")
cd /d "%~dp0"
rem local machine config (unidbg work dir / so path); gitignored, optional
if exist "env.local.bat" call "env.local.bat"

set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" goto :bootstrap
"%PY%" -c "import sys; raise SystemExit(0 if sys.version_info[:2]==(3,12) else 1)" >nul 2>nul
if errorlevel 1 goto :bootstrap
"%PY%" -c "import fastapi, uvicorn, requests, Crypto" >nul 2>nul
if errorlevel 1 goto :bootstrap
goto :run

:bootstrap
echo [setup] preparing Python 3.12 environment ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\bootstrap.ps1"
if errorlevel 1 goto :fail
if not exist "%PY%" goto :fail
goto :run

:run
rem port: AUTOBA_PORT if set (env.local.bat or shell), default 8800
if not defined AUTOBA_PORT set "AUTOBA_PORT=8800"
"%PY%" -m uvicorn webui.server:app --host 127.0.0.1 --port %AUTOBA_PORT%
pause
exit /b 0

:fail
echo [error] setup failed; see messages above.
pause
exit /b 1
