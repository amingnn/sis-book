param(
    [string]$Version = "dev",
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

if (-not $IsWindows) {
    throw "windows-package.ps1 must run on Windows because pywebview uses the WinForms backend."
}

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDist = Join-Path $ProjectRoot "frontend/dist"
$AlembicIni = Join-Path $BackendDir "alembic.ini"
$AlembicDir = Join-Path $BackendDir "alembic"
$AlembicEnv = Join-Path $AlembicDir "env.py"
$AlembicVersions = Join-Path $AlembicDir "versions/*.py"
$DistDir = Join-Path $ProjectRoot "dist"
$NuitkaOutputDir = Join-Path $DistDir "nuitka"
$NuitkaBuildDir = Join-Path $NuitkaOutputDir "main.dist"
$AppDir = Join-Path $DistDir "暮橙记账本"
$IconPath = Join-Path $ProjectRoot "build/assets/app-icon.ico"
$ReportPath = Join-Path $DistDir "nuitka-report.xml"
$InstallerScript = Join-Path $ProjectRoot "build/installer.iss"
$InstallerVersion = $Version -replace '[\\/:*?"<>|]', "-"
if ([string]::IsNullOrWhiteSpace($InstallerVersion)) {
    $InstallerVersion = "dev"
}

if (-not (Test-Path $FrontendDist)) {
    throw "Missing frontend/dist. Run pnpm build in the frontend directory before packaging."
}
if (-not (Test-Path $AlembicIni)) {
    throw "Missing backend/alembic.ini."
}
if (-not (Test-Path $AlembicDir)) {
    throw "Missing backend/alembic."
}
if (-not (Test-Path $AlembicEnv)) {
    throw "Missing backend/alembic/env.py."
}

New-Item -ItemType Directory -Path $DistDir -Force | Out-Null
Remove-Item -Path $NuitkaOutputDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path $AppDir -Recurse -Force -ErrorAction SilentlyContinue

Push-Location $BackendDir
try {
    uv sync --group build
    uv run --group build python -m nuitka `
        --mode=standalone `
        --assume-yes-for-downloads `
        --output-dir="$NuitkaOutputDir" `
        --output-filename="暮橙记账本.exe" `
        --windows-console-mode=disable `
        --windows-icon-from-ico="$IconPath" `
        --include-package=app `
        --include-package=uvicorn `
        --include-module=webview.platforms.winforms `
        --include-module=clr `
        --include-module=clr_loader `
        --include-data-dir="$FrontendDist=frontend/dist" `
        --include-data-files="$AlembicIni=alembic.ini" `
        --include-data-files="$AlembicEnv=alembic/env.py" `
        --include-data-files="$AlembicVersions=alembic/versions/" `
        --report="$ReportPath" `
        main.py
}
finally {
    Pop-Location
}

if (-not (Test-Path $NuitkaBuildDir)) {
    throw "Nuitka output directory not found: $NuitkaBuildDir"
}

New-Item -ItemType Directory -Path $AppDir -Force | Out-Null
Copy-Item -Path (Join-Path $NuitkaBuildDir "*") -Destination $AppDir -Recurse -Force

if (-not (Test-Path (Join-Path $AppDir "暮橙记账本.exe"))) {
    throw "Packaged executable not found in $AppDir."
}

if (-not $SkipInstaller) {
    & iscc $InstallerScript "/DMyAppVersion=$InstallerVersion"
}
