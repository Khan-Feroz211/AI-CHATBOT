# AI Project Assistant Pro

A powerful AI-powered task management and productivity tool.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Khan-Feroz211/AI-CHATBOT.git
cd AI-CHATBOT

# Install dependencies
pip install -r requirements.txt

# Run database migration (first time only)
python migrate_database.py

# Start the desktop app
python enhanced_chatbot_pro.py

# Or run the web version
cd web
python -m http.server 8000
# Visit: http://localhost:8000
```

## Windows PowerShell (Path With Spaces)

If your folder path has spaces (for example `C:\Users\Feroz Khan\...`), quote it:

```powershell
Set-Location "C:\Users\Feroz Khan\project-assistant-bot"
python -m http.server 8000 --directory web
```

Visit: `http://127.0.0.1:8000`

## Features

- Task management with priorities
- Smart note-taking with tags
- AI chat assistant (OpenAI/Anthropic)
- Guest mode (no registration needed)
- Analytics dashboard
- Export to PDF/Markdown
- Secure user authentication

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## License

MIT License - see `LICENSE`
