$ErrorActionPreference = "SilentlyContinue"
$baseDir = "c:\Users\Feroz Khan\project-assistant-bot"
$deletedFiles = @()
$deletedDirs = @()

Write-Host "Cleanup: Removing Old Files..." -ForegroundColor Green

# Files to delete
$filesToDelete = @(
    "docker-compose.prod.yml",
    "docker-compose.whatsapp.yml", 
    "Dockerfile.whatsapp",
    "requirements-docker.txt",
    "requirements-simple.txt",
    "requirements-minimal.txt"
)

foreach ($file in $filesToDelete) {
    $path = Join-Path $baseDir $file
    if (Test-Path $path) {
        Remove-Item $path -Force
        $deletedFiles += $file
        Write-Host "✓ $file"
    }
}

# Directories to delete
$dirsToDelete = @(
    "legacy_archive",
    "demo_mfa_setup"
)

foreach ($dir in $dirsToDelete) {
    $path = Join-Path $baseDir $dir
    if (Test-Path $path) {
        Remove-Item $path -Recurse -Force
        $deletedDirs += $dir
        Write-Host "✓ $dir/"
    }
}

# Remove Python cache recursively
Get-ChildItem -Path $baseDir -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
    $deletedDirs += $_.Name
    Write-Host "✓ __pycache__"
}

Get-ChildItem -Path $baseDir -Recurse -Directory -Filter ".pytest_cache" | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
    $deletedDirs += $_.Name
    Write-Host "✓ .pytest_cache"
}

# Remove backup files
Get-ChildItem -Path $baseDir -Recurse -File -Filter "*.bak" | ForEach-Object {
    Remove-Item $_.FullName -Force
    $deletedFiles += $_.Name
}

Get-ChildItem -Path $baseDir -Recurse -File -Filter "*.old" | ForEach-Object {
    Remove-Item $_.FullName -Force
    $deletedFiles += $_.Name
}

Get-ChildItem -Path $baseDir -Recurse -File -Filter "*.orig" | ForEach-Object {
    Remove-Item $_.FullName -Force
    $deletedFiles += $_.Name
}

Write-Host "`n✅ Cleanup Summary:" -ForegroundColor Green
Write-Host "Files deleted: $($deletedFiles.Count)"
Write-Host "Directories deleted: $($deletedDirs.Count)"
