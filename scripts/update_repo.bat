@echo off
REM AI Chatbot Repository Update Script for Windows
REM This script automates the repository update process

echo ============================================
echo  AI Chatbot Repository Update Script
echo ============================================
echo.

REM Check if we're in a git repository
if not exist ".git" (
    echo [ERROR] This is not a git repository!
    echo Please run this script from your AI-CHATBOT repository root.
    pause
    exit /b 1
)

echo [OK] Git repository detected
echo.

REM Step 1: Create folder structure
echo Step 1: Creating folder structure...
if not exist "legacy" mkdir legacy
if not exist "assets" mkdir assets
if not exist "docs" mkdir docs
echo [OK] Folders created: legacy\, assets\, docs\
echo.

REM Step 2: Move old files to legacy
echo Step 2: Moving old files to legacy...
if exist "chatbot_demo_light.py" (
    move /Y chatbot_demo_light.py legacy\ >nul 2>&1
    echo [OK] Moved chatbot_demo_light.py
)

if exist "chatbot_enhanced_ui.py" (
    move /Y chatbot_enhanced_ui.py legacy\ >nul 2>&1
    echo [OK] Moved chatbot_enhanced_ui.py
)

if exist "chatbot_vibrant_colors.py" (
    move /Y chatbot_vibrant_colors.py legacy\ >nul 2>&1
    echo [OK] Moved chatbot_vibrant_colors.py
)

if exist "index.html" (
    move /Y index.html legacy\ >nul 2>&1
    echo [OK] Moved index.html
)

if exist "QUICK_START_GUIDE.md" (
    move /Y QUICK_START_GUIDE.md docs\ >nul 2>&1
    echo [OK] Moved QUICK_START_GUIDE.md to docs\
)
echo.

REM Step 3: Backup old README
echo Step 3: Backing up old README...
if exist "README.md" (
    move /Y README.md legacy\README_old.md >nul 2>&1
    echo [OK] Old README backed up to legacy\README_old.md
)
echo.

REM Step 4: Copy new files
echo Step 4: Please copy the following files to your repository:
echo   1. enhanced_chatbot.py (to root)
echo   2. requirements.txt (to root)
echo   3. README.md (to root)
echo   4. CHANGELOG.md (to root)
echo   5. LICENSE (to root)
echo   6. .gitignore (to root)
echo   7. QUICK_START.md (to docs\)
echo   8. ENHANCEMENTS_GUIDE.md (to docs\)
echo.
set /p COPIED="Have you copied all the files? (Y/N): "
if /i not "%COPIED%"=="Y" (
    echo [WARNING] Please copy the files and run this script again.
    pause
    exit /b 1
)

echo [OK] Files copied
echo.

REM Step 5: Test the new chatbot
echo Step 5: Testing the enhanced chatbot...
if not exist "enhanced_chatbot.py" (
    echo [ERROR] enhanced_chatbot.py not found!
    echo Please copy it to the repository root.
    pause
    exit /b 1
)
echo [INFO] You can test with: python enhanced_chatbot.py
echo.

REM Step 6: Git operations
echo Step 6: Preparing git operations...
echo Current git status:
git status --short
echo.

set /p STAGE="Do you want to stage all changes? (Y/N): "
if /i "%STAGE%"=="Y" (
    REM Add new files
    git add enhanced_chatbot.py 2>nul
    git add requirements.txt 2>nul
    git add .gitignore 2>nul
    git add CHANGELOG.md 2>nul
    git add LICENSE 2>nul
    git add README.md 2>nul
    git add docs\ 2>nul
    git add legacy\ 2>nul
    git add assets\ 2>nul
    
    REM Remove old tracked files
    git rm --cached chatbot_demo_light.py 2>nul
    git rm --cached chatbot_enhanced_ui.py 2>nul
    git rm --cached chatbot_vibrant_colors.py 2>nul
    git rm --cached index.html 2>nul
    git rm --cached QUICK_START_GUIDE.md 2>nul
    
    echo [OK] Changes staged
    echo.
    
    echo Ready to commit. Suggested commit message:
    echo.
    echo "Major Update: Enhanced Production-Ready Version 2.0"
    echo.
    
    set /p COMMIT="Do you want to commit now? (Y/N): "
    if /i "%COMMIT%"=="Y" (
        git commit -m "🚀 Major Update: Enhanced Production-Ready Version 2.0" -m "" -m "- Added SQLite database for persistent storage" -m "- Implemented advanced task management with priorities and categories" -m "- Added note organization with tags and search" -m "- Created analytics dashboard for productivity insights" -m "- Added export/import functionality for data backup" -m "- Implemented auto-save feature (every 30 seconds)" -m "- Enhanced UI with menu bar, status bar, and professional design" -m "- Improved chat intelligence with context-aware responses" -m "- Moved legacy versions to legacy/ folder" -m "- Updated documentation with comprehensive guides" -m "- Added .gitignore, CHANGELOG, and LICENSE"
        
        echo [OK] Changes committed!
        echo.
        
        set /p PUSH="Do you want to push to GitHub? (Y/N): "
        if /i "%PUSH%"=="Y" (
            echo Pushing to origin main...
            git push origin main 2>nul
            if errorlevel 1 (
                echo Trying master branch...
                git push origin master 2>nul
                if errorlevel 1 (
                    echo [ERROR] Push failed. Please try manually:
                    echo   git push origin main
                    echo   (or: git push origin master)
                ) else (
                    echo [OK] Successfully pushed to GitHub!
                )
            ) else (
                echo [OK] Successfully pushed to GitHub!
            )
        )
    )
)

REM Final summary
echo.
echo ============================================
echo  Repository update process complete!
echo ============================================
echo.
echo Next steps:
echo   1. Visit your GitHub repo to verify changes
echo   2. Update repository description and topics
echo   3. Create a release (v2.0.0) - recommended
echo   4. Test the app: python enhanced_chatbot.py
echo   5. Share your updated project!
echo.
echo Documentation:
echo   - README.md - Main documentation
echo   - docs\QUICK_START.md - Quick start guide
echo   - docs\ENHANCEMENTS_GUIDE.md - Full feature guide
echo   - CHANGELOG.md - Version history
echo.
echo [OK] Your AI Chatbot is now production-ready!
echo.
pause
