<#
Install common scientific/development packages using pip (non-conda path).

Usage (from project root, with venv activated):
  .\scripts\install_pip_deps.ps1

What it does:
 - upgrades pip and wheel
 - attempts to install numpy, pandas, matplotlib, plotly, wordcloud, pillow
 - uses --prefer-binary to prefer wheels when available
 - logs output to scripts\install_deps.log for troubleshooting

If an installation fails (Meson/VS or compilation errors), see the 'Troubleshooting' section below.
#>

$LogPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) 'install_deps.log'
Write-Host "Logging install output to $LogPath"

# Ensure we're in repo root
$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $Root

Write-Host "Upgrading pip and wheel..."
python -m pip install --upgrade pip setuptools wheel | Tee-Object -FilePath $LogPath -Append

$pkgs = @(
    'numpy',
    'pandas',
    'matplotlib',
    'plotly',
    'wordcloud',
    'pillow'
)

# Try to install with prefer-binary to use prebuilt wheels when available
Write-Host "Installing packages: $($pkgs -join ', ')"
$cmd = "pip install --prefer-binary $($pkgs -join ' ')"
Write-Host "Running: $cmd"
Invoke-Expression "$cmd 2>&1 | Tee-Object -FilePath $LogPath -Append"

if ($LASTEXITCODE -ne 0) {
    Write-Host "One or more packages failed to install. See $LogPath for details." -ForegroundColor Yellow
    Write-Host "Common issues on Windows: missing C/C++ build tools or no wheels for Python 3.13."
    Write-Host "Troubleshooting options:" -ForegroundColor Cyan
    Write-Host "  1) Install Microsoft Build Tools (https://visualstudio.microsoft.com/visual-cpp-build-tools/) and retry."
    Write-Host "  2) Try a different Python version (3.11) in a new venv where wheels are more widely available." 
    Write-Host "  3) Copy/paste the last ~40 lines from $LogPath here and I will triage them."
} else {
    Write-Host "All packages installed successfully." -ForegroundColor Green
}

Write-Host "Done. If some installs failed, paste the log (or the error lines) and I'll help fix them."