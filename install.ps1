$ErrorActionPreference = "Stop"
$Python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $Python) {
    $Python = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $Python) {
    Write-Error "Python 3 is required."
    exit 1
}
& $Python.Source (Join-Path $PSScriptRoot "scripts/install_skill.py") @args
exit $LASTEXITCODE
