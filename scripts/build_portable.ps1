# Build a self-contained Windows x64 portable package.
# Output: dist/autoBA-portable-win64.zip
#
# Local usage:
#   .\scripts\build_portable.ps1
#   .\scripts\build_portable.ps1 -PythonSource C:\path\to\python-dir
#
# The optional -PythonSource reuses an existing standalone Python directory
# instead of downloading one via uv (useful for offline/local builds).
param(
    [string]$OutDir = 'dist',
    [string]$PythonSource = ''
)
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$tempRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [IO.Path]::GetTempPath() }
$stage = Join-Path $tempRoot 'autoBA-portable'
$runtime = Join-Path $stage 'runtime'
$pythonDir = Join-Path $runtime 'python'
$outDir = Join-Path $root $OutDir
$zip = Join-Path $outDir 'autoBA-portable-win64.zip'

if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Force $stage | Out-Null
New-Item -ItemType Directory -Force $runtime | Out-Null

if ($PythonSource) {
    Write-Host "[build] copying Python from $PythonSource"
    Copy-Item $PythonSource $pythonDir -Recurse -Force
} else {
    $installDir = Join-Path $stage '.python-install'
    New-Item -ItemType Directory -Force $installDir | Out-Null
    $env:UV_PYTHON_INSTALL_DIR = $installDir
    Write-Host '[build] downloading Python 3.12 via uv ...'
    uv python install 3.12
    if ($LASTEXITCODE -ne 0) { throw "uv python install failed (exit $LASTEXITCODE)" }

    $src = Get-ChildItem $installDir -Directory |
        Where-Object { -not $_.LinkType -and (Test-Path (Join-Path $_.FullName 'python.exe')) } |
        Select-Object -First 1
    if (-not $src) { throw 'managed Python directory not found' }
    Move-Item $src.FullName $pythonDir
    Remove-Item $installDir -Recurse -Force
}

$py = Join-Path $pythonDir 'python.exe'
if (-not (Test-Path $py)) { throw "python.exe not found: $py" }

Write-Host '[build] installing dependencies into portable runtime ...'
uv pip install --python $py --break-system-packages -r (Join-Path $root 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw "dependency install failed (exit $LASTEXITCODE)" }

& $py -c "import sys, fastapi, uvicorn, requests, Crypto"
if ($LASTEXITCODE -ne 0) { throw 'portable runtime verification failed' }

Write-Host '[build] copying project files ...'
$excludeDirs = @('.git', '.github', '.venv', '.venv.bak-*', 'build', 'dist', 'tools',
    '.screenshots', '__pycache__', 'logs', 'static')
$excludeFiles = @(
    'session_state.json', 'yostar_token.json', 'yostar_credentials.json', 'yostar_phone.json',
    'clan_state.json', 'resource_state.json', 'ticket_state.json', 'monitor_state.json',
    'favor_state.json', 'ui_state.json', 'daily_state.json', '*.log', '*.pyc'
)
$rc = @($root, $stage, '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/R:1', '/W:1')
$rc += '/XD'
$rc += $excludeDirs
$rc += '/XF'
$rc += $excludeFiles
& robocopy @rc | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed (exit $LASTEXITCODE)" }

$launcher = @'
@echo off
setlocal
cd /d "%~dp0"
if exist "env.local.bat" call "env.local.bat"
set "PY=%~dp0runtime\python\python.exe"
if not exist "%PY%" (echo [error] runtime missing & pause & exit /b 1)
if not defined AUTOBA_PORT set "AUTOBA_PORT=8800"
"%PY%" -m uvicorn webui.server:app --host 127.0.0.1 --port %AUTOBA_PORT%
pause
'@
$launcherPath = Join-Path $stage 'start_webui.bat'
[IO.File]::WriteAllText($launcherPath, $launcher.Replace("`n", "`r`n"), [Text.Encoding]::ASCII)

$portableReadme = @'
autoBA portable (Windows x64)

解压后双击 start_webui.bat 即可启动，无需安装 Python / uv。
首次启动仍需要联网访问游戏服务器。
运行状态与凭据会生成在当前目录，不会随包分发。
'@
[IO.File]::WriteAllText((Join-Path $stage 'PORTABLE.txt'), $portableReadme, (New-Object Text.UTF8Encoding($false)))

New-Item -ItemType Directory -Force $outDir | Out-Null
if (Test-Path $zip) { Remove-Item $zip -Force }
Write-Host '[build] creating zip ...'
Compress-Archive -Path $stage -DestinationPath $zip -CompressionLevel Optimal
Write-Host ("[build] done: {0} ({1:N1} MB)" -f $zip, ((Get-Item $zip).Length / 1MB))
