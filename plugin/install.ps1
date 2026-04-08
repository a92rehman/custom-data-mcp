# Taleemabad Data Plugin — Windows PowerShell Installer
# Two-step install: download this file, then run it
# Usage: .\install.ps1
param()
$ErrorActionPreference = "Stop"

$REPO = "https://github.com/Orenda-Project/taleemabad-data-mcp.git"
$PLUGIN_DIR = "$env:USERPROFILE\.claude\plugins\taleemabad-data"
$VENV_DIR = "$env:USERPROFILE\.claude\taleemabad-venv"
$ENV_FILE = "$env:USERPROFILE\.claude\taleemabad-data-mcp.env"

Write-Host ""
Write-Host "=== Taleemabad Data Plugin Installer ===" -ForegroundColor Cyan
Write-Host ""

# --- Prerequisites check ---
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python not found. Install Python 3.11+ from python.org"
    exit 1
}
$pythonVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$pyOk = & python -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>$null; $pyOkCode = $LASTEXITCODE
if ($pyOkCode -ne 0) {
    Write-Error "Python 3.11+ required. Found $pythonVersion"
    exit 1
}
Write-Host "✓ Python $pythonVersion"

$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) { Write-Error "git not found. Install Git for Windows."; exit 1 }
Write-Host "✓ git"

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) { Write-Warning "node not found. bigquery-analytics MCP will not work." }

# --- Detect existing install ---
if (Test-Path $PLUGIN_DIR) {
    Write-Host "Existing install found at $PLUGIN_DIR — running upgrade..."
    Set-Location $PLUGIN_DIR
    git fetch --tags --quiet
    $LATEST = (git tag -l 'v*' --sort=-v:refname | Select-Object -First 1)
    if ($LATEST) { git checkout $LATEST --quiet; Set-Content .current-version $LATEST }
    & "$VENV_DIR\Scripts\pip" install --quiet --force-reinstall "git+${REPO}@${LATEST}"
    # Re-substitute .mcp.json in case template changed in this release
    if (Test-Path $ENV_FILE) {
        $envContent = Get-Content $ENV_FILE | ForEach-Object {
            $parts = $_ -split '=', 2; [PSCustomObject]@{Key=$parts[0]; Value=$parts[1]}
        }
        $savedUser = ($envContent | Where-Object Key -eq 'TALEEMABAD_USER').Value
        $savedCreds = ($envContent | Where-Object Key -eq 'GOOGLE_APPLICATION_CREDENTIALS').Value
        if ($savedUser -and $savedCreds) {
            $winPython = "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -replace '\\', '\\\\'
            $mcpTemplate = Get-Content "$PLUGIN_DIR\plugin\.mcp.json" -Raw
            $mcpFinal = $mcpTemplate `
                -replace [regex]::Escape('${HOME}/.claude/taleemabad-venv/bin/python'), $winPython `
                -replace '\$\{HOME\}', ($env:USERPROFILE -replace '\\', '\\\\') `
                -replace '\$\{TALEEMABAD_CREDENTIALS\}', ($savedCreds -replace '\\', '\\\\') `
                -replace '\$\{TALEEMABAD_USER\}', $savedUser
            $mcpFinal | Set-Content "$PLUGIN_DIR\.mcp.json"
            Write-Host "✓ MCP config refreshed"
        }
    }
    Write-Host "✓ Upgraded to $LATEST"
    exit 0
}

# --- Clone plugin ---
Write-Host "Cloning plugin to $PLUGIN_DIR..."
git clone --quiet $REPO $PLUGIN_DIR
Set-Location $PLUGIN_DIR
$LATEST = (git tag -l 'v*' --sort=-v:refname | Select-Object -First 1)
if ($LATEST) {
    git checkout $LATEST --quiet
    Set-Content .current-version $LATEST
    Write-Host "✓ Pinned to $LATEST"
}

# --- Create venv ---
Write-Host "Creating Python venv at $VENV_DIR..."
python -m venv $VENV_DIR
& "$VENV_DIR\Scripts\pip" install --quiet --upgrade pip

# --- Install MCP server ---
Write-Host "Installing taleemabad-data-mcp..."
$installTag = if ($LATEST) { $LATEST } else { "main" }
& "$VENV_DIR\Scripts\pip" install --quiet "git+${REPO}@${installTag}[dashboard]"
Write-Host "✓ MCP server installed"

# --- Prompt for credentials ---
Write-Host ""
Write-Host "=== Configuration ===" -ForegroundColor Cyan
$TALEEMABAD_USER = Read-Host "Your name (for audit logs)"
$CREDENTIALS_PATH = Read-Host "Path to GCP service account JSON"
$CREDENTIALS_PATH = $CREDENTIALS_PATH -replace "~", $env:USERPROFILE

if (-not (Test-Path $CREDENTIALS_PATH)) {
    Write-Error "File not found: $CREDENTIALS_PATH"
    exit 1
}

# --- Save config ---
"TALEEMABAD_USER=$TALEEMABAD_USER`nGOOGLE_APPLICATION_CREDENTIALS=$CREDENTIALS_PATH" | Set-Content $ENV_FILE
icacls $ENV_FILE /inheritance:r /grant:r "${env:USERNAME}:(R,W)" | Out-Null
Write-Host "✓ Config saved to $ENV_FILE"

# --- Write final .mcp.json with substituted values ---
# On Windows, replace the Unix venv path pattern with the Windows equivalent
$winPython = "$env:USERPROFILE\.claude\taleemabad-venv\Scripts\python.exe" -replace '\\', '\\\\'
$mcpTemplate = Get-Content "$PLUGIN_DIR\plugin\.mcp.json" -Raw
$mcpFinal = $mcpTemplate `
    -replace [regex]::Escape('${HOME}/.claude/taleemabad-venv/bin/python'), $winPython `
    -replace '\$\{HOME\}', ($env:USERPROFILE -replace '\\', '\\\\') `
    -replace '\$\{TALEEMABAD_CREDENTIALS\}', ($CREDENTIALS_PATH -replace '\\', '\\\\') `
    -replace '\$\{TALEEMABAD_USER\}', $TALEEMABAD_USER
$mcpFinal | Set-Content "$PLUGIN_DIR\.mcp.json"
Write-Host "✓ MCP config written"

Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Plugin installed at: $PLUGIN_DIR"
Write-Host "Version: $LATEST"
Write-Host ""
Write-Host "Restart Claude Code to activate the plugin."
Write-Host "Ask 'what version of taleemabad data am I running?' to verify."
