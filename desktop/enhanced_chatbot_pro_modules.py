"""
AI Backend and Utility Modules for Enhanced Chatbot Pro
This file provides AIBackend, FileManager, and ExportManager classes
"""

class AIBackend:
    """Handle AI backend providers (Local, OpenAI, Anthropic)"""
    
    def __init__(self):
        self.provider = "local"
        self.api_key = None
        self.model = None
    
    def set_provider(self, provider, api_key=None, model=None):
        """Set AI provider and credentials"""
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model
    
    def generate_response(self, message, conversation_history=None):
        """Generate AI response based on provider"""
        
        if self.provider == "local":
            return self._local_response(message)
        elif self.provider == "openai":
            return self._openai_response(message, conversation_history)
        elif self.provider == "anthropic":
            return self._anthropic_response(message, conversation_history)
        else:
            return "❌ Unknown AI provider. Please configure in Settings."
    
    def _local_response(self, message):
        """Generate local rule-based responses"""
        message_lower = message.lower()
        
        # Help commands
        if 'help' in message_lower:
            return """🤖 **AI Assistant Help**
            
Available commands:
- 'help' - Show this help message
- 'add a task: [description]' - Create a new task
- 'what's my progress?' - Show task statistics
- 'clear chat' - Clear conversation history

Features:
📋 Tasks - Manage your to-do list
📝 Notes - Create and organize notes
📎 Files - Upload and attach files
📊 Analytics - View your productivity stats
📤 Export - Save data to PDF or Markdown

💡 Tip: Use the tabs above to access different features!"""
        
        # Task-related
        if 'add' in message_lower and 'task' in message_lower:
            task_text = message.split(':', 1)[1].strip() if ':' in message else "New Task"
            return f"✅ I'll help you add the task: '{task_text}'\n\nPlease use the Tasks tab or I can guide you through it!"
        
        if 'progress' in message_lower or 'status' in message_lower:
            return """📊 **Your Progress**
            
To see your complete progress:
1. Go to the Analytics tab
2. Check the Tasks tab for detailed task status
3. Use the status bar at the bottom for quick stats

💡 Tip: I can provide more detailed analysis if you configure an AI backend (OpenAI or Anthropic) in Settings!"""
        
        # Note-related
        if 'note' in message_lower:
            return """📝 **Notes Feature**
            
Create and manage notes:
1. Go to the Notes tab
2. Click '➕ Add Note'
3. Add title, content, and tags
4. Use search to find notes later

💡 Notes support rich text and organization with tags!"""
        
        # General questions
        greetings = ['hello', 'hi', 'hey', 'greetings']
        if any(greeting in message_lower for greeting in greetings):
            return """👋 **Hello! I'm your AI Project Assistant!**

I can help you with:
- 📋 Managing tasks and to-dos
- 📝 Creating and organizing notes
- 📎 Handling file uploads
- 📊 Tracking your productivity
- 💡 Getting things done efficiently

What would you like to work on today?

💡 Type 'help' to see all available commands!"""
        
        # Default response
        return f"""I received your message: "{message}"

🤖 **Local AI Mode**: I'm using basic responses. For smarter AI:
1. Click '⚙️ AI Settings'
2. Choose OpenAI or Anthropic
3. Add your API key

💡 Type 'help' for available commands!"""
    
    def _openai_response(self, message, conversation_history):
        """Generate response using OpenAI"""
        try:
            import openai
            
            if not self.api_key:
                return "❌ OpenAI API key not configured. Please add it in Settings."
            
            openai.api_key = self.api_key
            
            # Prepare messages
            messages = []
            if conversation_history:
                for msg in conversation_history[-10:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            messages.append({"role": "user", "content": message})
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model or "gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            return "❌ OpenAI library not installed. Install with: pip install openai"
        except Exception as e:
            return f"❌ OpenAI Error: {str(e)}\n\n💡 Check your API key in Settings."
    
    def _anthropic_response(self, message, conversation_history):
        """Generate response using Anthropic Claude"""
        try:
            import anthropic
            
            if not self.api_key:
                return "❌ Anthropic API key not configured. Please add it in Settings."
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Prepare messages
            messages = []
            if conversation_history:
                for msg in conversation_history[-10:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            messages.append({"role": "user", "content": message})
            
            # Call Anthropic API
            response = client.messages.create(
                model=self.model or "claude-3-sonnet-20240229",
                max_tokens=500,
                messages=messages
            )
            
            return response.content[0].text
            
        except ImportError:
            return "❌ Anthropic library not installed. Install with: pip install anthropic"
        except Exception as e:
            return f"❌ Anthropic Error: {str(e)}\n\n💡 Check your API key in Settings."


class FileManager:
    """Handle file uploads and management"""
    
    def __init__(self, db_path, data_dir):
        self.db_path = db_path
        self.data_dir = data_dir
        self.uploads_dir = data_dir / "uploads"
        self.uploads_dir.mkdir(exist_ok=True)
    
    def upload_file(self, file_path, user_id=None, task_id=None, note_id=None):
        """Upload a file and store metadata"""
        import shutil
        import os
        from datetime import datetime
        import sqlite3
        from pathlib import Path
        
        try:
            # Get file info
            file_path_obj = Path(file_path)
            original_name = file_path_obj.name
            file_size = file_path_obj.stat().st_size
            file_type = file_path_obj.suffix
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_name = f"{timestamp}_{original_name}"
            dest_path = self.uploads_dir / unique_name
            
            # Copy file
            shutil.copy2(file_path, dest_path)
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO files (filename, original_name, file_path, file_type, file_size, 
                                   uploaded_date, user_id, task_id, note_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (unique_name, original_name, str(dest_path), file_type, file_size,
                  datetime.now().isoformat(), user_id, task_id, note_id))
            
            file_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return True, file_id, f"✅ File uploaded successfully: {original_name}"
            
        except Exception as e:
            return False, None, f"❌ Upload failed: {str(e)}"


class ExportManager:
    """Handle data export to various formats"""
    
    def __init__(self, tasks, notes):
        self.tasks = tasks
        self.notes = notes
    
    def export_to_pdf(self, filename):
        """Export data to PDF"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from datetime import datetime
            
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph("AI Project Assistant - Export", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Date
            date_text = f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            story.append(Paragraph(date_text, styles['Normal']))
            story.append(Spacer(1, 24))
            
            # Tasks
            story.append(Paragraph("Tasks", styles['Heading1']))
            for task in self.tasks:
                status = "✓" if task['completed'] else "○"
                text = f"{status} {task['text']} (Priority: {task.get('priority', 'medium')})"
                story.append(Paragraph(text, styles['Normal']))
                story.append(Spacer(1, 6))
            
            story.append(Spacer(1, 24))
            
            # Notes
            story.append(Paragraph("Notes", styles['Heading1']))
            for note in self.notes:
                story.append(Paragraph(note['title'], styles['Heading2']))
                story.append(Paragraph(note['content'], styles['Normal']))
                story.append(Spacer(1, 12))
            
            doc.build(story)
            return True, f"✅ Exported to PDF: {filename}"
            
        except ImportError:
            return False, "❌ PDF export requires reportlab. Install with: pip install reportlab"
        except Exception as e:
            return False, f"❌ Export failed: {str(e)}"
    
    def export_to_markdown(self, filename):
        """Export data to Markdown"""
        try:
            from datetime import datetime
            
            with open(filename, 'w', encoding='utf-8') as f:
                # Header
                f.write("# AI Project Assistant - Export\n\n")
                f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                f.write("---\n\n")
                
                # Tasks
                f.write("## 📋 Tasks\n\n")
                for task in self.tasks:
                    status = "- [x]" if task['completed'] else "- [ ]"
                    priority = task.get('priority', 'medium')
                    f.write(f"{status} {task['text']} `{priority}`\n")
                
                f.write("\n---\n\n")
                
                # Notes
                f.write("## 📝 Notes\n\n")
                for note in self.notes:
                    f.write(f"### {note['title']}\n\n")
                    f.write(f"{note['content']}\n\n")
                    if note.get('tags'):
                        f.write(f"*Tags: {note['tags']}*\n\n")
            
            return True, f"✅ Exported to Markdown: {filename}"
            
        except Exception as e:
            return False, f"❌ Export failed: {str(e)}"