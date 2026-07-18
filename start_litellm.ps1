param(
  [switch]$NoCodex,
  [switch]$Force
)

$ErrorActionPreference = "Stop"

# ─── 配置 ───────────────────────────────────────────────────
$litellmPath   = "$env:APPDATA\Python\Python314\Scripts\litellm.exe"
$configPath    = "J:\litellm_config.yaml"
$logFile       = "J:\litellm.log"
$port          = 4000
$masterKey     = "sk-sGkQ0s9uI3KEOwktoKPJDSYjhDGfhx9TEQ5dzkcruTq1kvgNSkcOuJF1pwY0NkSY"

# ─── 环境变量 ───────────────────────────────────────────────
$env:LITELLM_MASTER_KEY = $masterKey
$env:OCC_ZEN_API_KEY    = $masterKey

# ─── 检查是否已运行 ─────────────────────────────────────────
$existing = Get-Process -Name "litellm" -ErrorAction SilentlyContinue
if ($existing) {
  try {
    $tcp = New-Object Net.Sockets.TcpClient('127.0.0.1', $port)
    $tcp.Close()
    Write-Host "[✓] LiteLLM 已在运行 (PID $($existing.Id), 端口 $port)" -ForegroundColor Green
    if (-not $NoCodex) { goto LaunchCodex }
    exit 0
  } catch {
    if (-not $Force) {
      Write-Host "[!] LiteLLM 进程存在但端口 $port 不可用，使用 -Force 强制重启" -ForegroundColor Yellow
      exit 1
    }
    Write-Host "[~] 强制重启 LiteLLM..." -ForegroundColor Yellow
    $existing | Stop-Process -Force
    Start-Sleep -Seconds 2
  }
}

# ─── 启动 LiteLLM ──────────────────────────────────────────
Write-Host "[~] 启动 LiteLLM 代理 → http://127.0.0.1:$port ..." -ForegroundColor Cyan

$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = $litellmPath
$startInfo.Arguments = "--config `"$configPath`" --port $port --telemetry=false"
$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$startInfo.UseShellExecute = $false
$startInfo.EnvironmentVariables["LITELLM_MASTER_KEY"] = $masterKey
$startInfo.EnvironmentVariables["OCC_ZEN_API_KEY"] = $masterKey

try {
  $proc = [System.Diagnostics.Process]::Start($startInfo)
  # 把输出异步写入日志
  $proc.BeginOutputReadLine()
  $proc.BeginErrorReadLine()
  $proc.OutputDataReceived.Add({ param($s, $e) if ($e.Data) { "$($e.Data)" | Out-File $logFile -Append } })
  $proc.ErrorDataReceived.Add({ param($s, $e) if ($e.Data) { "$($e.Data)" | Out-File $logFile -Append } })
} catch {
  Write-Host "[✗] 启动 LiteLLM 失败: $_" -ForegroundColor Red
  exit 1
}

# ─── 等待就绪 ─────────────────────────────────────────────
Write-Host "[~] 等待 LiteLLM 就绪..." -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 1
  try {
    $tcp = New-Object Net.Sockets.TcpClient('127.0.0.1', $port)
    $tcp.Close()
    $ready = $true
    break
  } catch {}
}
if (-not $ready) {
  Write-Host "[✗] LiteLLM 未能就绪，请检查日志: $logFile" -ForegroundColor Red
  exit 1
}

Write-Host "[✓] LiteLLM 已就绪 (PID $($proc.Id), 端口 $port)" -ForegroundColor Green

# ─── 验证接口 ──────────────────────────────────────────────
try {
  $body = @{ model = "deepseek-v4-flash-free"; messages = @(@{ role = "user"; content = "ping" }); max_tokens = 5 } | ConvertTo-Json
  $r = Invoke-RestMethod -Uri "http://127.0.0.1:$port/v1/chat/completions" -Method Post -Body $body -ContentType "application/json" -Headers @{ Authorization = "Bearer $masterKey" }
  if ($r.choices) { Write-Host "[✓] /v1/chat/completions 响应正常" -ForegroundColor Green }
} catch {
  Write-Host "[!] 接口验证请求失败: $_" -ForegroundColor Yellow
}

# ─── 启动 Codex ────────────────────────────────────────────
if (-not $NoCodex) {
  :LaunchCodex
  $codexCmd = (Get-Command "codex" -ErrorAction SilentlyContinue) -or (Get-Command "codex.exe" -ErrorAction SilentlyContinue)
  if ($codexCmd) {
    Write-Host "[~] 启动 Codex CLI..." -ForegroundColor Cyan
    codex
  } else {
    Write-Host "[!] 未找到 Codex 命令，请手动启动" -ForegroundColor Yellow
  }
}
