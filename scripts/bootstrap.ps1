# autoBA bootstrap: ensure Python 3.12 and project dependencies.
# Invoked by start_webui.bat when .venv is missing, broken or not Python 3.12.
#
# Order:
#   1. use an already installed uv (no download)
#   2. otherwise download a pinned uv into <repo>\tools\uv\<version> (gitignored)
#   3. if uv is unavailable, fall back to a local Python 3.12 + python -m venv
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$uvVersion = '0.13.6'
$arch = $env:PROCESSOR_ARCHITECTURE
switch ($arch) {
    'AMD64' {
        $uvAsset = 'uv-x86_64-pc-windows-msvc.zip'
        $uvSha = 'a2a8820d5eea32f08ef467ef3b7f66883a9b076d5737a2fc2fbb5f458d1bb50f'
    }
    'ARM64' {
        $uvAsset = 'uv-aarch64-pc-windows-msvc.zip'
        $uvSha = 'c2426c0c8e28b53d8c440e47a18d96ad4db51e159866c0e81435b196d7f0081c'
    }
    default {
        throw "Unsupported architecture: $arch (需要 64 位 Windows)"
    }
}

function Find-Python312 {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { return @{ Exe = $py.Source; Pre = @('-3.12') } }
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { return @{ Exe = $python.Source; Pre = @() } }
    }
    return $null
}

# 1) Prefer an already installed uv.
$uvExe = $null
$systemUv = Get-Command uv -ErrorAction SilentlyContinue
if ($systemUv) {
    $uvText = (& $systemUv.Source --version) 2>$null
    Write-Host "[setup] found installed uv: $($uvText -join ' ')"
    & $systemUv.Source venv --help *> $null
    if ($LASTEXITCODE -eq 0) {
        $uvExe = $systemUv.Source
    } else {
        Write-Warning 'installed uv cannot handle `uv venv`; falling back to pinned uv'
    }
}

# 2) No usable uv: download a pinned copy into the repo (tools/uv is gitignored).
if (-not $uvExe) {
    $uvDir = Join-Path $root "tools\uv\$uvVersion"
    $uvExe = Join-Path $uvDir 'uv.exe'
    if (-not (Test-Path $uvExe)) {
        New-Item -ItemType Directory -Force $uvDir | Out-Null
        $zip = Join-Path $uvDir $uvAsset
        $url = "https://github.com/astral-sh/uv/releases/download/$uvVersion/$uvAsset"
        Write-Host "[setup] downloading uv $uvVersion into $uvDir ..."
        $ok = $false
        for ($attempt = 1; $attempt -le 3 -and -not $ok; $attempt++) {
            try {
                Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $zip
                $hash = (Get-FileHash -Algorithm SHA256 $zip).Hash.ToLower()
                if ($hash -ne $uvSha) {
                    throw "uv checksum mismatch: $hash"
                }
                Expand-Archive -Force $zip -DestinationPath $uvDir
                Remove-Item $zip -Force -ErrorAction SilentlyContinue
                $ok = $true
            } catch {
                Write-Warning "uv download attempt $attempt failed: $_"
                Remove-Item $zip -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds (2 * $attempt)
            }
        }
    }
    if (-not (Test-Path $uvExe)) { $uvExe = $null }
}

$venv = Join-Path $root '.venv'
if (Test-Path $venv) {
    $bak = Join-Path $root ('.venv.bak-' + (Get-Date -Format 'yyyyMMddHHmmss'))
    Write-Host "[setup] moving existing .venv to $bak"
    Move-Item $venv $bak
}
$py = Join-Path $venv 'Scripts\python.exe'

if ($uvExe) {
    Write-Host '[setup] creating .venv with Python 3.12 via uv ...'
    & $uvExe venv --python 3.12 $venv
    if ($LASTEXITCODE -ne 0) { throw "uv venv failed (exit $LASTEXITCODE)" }

    & $py -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
    if ($LASTEXITCODE -ne 0) { throw 'created environment is not Python 3.12' }

    Write-Host '[setup] installing dependencies ...'
    & $uvExe pip install --python $py -r (Join-Path $root 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw "dependency install failed (exit $LASTEXITCODE)" }
} else {
    Write-Warning 'uv is unavailable and could not be downloaded; trying local Python 3.12'
    $pyInfo = Find-Python312
    if (-not $pyInfo) {
        throw 'no usable uv and no Python 3.12 found; install uv (https://docs.astral.sh/uv/) or Python 3.12'
    }
    Write-Host '[setup] creating .venv with local Python 3.12 ...'
    $venvArgs = @($pyInfo.Pre) + @('-m', 'venv', $venv)
    & $pyInfo.Exe @venvArgs
    if ($LASTEXITCODE -ne 0) { throw "python -m venv failed (exit $LASTEXITCODE)" }

    & $py -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
    if ($LASTEXITCODE -ne 0) { throw 'created environment is not Python 3.12' }

    Write-Host '[setup] installing dependencies ...'
    & $py -m pip install --disable-pip-version-check -r (Join-Path $root 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw "dependency install failed (exit $LASTEXITCODE)" }
}

& $py -c "import fastapi, uvicorn, requests, Crypto"
if ($LASTEXITCODE -ne 0) { throw 'dependency verification failed' }

Write-Host '[setup] environment ready'
exit 0
