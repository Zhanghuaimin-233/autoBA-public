@echo off
rem chdir to this bat's folder (safe on double-click or any cwd)
rem Keep this file pure ASCII with CRLF line endings: cmd parses .bat in the OEM
rem codepage, so UTF-8 Chinese comments break line parsing ("'?cd' is not recognized")
cd /d %~dp0
rem local machine config (unidbg work dir / so path); gitignored, optional
if exist "env.local.bat" call "env.local.bat"

rem Run straight from the project venv. Do NOT use "uv run --with": without a
rem pyproject.toml those packages land in a throwaway overlay env, so every
rem launch re-resolves and reinstalls them (the "Installed N packages" line).
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" goto :bootstrap
"%PY%" -c "import fastapi, uvicorn, requests, Crypto" 2>nul || goto :bootstrap
goto :run

:bootstrap
echo [setup] .venv missing or incomplete, installing deps with uv ...
if not exist "%PY%" uv venv --python 3.12 "%~dp0.venv"
uv pip install --python "%PY%" -r "%~dp0requirements.txt"
if errorlevel 1 goto :fail

:run
rem port: AUTOBA_PORT if set (env.local.bat or shell), default 8800
if not defined AUTOBA_PORT set "AUTOBA_PORT=8800"
"%PY%" -m uvicorn webui.server:app --host 127.0.0.1 --port %AUTOBA_PORT%
pause
exit /b

:fail
echo [error] dependency install failed, see messages above.
pause
exit /b 1
