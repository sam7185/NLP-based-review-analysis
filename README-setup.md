Quick setup for NLP-based-review-analysis (Windows PowerShell)

Prerequisites
- Python 3.10/3.11 installed (3.13 may have fewer binary wheels)
- Git

Steps (one-command bootstrap)
1. Clone the repo and open PowerShell.
2. From the repo root run (this will create a venv, install minimal deps and run migrations):

   .\setup.ps1 -UseMinimalFile -Migrate

3. To also install the scientific stack (may need build tools) and start the server:

   .\setup.ps1 -UseMinimalFile -InstallScientific -Migrate -RunServer

Notes
- Preferred: Use Miniconda for the scientific stack, but the script supports a pip-based install with --prefer-binary.
- If pip fails to build native packages on Windows, install Microsoft C++ Build Tools or use conda.
- The script creates a `.venv` folder in the repo root. Activate it manually with:

  . .\.venv\Scripts\Activate.ps1

Troubleshooting
- If package installs fail, paste the last lines of `scripts\install_deps.log` and I'll help.
