# CLEANUP SCRIPT - Part 1
# This script removes old, duplicate, and unused files

Write-Host "================================"
Write-Host "🧹 CLEANUP: Removing Old Files"
Write-Host "================================`n"

$deletedFiles = @()
$deletedDirs = @()
$baseDir = "c:\Users\Feroz Khan\project-assistant-bot"

# Function to safely remove files
function Remove-ItemSafely {
    param($Path, $Type)
    if (Test-Path $Path -ErrorAction SilentlyContinue) {
        Remove-Item $Path -Force -Recurse -ErrorAction SilentlyContinue
        if ($Type -eq "File") {
            $script:deletedFiles += $Path
        }
        else {
            $script:deletedDirs += $Path
        }
        Write-Host "✓ Deleted: $Path"
        return $true
    }
    return $false
}

# 1. Delete duplicate docker-compose files
Remove-ItemSafely "$baseDir\docker-compose.prod.yml" "File"
Remove-ItemSafely "$baseDir\docker-compose.whatsapp.yml" "File"

# 2. Delete duplicate Dockerfile.whatsapp
Remove-ItemSafely "$baseDir\Dockerfile.whatsapp" "File"

# 3. Delete old requirements variants (keep only requirements.txt)
Remove-ItemSafely "$baseDir\requirements-docker.txt" "File"
Remove-ItemSafely "$baseDir\requirements-simple.txt" "File"

# 4. Delete legacy_archive folder
Remove-ItemSafely "$baseDir\legacy_archive" "Dir"

# 5. Delete demo files
Remove-ItemSafely "$baseDir\demo_mfa_setup" "Dir"

# 6. Delete .pytest_cache
Get-ChildItem -Path "$baseDir" -Name ".pytest_cache" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    $fullPath = Join-Path $baseDir $_
    Remove-ItemSafely $fullPath "Dir"
}

# 7. Delete __pycache__ folders
Get-ChildItem -Path "$baseDir" -Name "__pycache__" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    $fullPath = Join-Path $baseDir $_
    Remove-ItemSafely $fullPath "Dir"
}

# 8. Delete .pyc files recursively
Get-ChildItem -Path "$baseDir" -Name "*.pyc" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item (Join-Path $baseDir $_) -Force -ErrorAction SilentlyContinue
    $deletedFiles += $_
}

# 9. Delete old QR code PNG files in root
Get-ChildItem -Path "$baseDir" -Name "*.png" -ErrorAction SilentlyContinue | Where-Object {$_ -like "*qr*" -or $_ -like "*mfa*"} | ForEach-Object {
    Remove-ItemSafely "$baseDir\$_" "File"
}

# 10. Delete .venv311_clean if it exists
Remove-ItemSafely "$baseDir\.venv311_clean" "Dir"

# 11. Clean old markdown docs (keep only README.md, keep DEPLOYMENT.md from /docs instead)
Remove-ItemSafely "$baseDir\docs\DEPLOYMENT_GUIDE.md" "File"
Remove-ItemSafely "$baseDir\docs\DEPLOYMENT_SUCCESS.md" "File"

# 12. Delete test output files
Get-ChildItem -Path "$baseDir" -Name "*.tmp" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-ItemSafely (Join-Path $baseDir $_) "File"
}

# 13. Delete backup files
Get-ChildItem -Path "$baseDir" -Name "*.bak" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-ItemSafely (Join-Path $baseDir $_) "File"
}

Get-ChildItem -Path "$baseDir" -Name "*.old" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-ItemSafely (Join-Path $baseDir $_) "File"
}

Get-ChildItem -Path "$baseDir" -Name "*.orig" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-ItemSafely (Join-Path $baseDir $_) "File"
}

Write-Host "`n================================"
Write-Host "📊 Cleanup Summary"
Write-Host "================================"
Write-Host "Files deleted: $($deletedFiles.Count)"
Write-Host "Directories deleted: $($deletedDirs.Count)"
Write-Host "Total removals: $($deletedFiles.Count + $deletedDirs.Count)`n"

Write-Host "Files removed:"
$deletedFiles | ForEach-Object { Write-Host "  - $_" }

Write-Host "`nDirectories removed:"
$deletedDirs | ForEach-Object { Write-Host "  - $_" }

Write-Host "`n✅ Cleanup complete!"
