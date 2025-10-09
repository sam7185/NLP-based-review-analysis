<#
PowerShell setup script for NLP-based-review-analysis

Usage:
  .\setup.ps1            # full install from requirements.txt
  .\setup.ps1 -Minimal   # install minimal dependencies only

This script will:
 - create a virtual environment in `.venv`
 - activate it for the current session
 - upgrade pip
 - install dependencies
 - print next steps (migrate, runserver)
#>
[CmdletBinding()]
param(
    [switch]$UseMinimalFile,
    [switch]$InstallScientific,
    [switch]$Migrate,
    [switch]$RunServer
)

$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $Root

$VenvPath = Join-Path $Root ".venv"

function Create-VenvIfMissing {
    param($VenvPath)
    if (-not (Test-Path $VenvPath)) {
        Write-Host "Creating virtual environment at $VenvPath..."
        python -m venv $VenvPath
    } else {
        Write-Host "Virtual environment already exists at $VenvPath"
    }
}

function Activate-Venv {
    param($VenvPath)
    $Activate = Join-Path $VenvPath "Scripts\Activate.ps1"
    if (Test-Path $Activate) {
        Write-Host "Activating virtual environment..."
        & $Activate
        return $true
    } else {
        Write-Warning "Couldn't find Activate.ps1. You may need to activate the venv manually: \n.\$VenvPath\Scripts\Activate.ps1"
        return $false
    }
}

Create-VenvIfMissing -VenvPath $VenvPath

$activated = Activate-Venv -VenvPath $VenvPath

Write-Host "Upgrading pip & setuptools..."
python -m pip install --upgrade pip setuptools wheel

# Install minimal requirements
if ($UseMinimalFile) {
    $MinPath = Join-Path $Root "requirements-minimal.txt"
    if (Test-Path $MinPath) {
        Write-Host "Installing dependencies from requirements-minimal.txt..."
        pip install -r $MinPath
    } else {
        Write-Warning "requirements-minimal.txt not found at $MinPath. Skipping minimal install."
    }
} else {
    # default to minimal file if present
    $MinPath = Join-Path $Root "requirements-minimal.txt"
    if (Test-Path $MinPath) {
        Write-Host "Installing dependencies from requirements-minimal.txt (default)..."
        pip install -r $MinPath
    } else {
        Write-Warning "requirements-minimal.txt not found. Consider creating or passing -UseMinimalFile with file present."
    }
}

# Optional: install scientific stack via pip (may require build tools on Windows)
if ($InstallScientific) {
    Write-Host "Installing scientific stack (numpy, pandas, matplotlib, plotly, wordcloud, pillow)..."
    pip install --prefer-binary numpy pandas matplotlib plotly wordcloud pillow
}

if ($Migrate) {
    Write-Host "Running Django migrations..."
    Push-Location -Path (Join-Path $Root 'Backend')
    python manage.py migrate
    Pop-Location
}

if ($RunServer) {
    Write-Host "Starting Django development server..."
    Push-Location -Path (Join-Path $Root 'Backend')
    python manage.py runserver
}

Write-Host "Bootstrap finished. Useful flags: -UseMinimalFile -InstallScientific -Migrate -RunServer"
