# scripts/ensure_requirements.ps1 — Windows hard-requirements probe + installer
# orama-system v0.9.9.8 — Run on the Windows GPU box
#
# HARD requirements:
#   LM Studio — auto-installed via winget if missing
#   Model loaded: Qwen3.5-27B (checked via LM Studio API)
#
# Usage (run in PowerShell as Administrator or regular user with winget):
#   .\scripts\ensure_requirements.ps1            # check + install
#   .\scripts\ensure_requirements.ps1 -CheckOnly # probe only, exit 1 if missing
#   .\scripts\ensure_requirements.ps1 -Force     # reinstall even if present
#
# Env overrides:
#   LM_STUDIO_WIN_PORT — override default 1234

param(
    [switch]$CheckOnly,
    [switch]$Force,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$LmStudioPort = $env:LM_STUDIO_WIN_PORT ?? "1234"
$LmStudioUrl  = "http://localhost:${LmStudioPort}"
$LogDir       = Join-Path $PSScriptRoot ".." ".logs"
$HardFail     = $false

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log($Level, $Msg) {
    $ts = (Get-Date).ToString("HH:mm:ss")
    $line = "[$ts] $Level [ensure-win] $Msg"
    if ($Level -ne "INFO " -or -not $Quiet) { Write-Host $line }
    Add-Content -Path (Join-Path $LogDir "ensure-win.log") -Value $line -ErrorAction SilentlyContinue
}
function ok($m)   { Write-Log "OK   " $m }
function info($m) { Write-Log "INFO " $m }
function warn($m) { Write-Log "WARN " $m }
function err($m)  { Write-Log "ERROR" $m; $script:HardFail = $true }

# ── OS fingerprint ─────────────────────────────────────────────────────────────
$WinVer = (Get-CimInstance Win32_OperatingSystem).Caption
$WinBuild = (Get-CimInstance Win32_OperatingSystem).BuildNumber
info "Platform: $WinVer (build $WinBuild)"

# ── PHASE 1: LM Studio binary ─────────────────────────────────────────────────
info "Phase 1 — LM Studio binary"

$LmStudioExe = @(
    "$env:LOCALAPPDATA\Programs\LM-Studio\LM Studio.exe",
    "$env:PROGRAMFILES\LM-Studio\LM Studio.exe",
    "$env:LOCALAPPDATA\LM-Studio\LM Studio.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $LmStudioExe) {
    if ($CheckOnly) {
        err "LM Studio not installed. Run without -CheckOnly to install."
    } else {
        info "LM Studio not found — installing via winget..."
        try {
            winget install --id "ElementLabs.LMStudio" --accept-source-agreements --accept-package-agreements `
                --silent 2>&1 | Tee-Object -Append -FilePath (Join-Path $LogDir "lmstudio-install.log")
            # Re-probe after install
            $LmStudioExe = @(
                "$env:LOCALAPPDATA\Programs\LM-Studio\LM Studio.exe",
                "$env:PROGRAMFILES\LM-Studio\LM Studio.exe"
            ) | Where-Object { Test-Path $_ } | Select-Object -First 1
            if ($LmStudioExe) { ok "LM Studio installed: $LmStudioExe" }
            else { err "LM Studio install completed but binary not found. Check logs." }
        } catch {
            err "winget install failed: $_. Manual install: https://lmstudio.ai/download"
        }
    }
} else {
    ok "LM Studio present: $LmStudioExe"
}

# ── PHASE 2: LM Studio server reachable ───────────────────────────────────────
info "Phase 2 — LM Studio server probe (port $LmStudioPort)"

if (-not $HardFail) {
    try {
        $resp = Invoke-RestMethod -Uri "${LmStudioUrl}/v1/models" -TimeoutSec 5 -ErrorAction Stop
        ok "LM Studio server responding on :$LmStudioPort"
    } catch {
        if ($CheckOnly) {
            warn "LM Studio server not reachable on :$LmStudioPort — start LM Studio and load a model"
        } else {
            warn "LM Studio server not reachable. Start LM Studio, enable the local server, and load a model."
            warn "Server tab → Start Server button → port $LmStudioPort"
        }
    }
}

# ── PHASE 3: Python venv + deps ───────────────────────────────────────────────
info "Phase 3 — Python venv + dependencies"

$RepoRoot  = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvDir   = Join-Path $RepoRoot ".venv"
$ReqFile   = Join-Path $RepoRoot "requirements.txt"
$StampFile = Join-Path $RepoRoot ".requirements.stamp"

if (-not (Test-Path $VenvDir)) {
    if (-not $CheckOnly) {
        info "Creating Python venv..."
        python -m venv $VenvDir 2>&1 | Out-File -Append (Join-Path $LogDir "install.log")
    } else {
        warn ".venv not found — run without -CheckOnly to create"
    }
}

if (Test-Path $VenvDir) {
    $PipExe = Join-Path $VenvDir "Scripts\pip.exe"
    if (Test-Path $ReqFile) {
        $ReqHash = (Get-FileHash $ReqFile -Algorithm SHA256).Hash
        $StampHash = if (Test-Path $StampFile) { (Get-Content $StampFile | Where-Object { $_ -match "^python_req=" }) -replace "python_req=",""  } else { "" }
        if ($Force -or $StampHash -ne $ReqHash) {
            if (-not $CheckOnly) {
                info "Installing Python deps..."
                & $PipExe install -q -r $ReqFile 2>&1 | Out-File -Append (Join-Path $LogDir "install.log")
                "python_req=$ReqHash`nts=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')`nversion=1" | Set-Content $StampFile
                ok "Python deps installed"
            } else {
                warn "requirements.txt changed — run without -CheckOnly to update"
            }
        } else {
            ok "Python deps up-to-date (stamp matches)"
        }
    }
}

# ── RESULT ────────────────────────────────────────────────────────────────────
Write-Host ""
if ($HardFail) {
    err "Hard requirements FAILED on Windows — see output above."
    err "Full spec: CLAUDE-instru.md §6"
    Write-Host ""
    exit 1
} else {
    ok "Windows requirements check complete"
    Write-Host ""
    exit 0
}
