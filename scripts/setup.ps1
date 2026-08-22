$ErrorActionPreference = 'Stop'
$skillRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $skillRoot '.venv'

if (-not (Test-Path -LiteralPath $venvPath)) {
    py -3 -m venv $venvPath
}

$pythonPath = Join-Path $venvPath 'Scripts\python.exe'
& $pythonPath -m pip install --disable-pip-version-check -r (Join-Path $PSScriptRoot 'requirements.txt')
& $pythonPath -c "import cv2, ezdxf, numpy, PIL, pygerber, vtracer; print('artwork-pcb-enig dependencies ready')"
