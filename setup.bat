@echo off
REM IPTV Spider - UV 项目启动脚本（CMD/批处理版本）
REM 用途: 自动初始化环境并运行项目

setlocal enabledelayedexpansion

if "%1"=="" (
    set "CMD=run"
) else (
    set "CMD=%1"
)

echo.
echo ==========================================
echo   IPTV Spider - UV Project Setup
echo ==========================================
echo.

REM 检查 UV 是否安装
echo [*] Checking UV installation...
uv --version >nul 2>&1
if errorlevel 1 (
    echo [!] Error: UV not installed
    echo     Please install UV: pip install uv
    exit /b 1
)
echo [+] UV is installed
for /f "tokens=*" %%i in ('uv --version') do echo     %%i
echo.

REM 同步依赖
echo [*] Syncing project dependencies...
uv sync --quiet
if errorlevel 1 (
    echo [!] Error: Failed to sync dependencies
    exit /b 1
)
echo [+] Dependencies synced successfully
echo.

REM 执行命令
if /i "%CMD%"=="run" (
    echo [*] Running IPTV Spider...
    uv run iptv-spider %*
    goto :end
)

if /i "%CMD%"=="help" (
    echo [*] Showing help information...
    uv run iptv-spider --help
    goto :end
)

if /i "%CMD%"=="test" (
    echo [*] Running test suite...
    uv run python -m pytest tests/ -v
    goto :end
)

if /i "%CMD%"=="shell" (
    echo [*] Starting Python shell...
    uv run python
    goto :end
)

if /i "%CMD%"=="dev" (
    echo [*] Installing dev dependencies...
    uv sync --extra dev --quiet
    echo [*] Starting Python shell...
    uv run python
    goto :end
)

if /i "%CMD%"=="clean" (
    echo [!] Cleaning virtual environment...
    if exist .venv (
        rmdir /s /q .venv
        echo [+] Virtual environment removed
    ) else (
        echo [i] Virtual environment not found
    )
    goto :end
)

if /i "%CMD%"=="list" (
    echo [*] Listing installed packages...
    uv pip list
    goto :end
)

if /i "%CMD%"=="lint" (
    echo [*] Running code checks...
    uv run flake8 src/iptv_spider/
    goto :end
)

REM 显示帮助
echo Usage: setup.bat [command] [arguments]
echo.
echo Available commands:
echo   run              Run IPTV Spider (default)
echo   help             Show project help
echo   test             Run unit tests
echo   shell            Start Python shell
echo   dev              Install dev dependencies and start shell
echo   list             List installed packages
echo   lint             Run code checks
echo   clean            Delete virtual environment
echo.
echo Examples:
echo   setup.bat
echo   setup.bat help
echo   setup.bat run --filter "CCTV" --output_dir ".\output"
echo   setup.bat test

:end
endlocal
