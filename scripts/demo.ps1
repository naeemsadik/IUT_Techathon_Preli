# Demo launcher - starts backend, simulator, and (optionally) the
# Discord bot, all from one PowerShell command. Designed for techathon demos.
#
# Usage (from repo root):
#
#   powershell -File scripts\demo.ps1                # backend + simulator
#   powershell -File scripts\demo.ps1 -WithBot       # backend + simulator + Discord bot
#   powershell -File scripts\demo.ps1 -Stop          # stop everything started here
#
# (Or, if you have PowerShell 7+: `pwsh -File scripts\demo.ps1 [args]` works
#  identically — both are accepted by this script.)
#
# Each child process is launched in a separate window so you can see their
# logs side-by-side. Hit Ctrl+C in any window to stop that component.

[CmdletBinding()]
param(
    [switch]$WithBot,
    [switch]$Stop
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$LogDir = Join-Path $RepoRoot "logs_demo"
$MarkerFile = Join-Path $LogDir ".demo-pids.txt"

function Ensure-Venv {
    if (-not (Test-Path (Join-Path $RepoRoot ".venv"))) {
        Write-Host "[setup] Creating venv and installing requirements..."
        python -m venv (Join-Path $RepoRoot ".venv")
        & (Join-Path $RepoRoot ".venv/Scripts/python.exe") -m pip install -r (Join-Path $RepoRoot "requirements.txt")
    }
}

function Stop-Demo {
    if (-not (Test-Path $MarkerFile)) {
        Write-Host "[stop] No marker file. Nothing to stop."
        return
    }
    Get-Content $MarkerFile | ForEach-Object {
        $proc = Get-Process -Id ([int]$_) -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "[stop] Killing PID $($proc.Id) ($($proc.ProcessName))"
            Stop-Process -Id $proc.Id -Force
        }
    }
    Remove-Item $MarkerFile -Force
    Write-Host "[stop] Done."
}

function Start-Demo {
    if (-not (Test-Path (Join-Path $RepoRoot "backend/.env"))) {
        Write-Host "[setup] Creating backend/.env from example"
        Copy-Item (Join-Path $RepoRoot "backend/.env.example") (Join-Path $RepoRoot "backend/.env")
    }

    Ensure-Venv
    if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

    $python = Join-Path $RepoRoot ".venv/Scripts/python.exe"
    # Plain array works in PS 5.1 — System.Collections.Generic.List is 7+ only.
    $pids = @()

    # 1. Backend
    Write-Host "[start] Backend (uvicorn) on http://127.0.0.1:8000"
    $p = Start-Process -FilePath $python `
        -ArgumentList @("-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $RepoRoot `
        -RedirectStandardOutput (Join-Path $LogDir "backend.out.log") `
        -RedirectStandardError  (Join-Path $LogDir "backend.err.log") `
        -PassThru -WindowStyle Normal
    $pids += $p.Id
    Start-Sleep -Seconds 2

    # 2. Simulator
    Write-Host "[start] Simulator (15 devices, staggered 3s/5s/7s)"
    $p = Start-Process -FilePath $python `
        -ArgumentList @("-m", "simulator.simulator") `
        -WorkingDirectory $RepoRoot `
        -RedirectStandardOutput (Join-Path $LogDir "simulator.out.log") `
        -RedirectStandardError  (Join-Path $LogDir "simulator.err.log") `
        -PassThru -WindowStyle Normal
    $pids += $p.Id

    # 3. Bot (optional)
    if ($WithBot) {
        if (-not (Test-Path (Join-Path $RepoRoot "bot/.env"))) {
            Write-Host "[setup] bot/.env missing — bot will fail to start. Copy bot\.env.example first." -ForegroundColor Yellow
        }
        Write-Host "[start] Discord bot"
        $p = Start-Process -FilePath $python `
            -ArgumentList @("-m", "bot.bot") `
            -WorkingDirectory $RepoRoot `
            -RedirectStandardOutput (Join-Path $LogDir "bot.out.log") `
            -RedirectStandardError  (Join-Path $LogDir "bot.err.log") `
            -PassThru -WindowStyle Normal
        $pids += $p.Id
    }

    # Use a string array so PS 5.1's Out-File writes one PID per line reliably.
    $pids | ForEach-Object { [string]$_ } | Out-File -FilePath $MarkerFile -Encoding ascii
    Write-Host ""
    Write-Host "============================================================"
    Write-Host "Demo stack is up."
    Write-Host "  Backend:   http://127.0.0.1:8000/docs"
    Write-Host "  Simulator: running in background, logs in logs_demo/"
    Write-Host "  Frontend:  run cd frontend; npm run dev"
    if ($WithBot) {
        Write-Host "  Bot:       running in background"
    }
    Write-Host ""
    Write-Host "To stop everything:"
    Write-Host "  powershell -File scripts\demo.ps1 -Stop"
    Write-Host "============================================================"
}

if ($Stop) {
    Stop-Demo
} else {
    Start-Demo
}
