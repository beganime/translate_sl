$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BundleRoot = Join-Path $ProjectRoot "deploy-bundle"
$Stage = Join-Path $BundleRoot "TranslateSL"
$Zip = Join-Path $ProjectRoot "TranslateSL-deploy.zip"

if (Test-Path $BundleRoot) { Remove-Item -LiteralPath $BundleRoot -Recurse -Force }
New-Item -ItemType Directory -Path $Stage | Out-Null

$ExcludedDirectories = @(".git", ".venv", "deploy-bundle", "staticfiles", "tmp", "__pycache__", ".idea", ".vscode")
$ExcludedFiles = @("TranslateSL-deploy.zip", ".env", ".env.production")

Get-ChildItem -LiteralPath $ProjectRoot -Force | Where-Object {
    $_.Name -notin $ExcludedDirectories -and $_.Name -notin $ExcludedFiles
} | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Stage -Recurse -Force
}

Get-ChildItem -LiteralPath $Stage -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $Stage -Recurse -File | Where-Object {
    $_.Extension -in @(".pyc", ".pyo")
} | Remove-Item -Force

# Replace the copied SQLite file with a transactionally consistent snapshot,
# even if the local development server is currently open.
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$env:TRANSLATESL_SOURCE_DB = Join-Path $ProjectRoot "db.sqlite3"
$env:TRANSLATESL_TARGET_DB = Join-Path $Stage "db.sqlite3"
& $Python -c "import os, sqlite3; s=sqlite3.connect(os.environ['TRANSLATESL_SOURCE_DB']); d=sqlite3.connect(os.environ['TRANSLATESL_TARGET_DB']); s.backup(d); d.close(); s.close()"
Remove-Item Env:TRANSLATESL_SOURCE_DB, Env:TRANSLATESL_TARGET_DB

if (Test-Path $Zip) { Remove-Item -LiteralPath $Zip -Force }
& $Python (Join-Path $ProjectRoot "deploy\create_zip.py") $Stage $Zip
if ($LASTEXITCODE -ne 0) { throw "Python failed to create deploy archive." }
Remove-Item -LiteralPath $BundleRoot -Recurse -Force
Write-Host "Created $Zip (includes the current db.sqlite3 and media directory)."
