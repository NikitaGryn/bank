$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$flet = Join-Path $root ".venv\Scripts\flet.exe"
$sourceApp = Join-Path $root "mobile"
$app = Join-Path $env:TEMP (
    "belarusbank_flet_build_" + [System.Guid]::NewGuid().ToString("N")
)

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:NO_COLOR = "1"
$env:_JAVA_OPTIONS = "-Xmx3g -XX:MaxMetaspaceSize=1g -XX:ReservedCodeCacheSize=256m -Dorg.gradle.workers.max=2 -Dorg.gradle.parallel=false"
$androidSdk = Join-Path $env:USERPROFILE "Android\sdk"
$env:JAVA_HOME = Join-Path $env:USERPROFILE "java\17.0.13+11"
$env:ANDROID_HOME = $androidSdk
$env:ANDROID_SDK_ROOT = $androidSdk
$env:PATH = "$(Join-Path $androidSdk 'platform-tools');$(Join-Path $androidSdk 'cmdline-tools\12.0\bin');$env:PATH"
$sdkManager = Join-Path $androidSdk "cmdline-tools\12.0\bin\sdkmanager.bat"
$buildMutex = [System.Threading.Mutex]::new(
    $false,
    "Local\BelarusbankInvestmentsApkBuild"
)
$hasBuildLock = $false

try {
    $hasBuildLock = $buildMutex.WaitOne(0)
}
catch [System.Threading.AbandonedMutexException] {
    $hasBuildLock = $true
}
if (-not $hasBuildLock) {
    $buildMutex.Dispose()
    throw "APK build is already running. Wait for it to finish."
}

try {
    $requiredSdkPaths = @(
        (Join-Path $androidSdk "platform-tools"),
        (Join-Path $androidSdk "platforms\android-36"),
        (Join-Path $androidSdk "build-tools\36.0.0"),
        (Join-Path $androidSdk "ndk\28.2.13676358")
    )
    if ($requiredSdkPaths | Where-Object { -not (Test-Path $_) }) {
        ((1..100 | ForEach-Object { "y" }) -join "`n") |
            & $sdkManager "--sdk_root=$androidSdk" --licenses
        & $sdkManager "--sdk_root=$androidSdk" `
            "platform-tools" `
            "platforms;android-36" `
            "build-tools;36.0.0" `
            "ndk;28.2.13676358"
    }

    New-Item $app -ItemType Directory | Out-Null
    Copy-Item (Join-Path $sourceApp "pyproject.toml") $app
    Copy-Item (Join-Path $sourceApp "src") $app -Recurse

    & $flet build apk $app `
        --output (Join-Path $root "dist\apk") `
        --product "Belarusbank Investments" `
        --project belarusbank_invest `
        --artifact belarusbank-invest `
        --org by.belarusbank.demo `
        --bundle-id by.belarusbank.demo.invest `
        --description "Belarusbank brokerage application" `
        --splash-color "#F5F7F6" `
        --android-adaptive-icon-background "#007A3D" `
        --android-permissions android.permission.INTERNET=true `
        --arch arm64-v8a `
        --no-rich-output `
        --yes
}
finally {
    if ($hasBuildLock) {
        $buildMutex.ReleaseMutex()
    }
    $buildMutex.Dispose()
}
