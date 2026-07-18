@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title LiteLLM Proxy - 腕上词典
cd /d "%~dp0"

set KEY=sk-sGkQ0s9uI3KEOwktoKPJDSYjhDGfhx9TEQ5dzkcruTq1kvgNSkcOuJF1pwY0NkSY
set LITELLM=%APPDATA%\Python\Python314\Scripts\litellm.exe

echo [~] LiteLLM 代理启动工具 - 腕上词典
echo.

:: 检查端口
netstat -ano 2>nul | findstr ":4000 " >nul
if !ERRORLEVEL! equ 0 (
    echo [✓] LiteLLM 已在运行（端口 4000）
    goto :prompt
)

:: 后台启动（start /b 在当前 cmd 窗口隐藏运行）
start /b "" "!LITELLM!" --config J:\litellm_config.yaml --port 4000 --telemetry=false 2>nul

:: 等待就绪
echo [~] 等待 LiteLLM 就绪（最多 25 秒）...
for /l %%i in (1,1,25) do (
    >nul 2>&1 netstat -ano | findstr ":4000 "
    if !ERRORLEVEL! equ 0 (
        echo [✓] LiteLLM 已就绪（端口 4000）
        goto :prompt
    )
    >nul ping -n 2 127.0.0.1
)
echo [✗] 启动超时，请检查日志: J:\litellm.log
pause
exit /b 1

:prompt
echo.
echo  LiteLLM 代理已在后台运行
echo  关闭此窗口不会影响 LiteLLM
echo.
echo  手动管理:
echo    停止: taskkill /f /im litellm.exe
echo    日志: type J:\litellm.log
echo.
choice /c YNC /n /m "[Y]启动 Codex  [N]仅启动 LiteLLM  [C]取消: "
if !ERRORLEVEL! equ 1 goto :launch
if !ERRORLEVEL! equ 2 exit /b 0
if !ERRORLEVEL! equ 3 exit /b 0

:launch
echo [~] 启动 Codex CLI...
set CODEX=
where codex >nul 2>&1 && set CODEX=found
if not defined CODEX if exist "%USERPROFILE%\.codex\bin\codex.exe" set "CODEX=%USERPROFILE%\.codex\bin\codex.exe"
if not defined CODEX if exist "%LOCALAPPDATA%\Programs\codex\codex.exe" set "CODEX=%LOCALAPPDATA%\Programs\codex\codex.exe"

if not defined CODEX (
    echo [✗] 未找到 Codex CLI，请手动启动
    echo    LiteLLM 已在后台运行（端口 4000）
    pause
    exit /b 1
)

if "!CODEX!"=="found" (codex) else ("!CODEX!")
