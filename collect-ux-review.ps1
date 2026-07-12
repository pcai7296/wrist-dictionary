param(
  [string]$ProjectRoot = $PSScriptRoot,
  [string]$OutputPath = (Join-Path $PSScriptRoot "ux-source-review.txt")
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$Utf8StrictNoBom = New-Object System.Text.UTF8Encoding($false, $true)
$Utf8WithBom = New-Object System.Text.UTF8Encoding($true)

$excludeDirs = @(
  ".git",
  ".codex",
  ".agents",
  ".vscode",
  "node_modules",
  "build",
  "dist",
  "sign"
)

function Read-Utf8Text {
  param([string]$Path)

  $reader = New-Object System.IO.StreamReader($Path, $Utf8StrictNoBom, $true)
  try {
    return $reader.ReadToEnd()
  } finally {
    $reader.Dispose()
  }
}

function Write-Utf8Text {
  param(
    [string]$Path,
    [string]$Text
  )

  [System.IO.File]::WriteAllText($Path, $Text, $Utf8WithBom)
}

function Test-IsExcludedPath {
  param([string]$FullName)

  $relative = $FullName.Substring($ProjectRoot.Length).TrimStart("\", "/")
  foreach ($dir in $excludeDirs) {
    if ($relative -eq $dir -or $relative -like "$dir\*" -or $relative -like "$dir/*") {
      return $true
    }
  }
  return $false
}

$uxFiles = Get-ChildItem -LiteralPath $ProjectRoot -Recurse -Force -File -Filter "*.ux" |
  Where-Object { -not (Test-IsExcludedPath $_.FullName) } |
  Sort-Object FullName

$lines = New-Object System.Collections.Generic.List[string]
$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$lines.Add("Wanshang Honghuang UX Source Review Bundle")
$lines.Add("Generated At: $now")
$lines.Add("Project Root: $ProjectRoot")
$lines.Add("UX File Count: $($uxFiles.Count)")
$lines.Add("")
$lines.Add("Vela / Band 10 Project Constraints Summary")
$lines.Add("1. manifest.json is the source of app identity, features, permissions, routes, and pages.")
$lines.Add("2. manifest.router.pages must match real page directories and component names; unregistered pages are skipped during packaging.")
$lines.Add("3. Keep every .ux page structured around template / script / style.")
$lines.Add("4. Vela event binding is strict; avoid complex inline expressions and prefer explicit handlers.")
$lines.Add("5. Declare system.router / system.prompt / system.storage and similar APIs in manifest.features before use.")
$lines.Add("6. Xiaomi Band 10 targets a 212x520 capsule screen; use large touch targets, restrained density, and avoid edge-hugging content.")
$lines.Add("7. System edge-swipe back is always available; ordinary non-critical pages usually do not need custom back buttons.")
$lines.Add("8. Symbol glyphs may render unreliably on device; prefer plain text for critical buttons.")
$lines.Add("9. After source changes, verify with npx aiot build and fix the first concrete compiler error first.")
$lines.Add("10. Do not include node_modules, build, dist, sign, or .git in review bundles; sign may contain private keys.")
$lines.Add("")
$lines.Add("================================================================")
$lines.Add("UX Source")
$lines.Add("================================================================")
$lines.Add("")

foreach ($file in $uxFiles) {
  $relative = $file.FullName.Substring($ProjectRoot.Length).TrimStart("\", "/")
  $lines.Add("")
  $lines.Add("################################################################")
  $lines.Add("# FILE: $relative")
  $lines.Add("################################################################")
  $lines.Add("")
  $content = Read-Utf8Text -Path $file.FullName
  $lines.Add($content.TrimEnd())
  $lines.Add("")
}

$outputDir = Split-Path -Parent $OutputPath
if ($outputDir -and -not (Test-Path -LiteralPath $outputDir)) {
  New-Item -ItemType Directory -Path $outputDir | Out-Null
}

$bundle = [string]::Join([Environment]::NewLine, [string[]]$lines) + [Environment]::NewLine
Write-Utf8Text -Path $OutputPath -Text $bundle
Write-Host "Generated: $OutputPath"
Write-Host "UX file count: $($uxFiles.Count)"
