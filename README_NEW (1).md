# AI Project Assistant Pro 🤖

[![GitHub](https://img.shields.io/badge/GitHub-Project-blue)](https://github.com/Khan-Feroz211/AI-CHATBOT)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Web](https://img.shields.io/badge/Web-Live-success)](https://khan-feroz211.github.io/AI-CHATBOT/)

A comprehensive AI-powered project management assistant with **dual interfaces** - web and desktop. Features include task management, smart notes, file handling, AI integration, and **guest mode** for instant access.

## 🌟 Features

### 🎯 Core Features
- ✅ **Dual Interface** - Web app + Desktop application
- 👥 **Guest Mode** - Instant access, no registration required
- 👤 **User Accounts** - Permanent data storage with authentication
- 📋 **Task Management** - Create, organize, and track tasks with priorities
- 📝 **Smart Notes** - Rich text notes with tags and search
- 📎 **File Management** - Upload and attach files to tasks/notes
- 🤖 **AI Integration** - OpenAI GPT & Anthropic Claude support
- 📊 **Analytics** - Visual progress tracking and statistics
- 📤 **Export** - PDF and Markdown export capabilities

### 🎮 Guest Mode Highlights
- **One-click access** - Start using immediately
- **Full features** - All premium features available
- **No commitment** - Try before creating an account
- **Easy upgrade** - Convert to permanent account anytime
- **Data transfer** - Keep your work when upgrading

## 🚀 Quick Start

### 🌐 Web Version (Recommended for Quick Try)

**No installation needed!**

Visit: **[https://khan-feroz211.github.io/AI-CHATBOT/](https://khan-feroz211.github.io/AI-CHATBOT/)**

### 💻 Desktop Version (Full Featured)

#### Prerequisites
- Python 3.8 or higher
- pip package manager

#### Installation

```powershell
# Clone the repository
git clone https://github.com/Khan-Feroz211/AI-CHATBOT.git
cd AI-CHATBOT

# Navigate to desktop app
cd desktop

# Install dependencies
pip install -r requirements.txt

# Run the application
python enhanced_chatbot_pro.py
```

#### First Launch Options

When you launch the desktop app, you'll see three options:

1. **🎮 Start as Guest** ⭐ (Recommended for first-time users)
   - Instant access
   - Full features
   - No registration

2. **🔑 Login**
   - For returning users
   - Access saved data

3. **📝 Register**
   - Create permanent account
   - Secure data storage

## 📁 Project Structure

```
project-assistant-bot/
│
├── web/                        # Web Version (HTML/CSS/JS)
│   ├── index.html             # Main web interface
│   ├── css/                   # Stylesheets
│   ├── js/                    # JavaScript files
│   └── assets/                # Images and resources
│
├── desktop/                    # Desktop Application (Python)
│   ├── enhanced_chatbot_pro.py   # Main application file
│   ├── enhanced_chatbot.py       # Legacy version
│   ├── requirements.txt          # Python dependencies
│   │
│   ├── auth/                  # Authentication (modular)
│   ├── database/              # Database operations
│   ├── gui/                   # GUI components
│   ├── ai/                    # AI backend integrations
│   └── utils/                 # Utility functions
│
├── chatbot_data/              # User data and database
│   ├── chatbot.db            # SQLite database
│   └── uploads/              # Uploaded files
│
├── docs/                      # Documentation
│   ├── QUICK_START.md        # Quick start guide
│   ├── CHANGELOG.md          # Version history
│   ├── CONTRIBUTING.md       # Contribution guidelines
│   └── guides/               # Detailed guides
│
├── scripts/                   # Utility scripts
│   ├── reorganize.ps1        # Structure reorganization
│   ├── update_repo.bat       # Repository update (Windows)
│   └── update_repo.sh        # Repository update (Unix)
│
└── legacy/                    # Legacy versions
    └── chatbot_demo_light.py
```

## 📚 Documentation

### Getting Started
- 📖 [Quick Start Guide](docs/QUICK_START.md) - Get up and running
- 🎯 [Guest Mode Guide](docs/guides/GUEST_MODE.md) - Using without registration
- 🤖 [AI Setup Guide](docs/guides/AI_SETUP.md) - Configure AI backends

### Advanced
- 🏗️ [Architecture](docs/ARCHITECTURE.md) - System design and structure
- 🔧 [API Guide](docs/guides/API_GUIDE.md) - Integration and API usage
- 🚀 [Deployment Guide](docs/guides/DEPLOYMENT.md) - Deploy your own instance

### Reference
- 📝 [Changelog](docs/CHANGELOG.md) - Version history and updates
- 🤝 [Contributing](docs/CONTRIBUTING.md) - How to contribute
- 🔒 [Security](docs/SECURITY.md) - Security policies

## 🎯 Usage

### Desktop Application

#### Task Management
```python
# Add tasks via chat
"Add a task: Complete project documentation"

# Or use the Tasks tab
1. Click "➕ Add Task"
2. Enter description
3. Set priority (High/Medium/Low)
4. Choose category
5. Click "Save"
```

#### Notes
```python
# Create notes with tags
1. Go to Notes tab
2. Click "➕ Add Note"
3. Enter title and content
4. Add tags (comma-separated)
5. Click "Save"

# Search notes
- Use search box to find by title, content, or tags
```

#### AI Chat
```python
# Configure AI backend
1. Click "⚙️ AI Settings"
2. Choose provider: Local / OpenAI / Anthropic
3. Enter API key (if using external provider)
4. Click "Save"

# Chat with AI
- Ask questions: "What should I work on today?"
- Get suggestions: "Help me organize my tasks"
- Analyze progress: "Show my productivity stats"
```

#### File Management
```python
# Upload files
1. Go to Files tab
2. Click "📁 Choose File"
3. Select file
4. File is stored and can be attached to tasks/notes
```

### Guest Mode to Registered User

#### Upgrade Process
```python
# When using guest account
1. Click "⭐ Upgrade" button in header
   OR
2. Go to File → "⭐ Create Permanent Account"

# Fill in details
3. Choose username
4. Set password (min 6 characters)
5. Enter email (optional)
6. Click "Create Account"

# All your data is automatically transferred! 🎉
```

## 🔧 Configuration

### Desktop App Settings

#### AI Backend Configuration
- **Local** - Basic responses, no API key needed
- **OpenAI** - Requires API key from [platform.openai.com](https://platform.openai.com)
  - Models: gpt-4, gpt-3.5-turbo
- **Anthropic** - Requires API key from [console.anthropic.com](https://console.anthropic.com)
  - Models: claude-3-sonnet, claude-3-opus

#### Database
- Location: `chatbot_data/chatbot.db`
- Type: SQLite
- Backup: Use Tools → Cleanup Database

#### File Uploads
- Location: `chatbot_data/uploads/`
- Supported types: All file types
- Size limit: System dependent

## 📦 Dependencies

### Desktop Application
```
# Core (required)
tkinter (included with Python)
sqlite3 (included with Python)

# Optional (enhanced features)
reportlab>=3.6.0    # PDF export
openai>=1.0.0       # OpenAI integration
anthropic>=0.8.0    # Anthropic integration
```

### Web Application
- No dependencies
- Runs in any modern browser
- Requires JavaScript enabled

## 🛠️ Development

### Project Reorganization

To reorganize the project structure:

```powershell
# Run the reorganization script
.\scripts\reorganize.ps1

# This will:
# - Create modular directory structure
# - Move files to appropriate locations
# - Clean up duplicates
# - Create backup
```

### Code Extraction

To split `enhanced_chatbot_pro.py` into modules:

```powershell
# See detailed instructions in:
.\docs\REORGANIZATION_PLAN.md

# Key modules to extract:
# - auth/user_auth.py       (Authentication)
# - database/db_manager.py  (Database operations)
# - gui/app.py             (Main application)
# - gui/theme.py           (UI theme)
# - gui/tabs/*.py          (Individual tabs)
```

### Testing

```powershell
# Test desktop app
cd desktop
python enhanced_chatbot_pro.py

# Test guest mode
1. Launch app
2. Click "🎮 Start as Guest"
3. Verify all features work

# Test upgrade flow
1. Use guest account
2. Create tasks/notes
3. Click "⭐ Upgrade"
4. Verify data transferred
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Quick Contribution Steps
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Python** - Core language
- **Tkinter** - Desktop UI framework
- **SQLite** - Database engine
- **OpenAI** - AI integration
- **Anthropic** - Claude AI integration
- **ReportLab** - PDF generation

## 📧 Support

- 🐛 **Issues:** [GitHub Issues](https://github.com/Khan-Feroz211/AI-CHATBOT/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Khan-Feroz211/AI-CHATBOT/discussions)
- 📧 **Email:** Create an issue for support

## 🗺️ Roadmap

### Completed ✅
- [x] User authentication system
- [x] Guest mode implementation
- [x] Task management
- [x] Notes system
- [x] File uploads
- [x] AI integration (OpenAI, Anthropic)
- [x] Export to PDF/Markdown
- [x] Analytics dashboard

### In Progress 🚧
- [ ] Modular code structure
- [ ] Comprehensive testing
- [ ] Enhanced documentation
- [ ] Performance optimizations

### Planned 📋
- [ ] Cloud sync option
- [ ] Mobile app companion
- [ ] Collaborative features
- [ ] Plugin system
- [ ] Multi-language support
- [ ] Dark mode
- [ ] Calendar integration

## 📊 Statistics

- **Lines of Code:** ~2000+
- **Files:** 20+
- **Features:** 15+
- **Supported Platforms:** Windows, macOS, Linux
- **Web Support:** All modern browsers

## 🔗 Links

- 🌐 **Live Demo:** [https://khan-feroz211.github.io/AI-CHATBOT/](https://khan-feroz211.github.io/AI-CHATBOT/)
- 📦 **GitHub:** [https://github.com/Khan-Feroz211/AI-CHATBOT](https://github.com/Khan-Feroz211/AI-CHATBOT)
- 📚 **Documentation:** [docs/](docs/)

---

**Made with ❤️ by Khan-Feroz211**

**Version:** 2.1 | **Last Updated:** 2024
