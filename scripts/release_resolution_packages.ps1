$ErrorActionPreference = "Stop"

$targets = @(
  @{ Id = "W192"; Width = 192; Height = 490 },
  @{ Id = "W212"; Width = 212; Height = 520 },
  @{ Id = "W336"; Width = 336; Height = 336 },
  @{ Id = "W432"; Width = 432; Height = 432 },
  @{ Id = "W466"; Width = 466; Height = 466 }
)

$root = Split-Path -Parent $PSScriptRoot
$output = Join-Path $root "dist\resolutions-release"
$staging = Join-Path $root ".tmp\resolution-release-packages"
if (Test-Path -LiteralPath $staging) {
  Remove-Item -LiteralPath $staging -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $staging | Out-Null
$manifest = @()
$sha256 = [System.Security.Cryptography.SHA256]::Create()

try {
  foreach ($target in $targets) {
    Write-Host "Releasing $($target.Id) ($($target.Width)x$($target.Height))"
    $env:TARGET_ID = $target.Id
    $env:TARGET_WIDTH = [string]$target.Width
    $env:TARGET_HEIGHT = [string]$target.Height

    Push-Location $root
    try {
      npx aiot release --enable-custom-component
      if ($LASTEXITCODE -ne 0) {
        throw "Release failed for $($target.Id)"
      }
    } finally {
      Pop-Location
    }

    $rpk = Get-ChildItem -LiteralPath (Join-Path $root "dist") -Filter "*.release.*.rpk" -File |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 1
    if ($null -eq $rpk) {
      throw "No release RPK generated for $($target.Id)"
    }

    $name = "com.watch.dic.release.2.3.0.$($target.Id.ToLowerInvariant()).rpk"
    $destination = Join-Path $staging $name
    Copy-Item -LiteralPath $rpk.FullName -Destination $destination -Force
    $hash = ([System.BitConverter]::ToString($sha256.ComputeHash([System.IO.File]::ReadAllBytes($destination))) -replace "-", "").ToLowerInvariant()
    $manifest += [ordered]@{
      id = $target.Id
      width = $target.Width
      height = $target.Height
      file = $name
      sha256 = $hash
      package = "com.watch.dic"
      version = "2.3.0"
      mode = "release"
    }
  }
} finally {
  Remove-Item Env:TARGET_ID, Env:TARGET_WIDTH, Env:TARGET_HEIGHT -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Force -Path $output | Out-Null
Get-ChildItem -LiteralPath $output -File -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem -LiteralPath $staging -Filter "*.rpk" -File | Copy-Item -Destination $output -Force
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $output "manifest.json") -Encoding utf8
Write-Host "Created $($manifest.Count) release packages in $output"
