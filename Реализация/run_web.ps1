$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$flet = Join-Path $root ".venv\Scripts\flet.exe"
$env:BROKER_API_URL = "http://127.0.0.1:8000/api"

& $flet run --web --port 8550 (Join-Path $root "mobile")
