$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$flet = Join-Path $root ".venv\Scripts\flet.exe"

& $flet build web (Join-Path $root "mobile") `
    --output (Join-Path $root "dist\web") `
    --product "Беларусбанк Инвестиции" `
    --project belarusbank_invest `
    --org by.belarusbank.demo `
    --pwa-theme-color "#007A3D" `
    --pwa-background-color "#F5F7F6" `
    --yes
