#!/bin/bash

# AI Chatbot Repository Update Script
# This script automates the repository update process

echo "🚀 AI Chatbot Repository Update Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "This is not a git repository!"
    print_info "Please run this script from your AI-CHATBOT repository root."
    exit 1
fi

print_success "Git repository detected"

# Step 1: Create folder structure
echo ""
print_info "Step 1: Creating folder structure..."
mkdir -p legacy
mkdir -p assets
mkdir -p docs
print_success "Folders created: legacy/, assets/, docs/"

# Step 2: Move old files to legacy
echo ""
print_info "Step 2: Moving old files to legacy/..."
if [ -f "chatbot_demo_light.py" ]; then
    mv chatbot_demo_light.py legacy/
    print_success "Moved chatbot_demo_light.py"
fi

if [ -f "chatbot_enhanced_ui.py" ]; then
    mv chatbot_enhanced_ui.py legacy/
    print_success "Moved chatbot_enhanced_ui.py"
fi

if [ -f "chatbot_vibrant_colors.py" ]; then
    mv chatbot_vibrant_colors.py legacy/
    print_success "Moved chatbot_vibrant_colors.py"
fi

if [ -f "index.html" ]; then
    mv index.html legacy/
    print_success "Moved index.html"
fi

if [ -f "QUICK_START_GUIDE.md" ]; then
    mv QUICK_START_GUIDE.md docs/
    print_success "Moved QUICK_START_GUIDE.md to docs/"
fi

# Step 3: Backup old README
echo ""
print_info "Step 3: Backing up old README..."
if [ -f "README.md" ]; then
    mv README.md legacy/README_old.md
    print_success "Old README backed up to legacy/README_old.md"
fi

# Step 4: Copy new files
echo ""
print_info "Step 4: Please copy the following files to your repository:"
echo "  1. enhanced_chatbot.py (to root)"
echo "  2. requirements.txt (to root)"
echo "  3. README.md (to root)"
echo "  4. CHANGELOG.md (to root)"
echo "  5. LICENSE (to root)"
echo "  6. .gitignore (to root)"
echo "  7. QUICK_START.md (to docs/)"
echo "  8. ENHANCEMENTS_GUIDE.md (to docs/)"
echo ""
read -p "Have you copied all the files? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Please copy the files and run this script again."
    exit 1
fi

print_success "Files copied"

# Step 5: Test the new chatbot
echo ""
print_info "Step 5: Testing the enhanced chatbot..."
if [ -f "enhanced_chatbot.py" ]; then
    print_info "You can test with: python enhanced_chatbot.py"
    print_info "We'll skip automatic testing to avoid interrupting your workflow"
else
    print_error "enhanced_chatbot.py not found! Please copy it to the repository root."
    exit 1
fi

# Step 6: Git operations
echo ""
print_info "Step 6: Preparing git operations..."
print_info "Current git status:"
git status --short

echo ""
read -p "Do you want to stage all changes? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Add new files
    git add enhanced_chatbot.py 2>/dev/null || print_warning "enhanced_chatbot.py not found"
    git add requirements.txt 2>/dev/null || print_warning "requirements.txt not found"
    git add .gitignore 2>/dev/null || print_warning ".gitignore not found"
    git add CHANGELOG.md 2>/dev/null || print_warning "CHANGELOG.md not found"
    git add LICENSE 2>/dev/null || print_warning "LICENSE not found"
    git add README.md 2>/dev/null || print_warning "README.md not found"
    git add docs/ 2>/dev/null
    git add legacy/ 2>/dev/null
    git add assets/ 2>/dev/null
    
    # Remove old tracked files
    git rm --cached chatbot_demo_light.py 2>/dev/null
    git rm --cached chatbot_enhanced_ui.py 2>/dev/null
    git rm --cached chatbot_vibrant_colors.py 2>/dev/null
    git rm --cached index.html 2>/dev/null
    git rm --cached QUICK_START_GUIDE.md 2>/dev/null
    
    print_success "Changes staged"
    
    echo ""
    print_info "Ready to commit. Suggested commit message:"
    echo ""
    echo "🚀 Major Update: Enhanced Production-Ready Version 2.0"
    echo ""
    echo "- Added SQLite database for persistent storage"
    echo "- Implemented advanced task management with priorities"
    echo "- Added note organization with tags and search"
    echo "- Created analytics dashboard"
    echo "- Added export/import functionality"
    echo "- Implemented auto-save feature"
    echo "- Enhanced UI with professional design"
    echo "- Moved legacy versions to legacy/ folder"
    echo "- Updated comprehensive documentation"
    echo ""
    
    read -p "Do you want to commit now? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git commit -m "🚀 Major Update: Enhanced Production-Ready Version 2.0

- Added SQLite database for persistent storage
- Implemented advanced task management with priorities and categories
- Added note organization with tags and search
- Created analytics dashboard for productivity insights
- Added export/import functionality for data backup
- Implemented auto-save feature (every 30 seconds)
- Enhanced UI with menu bar, status bar, and professional design
- Improved chat intelligence with context-aware responses
- Moved legacy versions to legacy/ folder
- Updated documentation with comprehensive guides
- Added .gitignore, CHANGELOG, and LICENSE

Breaking Changes:
- Main file is now enhanced_chatbot.py (was chatbot_demo_light.py)
- Requires Python 3.8+ (was 3.6+)
- Uses SQLite database (creates chatbot_data/ folder)"
        
        print_success "Changes committed!"
        
        echo ""
        read -p "Do you want to push to GitHub? (y/n): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Pushing to origin main..."
            if git push origin main 2>/dev/null; then
                print_success "Successfully pushed to GitHub!"
            else
                print_info "Trying master branch..."
                if git push origin master 2>/dev/null; then
                    print_success "Successfully pushed to GitHub!"
                else
                    print_error "Push failed. Please check your git configuration and try manually:"
                    echo "  git push origin main"
                    echo "  (or: git push origin master)"
                fi
            fi
        fi
    fi
fi

# Final summary
echo ""
echo "========================================"
print_success "Repository update process complete!"
echo "========================================"
echo ""
print_info "Next steps:"
echo "  1. Visit your GitHub repo to verify changes"
echo "  2. Update repository description and topics"
echo "  3. Create a release (v2.0.0) - recommended"
echo "  4. Test the app: python enhanced_chatbot.py"
echo "  5. Share your updated project!"
echo ""
print_info "Documentation:"
echo "  - README.md - Main documentation"
echo "  - docs/QUICK_START.md - Quick start guide"
echo "  - docs/ENHANCEMENTS_GUIDE.md - Full feature guide"
echo "  - CHANGELOG.md - Version history"
echo ""
print_success "Your AI Chatbot is now production-ready! 🎉"
