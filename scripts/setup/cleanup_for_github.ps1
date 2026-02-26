# Cleanup Script for GitHub Push
# Run this to organize your project before pushing

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "  PROJECT CLEANUP FOR GITHUB PUSH" -ForegroundColor Yellow
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# 1. Remove duplicate/backup files
Write-Host "🧹 Step 1: Removing duplicate and backup files..." -ForegroundColor Cyan

$filesToRemove = @(
    "MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed).backup",
    "README_NEW (1).md",
    "requirements_pro.txt"  # Keep only requirements.txt
)

foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  ✅ Removed: $file" -ForegroundColor Green
    }
}

# 2. Clean up docs folder
Write-Host ""
Write-Host "📚 Step 2: Organizing docs folder..." -ForegroundColor Cyan

$docsToRemove = @(
    "docs\README (1).md",
    "docs\README (2).md",
    "docs\START_HERE (1).md"
)

foreach ($file in $docsToRemove) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  ✅ Removed duplicate: $file" -ForegroundColor Green
    }
}

# 3. Move root documentation to docs
Write-Host ""
Write-Host "📄 Step 3: Moving documentation to docs folder..." -ForegroundColor Cyan

$docsToMove = @(
    "CHANGELOG_PRO.md",
    "ENHANCEMENTS_GUIDE.md",
    "PRO_FEATURES_GUIDE.md",
    "QUICK_START.md",
    "REORGANIZATION_PLAN.md",
    "TODO.md"
)

foreach ($file in $docsToMove) {
    if (Test-Path $file) {
        Move-Item $file "docs\" -Force
        Write-Host "  ✅ Moved: $file → docs\" -ForegroundColor Green
    }
}

# 4. Update .gitignore if needed
Write-Host ""
Write-Host "🛡️ Step 4: Checking .gitignore..." -ForegroundColor Cyan

$gitignoreContent = @"
# Database files - DON'T push user data!
chatbot_data/
*.db
*.sqlite
*.sqlite3
*.db-journal

# Desktop app data
desktop/chatbot_data/

# User uploads
uploads/
files/
chatbot_data/uploads/
chatbot_data/files/

# Python cache
__pycache__/
*.py[cod]
*`$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db
desktop.ini

# Logs
*.log

# Environment variables (API keys!)
.env
.env.local
.env.*.local

# Temporary files
*.tmp
*.temp
temp/
tmp/

# Backup files
*.backup
*.bak
*_backup.*

# Empty asset folders (will add later)
assets/.gitkeep
css/.gitkeep
js/.gitkeep
"@

Set-Content -Path ".gitignore" -Value $gitignoreContent -Force
Write-Host "  ✅ Updated .gitignore" -ForegroundColor Green

# 5. Create .gitkeep for empty folders
Write-Host ""
Write-Host "📁 Step 5: Creating .gitkeep for empty folders..." -ForegroundColor Cyan

$emptyFolders = @("assets", "css", "js")
foreach ($folder in $emptyFolders) {
    if (Test-Path $folder) {
        New-Item -Path "$folder\.gitkeep" -ItemType File -Force | Out-Null
        Write-Host "  ✅ Created: $folder\.gitkeep" -ForegroundColor Green
    }
}

# 6. Create requirements.txt if missing
Write-Host ""
Write-Host "📦 Step 6: Checking requirements.txt..." -ForegroundColor Cyan

if (-not (Test-Path "requirements.txt")) {
    $requirements = @"
# Core dependencies
tkinter-tooltip==0.0.1

# PDF Export
reportlab==4.0.7

# AI Providers (optional)
openai==1.3.5
anthropic==0.7.1

# Environment variables
python-dotenv==1.0.0

# Database
# sqlite3 is built-in to Python
"@
    Set-Content -Path "requirements.txt" -Value $requirements
    Write-Host "  ✅ Created requirements.txt" -ForegroundColor Green
} else {
    Write-Host "  ℹ️ requirements.txt already exists" -ForegroundColor Yellow
}

# 7. Create PROJECT_STRUCTURE.md
Write-Host ""
Write-Host "📊 Step 7: Creating PROJECT_STRUCTURE.md..." -ForegroundColor Cyan

$structureDoc = @"
# 📁 Project Structure

``````
project-assistant-bot/
│
├── 📄 README.md                    # Main documentation
├── 📜 LICENSE                      # MIT License
├── 🔒 .gitignore                   # Git ignore rules
├── 📦 requirements.txt             # Python dependencies
├── 🐍 MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)      # Main application (Desktop)
│
├── 🌐 web/                         # Web Interface
│   ├── index.html                  # Main HTML file
│   ├── css/
│   │   └── style.css              # Styles
│   └── js/
│       └── script.js              # JavaScript
│
├── 🖥️ desktop/                     # Desktop App (Modular - WIP)
│   ├── enhanced_chatbot.py        # Alternative version
│   ├── MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)    # Pro version
│   ├── enhanced_chatbot_pro_modules.py  # Extracted modules
│   ├── requirements.txt
│   ├── ai/                        # AI backend modules
│   ├── auth/                      # Authentication
│   ├── database/                  # Database operations
│   ├── gui/                       # GUI components
│   └── utils/                     # Utilities
│
├── 📚 docs/                        # Documentation
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── QUICK_START.md
│   ├── PRO_FEATURES_GUIDE.md
│   ├── ENHANCEMENTS_GUIDE.md
│   ├── CONTRIBUTING.md
│   ├── SECURITY.md
│   └── [other guides...]
│
├── 🔧 scripts/                     # Utility scripts
│   ├── update_repo.bat
│   ├── update_repo.sh
│   ├── verify_deployment.sh
│   └── reorganize.ps1
│
├── 🗂️ legacy/                      # Previous versions
│   └── chatbot_demo_light.py
│
├── 🗄️ chatbot_data/               # Local data (NOT in Git!)
│   ├── chatbot.db                 # SQLite database
│   ├── uploads/                   # User uploaded files
│   └── files/                     # Managed files
│
├── 🎨 assets/                      # Images, icons (empty for now)
├── 📄 css/                         # Root CSS (legacy, moving to web/)
└── 📜 js/                          # Root JS (legacy, moving to web/)

``````

## 🔐 Security Notes

**Files/folders NOT pushed to GitHub (see .gitignore):**
- ❌ \`chatbot_data/\` - Contains user databases
- ❌ \`*.db\` - SQLite databases with user data
- ❌ \`uploads/\` - User uploaded files
- ❌ \`__pycache__/\` - Python cache
- ❌ \`.env\` - Environment variables (API keys)

## 🚀 Quick Start

1. **Desktop App:** \`python MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)\`
2. **Web Interface:** \`cd web && python -m http.server 8000\`

## 📝 Notes

- Main desktop app is in root: \`MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)\`
- Modular version is WIP in \`desktop/\` folder
- Web interface is complete in \`web/\` folder
- All documentation in \`docs/\` folder
"@

Set-Content -Path "PROJECT_STRUCTURE.md" -Value $structureDoc
Write-Host "  ✅ Created PROJECT_STRUCTURE.md" -ForegroundColor Green

# 8. Final status
Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "  ✅ CLEANUP COMPLETE!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Summary:" -ForegroundColor Yellow
Write-Host "  ✅ Removed duplicate files" -ForegroundColor Green
Write-Host "  ✅ Organized documentation" -ForegroundColor Green
Write-Host "  ✅ Updated .gitignore" -ForegroundColor Green
Write-Host "  ✅ Created .gitkeep files" -ForegroundColor Green
Write-Host "  ✅ Updated requirements.txt" -ForegroundColor Green
Write-Host "  ✅ Created PROJECT_STRUCTURE.md" -ForegroundColor Green
Write-Host ""

Write-Host "🚀 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Run: python migrate_database.py" -ForegroundColor Cyan
Write-Host "  2. Test: python MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)" -ForegroundColor Cyan
Write-Host "  3. Check: git status" -ForegroundColor Cyan
Write-Host "  4. Push: git add . && git commit -m 'Clean up structure' && git push" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
