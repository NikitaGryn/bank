$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"

& $python (Join-Path $root "backend\manage.py") migrate
& $python (Join-Path $root "backend\manage.py") seed_demo
& $python (Join-Path $root "backend\manage.py") runserver 0.0.0.0:8000
