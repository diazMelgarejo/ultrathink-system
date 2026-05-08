#Requires -Version 5.1
<#
.SYNOPSIS
    install.ps1 — One-time Windows setup for orama-system  v0.9.9.8

.DESCRIPTION
    Idempotent setup script (safe to re-run).  Installs Python dependencies,
    verifies LM Studio port, creates .venv if missing, and writes openclaw.json
    defaults for Windows node.

    Run once after cloning:
        powershell -ExecutionPolicy Bypass -File .\windows\install.ps1

.NOTES
    Execution policy: run as:
        Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
    or use the one-liner above.
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $PSCommandPath
$RepoRoot  = Split-Path -Parent $ScriptDir

function _Step { param([string]$Msg) Write-Host "  [+] $Msg" -ForegroundColor Cyan }
function _OK   { param([string]$Msg) Write-Host "  ✓  $Msg" -ForegroundColor Green }
function _Warn { param([string]$Msg) Write-Host "  !  $Msg" -ForegroundColor Yellow }
function _Err  { param([string]$Msg) Write-Host "  ✗  $Msg" -ForegroundColor Red; exit 1 }

Write-Host ''
Write-Host '═══════════════════════════════════════════════════════════' -ForegroundColor DarkCyan
Write-Host '  orama-system Windows installer  v0.9.9.8' -ForegroundColor Cyan
Write-Host '═══════════════════════════════════════════════════════════' -ForegroundColor DarkCyan
Write-Host ''

# ── Python version check ──────────────────────────────────────────────────────
_Step 'Checking Python...'
try {
    $pyVer = & python --version 2>&1
    if ($pyVer -match '(\d+)\.(\d+)') {
        $major = [int]$Matches[1]; $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            _Err "Python 3.10+ required. Found: $pyVer"
        }
        _OK "Python $pyVer"
    }
} catch { _Err 'Python not found. Install from https://python.org/downloads/' }

# ── Virtual environment ───────────────────────────────────────────────────────
$VenvPath = Join-Path $RepoRoot '.venv'
_Step "Checking virtual environment at $VenvPath..."
if (-not (Test-Path (Join-Path $VenvPath 'Scripts\python.exe'))) {
    _Step 'Creating .venv...'
    & python -m venv $VenvPath
    _OK '.venv created'
} else {
    _OK '.venv already exists'
}

$VenvPython = Join-Path $VenvPath 'Scripts\python.exe'
$VenvPip    = Join-Path $VenvPath 'Scripts\pip.exe'

# ── Install dependencies ──────────────────────────────────────────────────────
_Step 'Installing core requirements...'
$rootReqs = Join-Path $RepoRoot 'requirements.txt'
if (Test-Path $rootReqs) {
    & $VenvPip install -r $rootReqs --quiet
    _OK 'Core requirements installed'
} else {
    _Warn "requirements.txt not found at $rootReqs — skipping core install"
}

_Step 'Installing Windows-specific requirements...'
$winReqs = Join-Path $ScriptDir 'requirements-windows.txt'
if (Test-Path $winReqs) {
    & $VenvPip install -r $winReqs --quiet
    _OK 'Windows requirements installed'
} else {
    _Warn "windows/requirements-windows.txt not found — skipping"
}

# ── LM Studio port check ──────────────────────────────────────────────────────
_Step 'Checking LM Studio (localhost:1234)...'
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $conn = $tcp.ConnectAsync('localhost', 1234)
    if ($conn.Wait(2000)) {
        $tcp.Close()
        _OK 'LM Studio is listening on :1234'
    } else {
        $tcp.Close()
        _Warn 'LM Studio not detected on :1234 — start LM Studio before running start.ps1'
    }
} catch {
    _Warn "LM Studio check failed: $_"
}

# ── openclaw.json defaults ────────────────────────────────────────────────────
_Step 'Writing openclaw.json Windows defaults...'
$OcDir  = Join-Path $HOME '.openclaw'
$OcJson = Join-Path $OcDir 'openclaw.json'
$null   = New-Item -ItemType Directory -Force -Path $OcDir

$template = @{
    models = @{
        providers = @{
            'lmstudio-win' = @{ baseUrl = 'http://localhost:1234' }
            'ollama-win'   = @{ baseUrl = 'http://localhost:11434' }
        }
    }
    distributed = $false
    platform    = 'windows'
    version     = '0.9.9.8'
}

if (Test-Path $OcJson) {
    try {
        $existing = Get-Content $OcJson -Raw | ConvertFrom-Json
        # Merge — don't overwrite user customizations
        if (-not $existing.models) {
            $existing | Add-Member -NotePropertyName 'models' -NotePropertyValue $template.models
            $existing | ConvertTo-Json -Depth 10 | Set-Content $OcJson -Encoding UTF8
            _OK "openclaw.json updated (merged defaults)"
        } else {
            _OK "openclaw.json already configured"
        }
    } catch {
        _Warn "Could not read existing openclaw.json: $_ — writing fresh copy"
        $template | ConvertTo-Json -Depth 10 | Set-Content $OcJson -Encoding UTF8
    }
} else {
    $template | ConvertTo-Json -Depth 10 | Set-Content $OcJson -Encoding UTF8
    _OK "openclaw.json created at $OcJson"
}

# ── .paths.ps1 cache ──────────────────────────────────────────────────────────
_Step 'Generating .paths.ps1...'
& $VenvPython (Join-Path $ScriptDir 'start.ps1') --discover
_OK '.paths.ps1 written'

# ── GPU parallel limit (Windows LM Studio rule) ───────────────────────────────
_Warn 'IMPORTANT: Windows GPU loads ONE model at a time.'
_Warn '           Never configure parallel inference on Windows.'
_Warn '           LM Studio handles this automatically in single-model mode.'

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ''
Write-Host '═══════════════════════════════════════════════════════════' -ForegroundColor DarkCyan
_OK 'Install complete!'
Write-Host ''
Write-Host '  Start services:  .\windows\start.ps1'
Write-Host '  Stop services:   .\windows\start.ps1 --stop'
Write-Host '  Check status:    .\windows\start.ps1 --status'
Write-Host ''
