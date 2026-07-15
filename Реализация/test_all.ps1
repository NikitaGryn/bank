$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"

& $python (Join-Path $root "backend\manage.py") test broker
& $python -m unittest discover -s (Join-Path $root "mobile\tests") -v
& $python -m compileall -q (Join-Path $root "backend") (Join-Path $root "mobile")
