param(
  [string]$Serial = "emulator-5554",
  [switch]$NoBuild
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$manifestPath = Join-Path $projectRoot "src\manifest.json"
$distDir = Join-Path $projectRoot "dist"
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$packageName = [string]$manifest.package

if (-not $packageName) {
  throw "manifest package is empty: $manifestPath"
}

if (-not $NoBuild) {
  Push-Location $projectRoot
  try {
    npm run build
    if ($LASTEXITCODE -ne 0) {
      exit $LASTEXITCODE
    }
  } finally {
    Pop-Location
  }
}

$rpk = Get-ChildItem -LiteralPath $distDir -Filter "$packageName.debug.*.rpk" -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

if (-not $rpk) {
  $rpk = Get-ChildItem -LiteralPath $distDir -Filter "*.rpk" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
}

if (-not $rpk) {
  throw "No RPK found in $distDir"
}

$targetRpk = "/data/app/$packageName.rpk"
Write-Host "Package: $packageName"
Write-Host "RPK: $($rpk.FullName)"
Write-Host "Target: $targetRpk"

adb -s $Serial push "$($rpk.FullName)" $targetRpk
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

adb -s $Serial shell pm install $targetRpk
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

adb -s $Serial shell am start $packageName
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Start-Sleep -Seconds 2
$dump = adb -s $Serial shell am dump
$dump
if (($dump -join "`n") -notmatch [regex]::Escape("$packageName/QuickActivity") + "\s+\[resumed\]") {
  Write-Warning "App start was not confirmed by am dump."
  exit 2
}
