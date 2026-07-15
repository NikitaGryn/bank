$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"
$manage = Join-Path $root "backend\manage.py"

& $python $manage migrate --noinput
& $python $manage seed_demo

$backend = Start-Process `
    -FilePath $python `
    -ArgumentList @($manage, "runserver", "127.0.0.1:8000", "--noreload") `
    -WorkingDirectory $root `
    -NoNewWindow `
    -PassThru

try {
    Start-Sleep -Seconds 2
    $env:BROKER_API_URL = "http://127.0.0.1:8000/api"
    Push-Location (Join-Path $root "mobile\src")
    & $python -c "import flet as ft; import main; ft.run(main.main, view=ft.AppView.WEB_BROWSER, port=8550)"
}
finally {
    Pop-Location
    if ($backend -and -not $backend.HasExited) {
        Stop-Process -Id $backend.Id
    }
}
