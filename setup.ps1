#!/usr/bin/env pwsh
# IPTV Spider - UV project bootstrap script
# Purpose: Automatically initialize environment and run project

param(
    [string]$Command = "run",
    [string[]]$CmdArgs = @()
)

# Color definitions
$Colors = @{
    "Success" = "Green"
    "Error" = "Red"
    "Info" = "Cyan"
    "Warning" = "Yellow"
}

# Helper function to write colored output
function Write-Colored {
    param([string]$Message, [string]$Color = "Info")
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

# Helper function to test if command exists
function Test-HasCommand {
    param([string]$Cmd)
    $exists = $null -ne (Get-Command $Cmd -ErrorAction SilentlyContinue)
    return $exists
}

# Main function
function Invoke-Setup {
    Write-Colored "IPTV Spider - UV Project Setup" "Info"
    Write-Host ""

    # Check if UV is installed
    Write-Colored "[*] Checking UV installation..." "Info"
    if (-not (Test-HasCommand "uv")) {
        Write-Colored "[!] Error: UV not installed" "Error"
        Write-Host "Please install UV: pip install uv"
        exit 1
    }
    Write-Colored "[+] UV is installed" "Success"

    # Show UV version
    $uvVersion = & uv --version
    Write-Colored "    $uvVersion" "Info"
    Write-Host ""

    # Sync dependencies
    Write-Colored "[*] Syncing project dependencies..." "Info"
    & uv sync --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Colored "[!] Error: Failed to sync dependencies" "Error"
        exit $LASTEXITCODE
    }
    Write-Colored "[+] Dependencies synced successfully" "Success"
    Write-Host ""

    # Execute command
    switch ($Command.ToLower()) {
        "run" {
            Write-Colored "[*] Running IPTV Spider..." "Info"
            if ($CmdArgs.Count -gt 0) {
                & uv run iptv-spider @CmdArgs
            } else {
                & uv run iptv-spider
            }
        }
        "help" {
            Write-Colored "[*] Showing help information..." "Info"
            & uv run iptv-spider --help
        }
        "test" {
            Write-Colored "[*] Installing test dependencies..." "Info"
            & uv sync --extra test --quiet
            if ($LASTEXITCODE -ne 0) {
                Write-Colored "[!] Error: Failed to sync test dependencies" "Error"
                exit $LASTEXITCODE
            }
            Write-Colored "[*] Running test suite..." "Info"
            & uv run python -m pytest tests/ -v @CmdArgs
        }
        "shell" {
            Write-Colored "[*] Starting Python shell..." "Info"
            & uv run python
        }
        "dev" {
            Write-Colored "[*] Installing dev dependencies..." "Info"
            & uv sync --extra dev --quiet
            Write-Colored "[*] Starting Python shell..." "Info"
            & uv run python
        }
        "clean" {
            Write-Colored "[!] Cleaning virtual environment..." "Warning"
            if (Test-Path .venv) {
                Remove-Item -Path .venv -Recurse -Force
                Write-Colored "[+] Virtual environment removed" "Success"
            } else {
                Write-Colored "[i] Virtual environment not found" "Info"
            }
        }
        "list" {
            Write-Colored "[*] Listing installed packages..." "Info"
            & uv pip list @CmdArgs
        }
        "lint" {
            Write-Colored "[*] Installing dev dependencies..." "Info"
            & uv sync --extra dev --quiet
            if ($LASTEXITCODE -ne 0) {
                Write-Colored "[!] Error: Failed to sync dev dependencies" "Error"
                exit $LASTEXITCODE
            }
            Write-Colored "[*] Running code checks..." "Info"
            & uv run flake8 src/iptv_spider/ @CmdArgs
        }
        default {
            Show-Help
        }
    }
}

function Show-Help {
    Write-Colored "Usage: .\setup.ps1 [command] [arguments]" "Info"
    Write-Host ""
    Write-Colored "Available commands:" "Info"
    Write-Host "  run              Run IPTV Spider (default)"
    Write-Host "  help             Show project help"
    Write-Host "  test             Run unit tests"
    Write-Host "  shell            Start Python shell"
    Write-Host "  dev              Install dev dependencies and start shell"
    Write-Host "  list             List installed packages"
    Write-Host "  lint             Run code checks"
    Write-Host "  clean            Delete virtual environment"
    Write-Host ""
    Write-Colored "Examples:" "Info"
    Write-Host "  # Run project"
    Write-Host "  .\setup.ps1"
    Write-Host ""
    Write-Host "  # Show help"
    Write-Host "  .\setup.ps1 help"
    Write-Host ""
    Write-Host "  # Run with parameters"
    Write-Host '  .\setup.ps1 run --filter "CCTV" --output_dir ".\output"'
    Write-Host ""
    Write-Host "  # Run tests"
    Write-Host "  .\setup.ps1 test"
}

# Run main function
Invoke-Setup
