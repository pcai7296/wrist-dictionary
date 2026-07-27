$ErrorActionPreference = "Stop"

$targets = @(
  @{ Id = "W192"; Width = 192; Script = "build:192" },
  @{ Id = "W212"; Width = 212; Script = "build:212" },
  @{ Id = "W336"; Width = 336; Script = "build:336" },
  @{ Id = "W432"; Width = 432; Script = "build:432" },
  @{ Id = "W466"; Width = 466; Script = "build:466" }
)

$root = Split-Path -Parent $PSScriptRoot
$output = Join-Path $root "dist\resolutions"
$staging = Join-Path $root ".tmp\resolution-packages"
if (Test-Path -LiteralPath $staging) {
  Remove-Item -LiteralPath $staging -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $staging | Out-Null
$manifest = @()
$sha256 = [System.Security.Cryptography.SHA256]::Create()

foreach ($target in $targets) {
  Write-Host "Building $($target.Id) ($($target.Width)px)"
  Push-Location $root
  try {
    npm run $target.Script
    if ($LASTEXITCODE -ne 0) {
      throw "Build failed for $($target.Id)"
    }
  } finally {
    Pop-Location
  }

  $rpk = Get-ChildItem -LiteralPath (Join-Path $root "dist") -Filter "*.rpk" -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
  if ($null -eq $rpk) {
    throw "No RPK generated for $($target.Id)"
  }

  $name = "com.watch.dic.debug.2.3.0.$($target.Id.ToLowerInvariant()).rpk"
  $destination = Join-Path $staging $name
  Copy-Item -LiteralPath $rpk.FullName -Destination $destination -Force
  $bytes = [System.IO.File]::ReadAllBytes($destination)
  $hash = ([System.BitConverter]::ToString($sha256.ComputeHash($bytes)) -replace "-", "").ToLowerInvariant()
  $manifest += [ordered]@{
    id = $target.Id
    width = $target.Width
    file = $name
    sha256 = $hash
    package = "com.watch.dic"
    version = "2.3.0"
  }
}

New-Item -ItemType Directory -Force -Path $output | Out-Null
Get-ChildItem -LiteralPath $output -File -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem -LiteralPath $staging -Filter "*.rpk" -File | Copy-Item -Destination $output -Force
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $output "manifest.json") -Encoding utf8
Write-Host "Created $($manifest.Count) resolution packages in $output"
