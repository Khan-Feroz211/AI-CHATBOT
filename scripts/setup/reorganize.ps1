# reorganize.ps1
# PowerShell script to reorganize the project structure

Write-Host "🚀 AI Project Assistant - Structure Reorganization" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Confirm before proceeding
$confirm = Read-Host "This will reorganize your project structure. Continue? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "❌ Aborted by user" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "📦 Step 1: Creating backup..." -ForegroundColor Yellow

# Create backup using git
git checkout -b backup-$(Get-Date -Format "yyyyMMdd-HHmmss") 2>$null
if ($LASTEXITCODE -eq 0) {
    git add .
    git commit -m "Backup before reorganization" 2>$null
    Write-Host "✅ Backup created successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️ Git not initialized. Creating manual backup..." -ForegroundColor Yellow
    
    $backupDir = "backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item -Path "." -Destination $backupDir -Recurse -Force
    Write-Host "✅ Manual backup created: $backupDir" -ForegroundColor Green
}

Write-Host ""
Write-Host "📁 Step 2: Creating directory structure..." -ForegroundColor Yellow

# Create web directory
if (-not (Test-Path "web")) {
    New-Item -ItemType Directory -Path "web" -Force | Out-Null
    Write-Host "✅ Created: web/" -ForegroundColor Green
}

if (-not (Test-Path "web\css")) {
    New-Item -ItemType Directory -Path "web\css" -Force | Out-Null
    Write-Host "✅ Created: web/css/" -ForegroundColor Green
}

if (-not (Test-Path "web\js")) {
    New-Item -ItemType Directory -Path "web\js" -Force | Out-Null
    Write-Host "✅ Created: web/js/" -ForegroundColor Green
}

# Create desktop subdirectories
$desktopDirs = @(
    "desktop\auth",
    "desktop\database",
    "desktop\gui",
    "desktop\gui\tabs",
    "desktop\ai",
    "desktop\utils"
)

foreach ($dir in $desktopDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ Created: $dir/" -ForegroundColor Green
    }
}

# Create __init__.py files
$initFiles = @(
    "desktop\auth\__init__.py",
    "desktop\database\__init__.py",
    "desktop\gui\__init__.py",
    "desktop\gui\tabs\__init__.py",
    "desktop\ai\__init__.py",
    "desktop\utils\__init__.py"
)

foreach ($file in $initFiles) {
    if (-not (Test-Path $file)) {
        New-Item -ItemType File -Path $file -Force | Out-Null
        Write-Host "✅ Created: $file" -ForegroundColor Green
    }
}

# Create scripts directory
if (-not (Test-Path "scripts")) {
    New-Item -ItemType Directory -Path "scripts" -Force | Out-Null
    Write-Host "✅ Created: scripts/" -ForegroundColor Green
}

Write-Host ""
Write-Host "📦 Step 3: Moving web files..." -ForegroundColor Yellow

# Move index.html
if (Test-Path "index.html") {
    Move-Item "index.html" "web\" -Force
    Write-Host "✅ Moved: index.html -> web/" -ForegroundColor Green
}

# Move CSS files
if (Test-Path "css") {
    if (Test-Path "css\style.css") {
        Move-Item "css\style.css" "web\css\" -Force
        Write-Host "✅ Moved: css/style.css -> web/css/" -ForegroundColor Green
    }
    Remove-Item "css" -Force -ErrorAction SilentlyContinue
}

# Move JS files
if (Test-Path "js") {
    if (Test-Path "js\script.js") {
        Move-Item "js\script.js" "web\js\" -Force
        Write-Host "✅ Moved: js/script.js -> web/js/" -ForegroundColor Green
    }
    Remove-Item "js" -Force -ErrorAction SilentlyContinue
}

# Move assets
if (Test-Path "assets") {
    Move-Item "assets" "web\" -Force
    Write-Host "✅ Moved: assets/ -> web/assets/" -ForegroundColor Green
}

Write-Host ""
Write-Host "🗑️ Step 4: Cleaning up duplicate files..." -ForegroundColor Yellow

# Remove duplicate requirements
$duplicateReqs = @(
    "requirements (1).txt",
    "requirements (2).txt"
)

foreach ($file in $duplicateReqs) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "✅ Removed: $file" -ForegroundColor Green
    }
}

# Clean up docs directory
$duplicateDocs = @(
    "docs\README (1).md",
    "docs\README (2).md",
    "docs\START_HERE (1).md"
)

foreach ($doc in $duplicateDocs) {
    if (Test-Path $doc) {
        Remove-Item $doc -Force
        Write-Host "✅ Removed: $doc" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "📝 Step 5: Moving utility scripts..." -ForegroundColor Yellow

# Move scripts to scripts directory
$scriptFiles = @(
    "update_repo.bat",
    "update_repo.sh",
    "verify_deployment.sh"
)

foreach ($script in $scriptFiles) {
    if (Test-Path $script) {
        Move-Item $script "scripts\" -Force
        Write-Host "✅ Moved: $script -> scripts/" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "📚 Step 6: Organizing documentation..." -ForegroundColor Yellow

# Create guides subdirectory in docs
if (-not (Test-Path "docs\guides")) {
    New-Item -ItemType Directory -Path "docs\guides" -Force | Out-Null
    Write-Host "✅ Created: docs/guides/" -ForegroundColor Green
}

# Move detailed guides
$guideFiles = @(
    "docs\PRO_FEATURES_GUIDE.md",
    "docs\ENHANCEMENTS_GUIDE.md",
    "docs\ml_projects_concepts_guide.md",
    "docs\learn_ml_architecture_design.md"
)

foreach ($guide in $guideFiles) {
    if (Test-Path $guide) {
        $filename = Split-Path $guide -Leaf
        Move-Item $guide "docs\guides\$filename" -Force
        Write-Host "✅ Moved: $guide -> docs/guides/" -ForegroundColor Green
    }
}

# Move root guides to docs
$rootGuides = @(
    "CHANGELOG_PRO.md",
    "ENHANCEMENTS_GUIDE.md",
    "PRO_FEATURES_GUIDE.md",
    "QUICK_START.md",
    "TODO.md"
)

foreach ($guide in $rootGuides) {
    if (Test-Path $guide) {
        Move-Item $guide "docs\" -Force
        Write-Host "✅ Moved: $guide -> docs/" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "📋 Step 7: Creating project structure documentation..." -ForegroundColor Yellow

# Create structure overview file
$structureDoc = @"
# Project Structure

Last updated: $(Get-Date -Format "yyyy-MM-dd HH:mm")

``````
project-assistant-bot/
│
├── README.md                   # Main project README
├── LICENSE
├── .gitignore
├── requirements.txt            # Main requirements
│
├── web/                       # Web Version
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── assets/
│
├── desktop/                   # Desktop Application
│   ├── README.md
│   ├── requirements.txt
│   ├── MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)  # Current main file
│   ├── enhanced_chatbot.py      # Legacy version
│   │
│   ├── auth/                  # Authentication module
│   │   ├── __init__.py
│   │   └── user_auth.py       # (To be extracted)
│   │
│   ├── database/              # Database operations
│   │   ├── __init__.py
│   │   └── db_manager.py      # (To be extracted)
│   │
│   ├── gui/                   # GUI components
│   │   ├── __init__.py
│   │   ├── app.py             # (To be extracted)
│   │   ├── theme.py           # (To be extracted)
│   │   ├── splash.py          # (To be extracted)
│   │   ├── login.py           # (To be extracted)
│   │   └── tabs/              # Tab modules
│   │       ├── __init__.py
│   │       └── (To be created)
│   │
│   ├── ai/                    # AI backends
│   │   ├── __init__.py
│   │   └── (To be created)
│   │
│   └── utils/                 # Utilities
│       ├── __init__.py
│       └── (To be created)
│
├── chatbot_data/              # Application data
│   ├── chatbot.db
│   └── uploads/
│
├── docs/                      # Documentation
│   ├── README.md
│   ├── QUICK_START.md
│   ├── CHANGELOG.md
│   ├── CONTRIBUTING.md
│   ├── SECURITY.md
│   └── guides/                # Detailed guides
│
├── legacy/                    # Legacy code
│   └── chatbot_demo_light.py
│
├── scripts/                   # Utility scripts
│   ├── reorganize.ps1         # This script
│   ├── update_repo.bat
│   ├── update_repo.sh
│   └── verify_deployment.sh
│
└── __pycache__/              # Python cache
``````

## Next Steps

1. **Review the structure** - Check that all files are in correct locations
2. **Test desktop app** - Verify MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed) still works
3. **Extract modules** - Split MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed) into modules
4. **Update imports** - Update all import statements
5. **Test thoroughly** - Ensure all features work
6. **Update README** - Document the new structure
7. **Commit changes** - Save your reorganized project

## Migration Status

- ✅ Directory structure created
- ✅ Web files moved
- ✅ Scripts organized
- ✅ Docs consolidated
- ⏳ Code extraction pending
- ⏳ Import updates pending
- ⏳ Testing pending

## Commands

### Run Desktop App
``````powershell
cd desktop
python MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)
``````

### Run Web Version Locally
``````powershell
cd web
python -m http.server 8000
# Visit: http://localhost:8000
``````
"@

Set-Content -Path "PROJECT_STRUCTURE.md" -Value $structureDoc
Write-Host "✅ Created: PROJECT_STRUCTURE.md" -ForegroundColor Green

Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ Reorganization Complete!" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Summary:" -ForegroundColor Yellow
Write-Host "  ✅ Directory structure created" -ForegroundColor Green
Write-Host "  ✅ Web files moved to web/" -ForegroundColor Green
Write-Host "  ✅ Scripts moved to scripts/" -ForegroundColor Green
Write-Host "  ✅ Documentation organized" -ForegroundColor Green
Write-Host "  ✅ Duplicate files removed" -ForegroundColor Green
Write-Host "  ✅ Backup created" -ForegroundColor Green
Write-Host ""

Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review the new structure in PROJECT_STRUCTURE.md"
Write-Host "  2. Test desktop app: cd desktop && python MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)"
Write-Host "  3. Extract code modules (see REORGANIZATION_PLAN.md)"
Write-Host "  4. Update README.md with new structure"
Write-Host ""

Write-Host "⚠️ Important:" -ForegroundColor Yellow
Write-Host "  - Your original files are backed up"
Write-Host "  - Desktop app should still work from desktop/"
Write-Host "  - Web files are now in web/"
Write-Host ""

# Ask if user wants to see the structure
$showStructure = Read-Host "Show new directory structure? (y/n)"
if ($showStructure -eq 'y') {
    Write-Host ""
    Get-Content "PROJECT_STRUCTURE.md"
}

Write-Host ""
Write-Host "🎉 Done! Happy coding!" -ForegroundColor Cyan
