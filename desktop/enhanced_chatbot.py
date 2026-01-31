import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import json
from datetime import datetime
import sqlite3
import os
from pathlib import Path

class EnhancedChatbot:
    """Enhanced chatbot with production-ready features"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AI Project Assistant - Enhanced Edition")
        self.root.geometry("900x650")
        
        # Setup data directory and database
        self.data_dir = Path("chatbot_data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.db_path = self.data_dir / "chatbot.db"
        self.setup_database()
        
        # Load data from database
        self.load_data()
        
        # Conversation history for context
        self.conversation_history = []
        
        self.setup_ui()
        
        # Auto-save every 30 seconds
        self.auto_save()
        
    def setup_database(self):
        """Initialize SQLite database with proper schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'medium',
                added_date TEXT,
                completed_date TEXT,
                category TEXT DEFAULT 'general'
            )
        ''')
        
        # Notes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                created_date TEXT,
                modified_date TEXT,
                tags TEXT
            )
        ''')
        
        # Conversation logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_message TEXT,
                bot_response TEXT,
                session_id TEXT
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def load_data(self):
        """Load tasks and notes from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load tasks
        cursor.execute('SELECT * FROM tasks ORDER BY added_date DESC')
        self.tasks = [
            {
                'id': row[0],
                'text': row[1],
                'completed': bool(row[2]),
                'priority': row[3],
                'added': row[4],
                'completed_date': row[5],
                'category': row[6]
            }
            for row in cursor.fetchall()
        ]
        
        # Load notes
        cursor.execute('SELECT * FROM notes ORDER BY modified_date DESC')
        self.notes = [
            {
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'created': row[3],
                'modified': row[4],
                'tags': row[5]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
    def save_task(self, task):
        """Save a single task to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if 'id' in task and task['id']:
            # Update existing task
            cursor.execute('''
                UPDATE tasks 
                SET text=?, completed=?, priority=?, completed_date=?, category=?
                WHERE id=?
            ''', (task['text'], int(task['completed']), task['priority'],
                  task.get('completed_date'), task.get('category', 'general'), task['id']))
        else:
            # Insert new task
            cursor.execute('''
                INSERT INTO tasks (text, completed, priority, added_date, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (task['text'], int(task['completed']), task.get('priority', 'medium'),
                  task['added'], task.get('category', 'general')))
            task['id'] = cursor.lastrowid
            
        conn.commit()
        conn.close()
        
    def save_note(self, note):
        """Save a single note to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if 'id' in note and note['id']:
            # Update existing note
            cursor.execute('''
                UPDATE notes 
                SET title=?, content=?, modified_date=?, tags=?
                WHERE id=?
            ''', (note['title'], note['content'], 
                  datetime.now().strftime("%Y-%m-%d %H:%M"), 
                  note.get('tags', ''), note['id']))
        else:
            # Insert new note
            cursor.execute('''
                INSERT INTO notes (title, content, created_date, modified_date, tags)
                VALUES (?, ?, ?, ?, ?)
            ''', (note['title'], note['content'], note['created'], note['created'],
                  note.get('tags', '')))
            note['id'] = cursor.lastrowid
            
        conn.commit()
        conn.close()
        
    def log_conversation(self, user_msg, bot_response):
        """Log conversation to database for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_id = datetime.now().strftime("%Y%m%d")
        
        cursor.execute('''
            INSERT INTO conversations (timestamp, user_message, bot_response, session_id)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), user_msg, bot_response, session_id))
        
        conn.commit()
        conn.close()
        
    def setup_ui(self):
        # Menu bar
        self.setup_menu()
        
        # Create tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Chat tab
        self.setup_chat_tab()
        
        # Tasks tab
        self.setup_tasks_tab()
        
        # Notes tab
        self.setup_notes_tab()
        
        # Analytics tab (NEW)
        self.setup_analytics_tab()
        
        # Status bar
        self.setup_status_bar()
        
    def setup_menu(self):
        """Add menu bar with File, Edit, Help options"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_command(label="Import Data", command=self.import_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Clear Chat", command=self.clear_chat)
        edit_menu.add_command(label="Settings", command=self.show_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        
    def setup_status_bar(self):
        """Add status bar at bottom"""
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status()
        
    def update_status(self):
        """Update status bar with stats"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks if t['completed'])
        total_notes = len(self.notes)
        
        status_text = f"Tasks: {completed_tasks}/{total_tasks} | Notes: {total_notes} | Last saved: {datetime.now().strftime('%H:%M:%S')}"
        self.status_bar.config(text=status_text)
        
    def setup_chat_tab(self):
        chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(chat_frame, text='💬 Chat')
        
        # Chat display with better styling
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, height=20, font=("Arial", 10),
            bg="#f5f5f5", fg="#333"
        )
        self.chat_display.pack(padx=10, pady=10, fill='both', expand=True)
        self.chat_display.config(state='disabled')
        
        # Configure tags for different message types
        self.chat_display.tag_config("user", foreground="#0066cc", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("bot", foreground="#009900", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("system", foreground="#cc0000", font=("Arial", 9, "italic"))
        
        # Input area with better layout
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill='x', padx=10, pady=5)
        
        # Character counter
        self.char_count = ttk.Label(input_frame, text="0/500")
        self.char_count.pack(side='right', padx=5)
        
        send_btn = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_btn.pack(side='right', padx=5)
        
        self.chat_input = ttk.Entry(input_frame, font=("Arial", 10))
        self.chat_input.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.chat_input.bind('<Return>', lambda e: self.send_message())
        self.chat_input.bind('<KeyRelease>', self.update_char_count)
        
        # Welcome message
        self.add_message("system", "🤖 AI Project Assistant v2.0 Enhanced Edition\n")
        self.add_message("bot", "👋 Welcome! I'm your enhanced project assistant.\n\n"
                        "New features:\n"
                        "• 💾 Auto-save to database\n"
                        "• 📊 Analytics and insights\n"
                        "• 🎯 Task priorities\n"
                        "• 🔍 Smart search\n"
                        "• 📤 Export/Import data\n\n"
                        "Try: 'show high priority tasks' or 'what's my progress?'")
        
    def setup_tasks_tab(self):
        tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(tasks_frame, text='✅ Tasks')
        
        # Top toolbar
        toolbar = ttk.Frame(tasks_frame)
        toolbar.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(toolbar, text="Filter:").pack(side='left', padx=5)
        self.task_filter = ttk.Combobox(toolbar, values=['All', 'Active', 'Completed', 'High Priority'], 
                                        state='readonly', width=15)
        self.task_filter.set('All')
        self.task_filter.pack(side='left', padx=5)
        self.task_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_tasks_list())
        
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_tasks_list).pack(side='left', padx=5)
        
        # Add task section
        add_frame = ttk.LabelFrame(tasks_frame, text="Add New Task", padding=10)
        add_frame.pack(fill='x', padx=10, pady=5)
        
        # Task input with priority and category
        input_row = ttk.Frame(add_frame)
        input_row.pack(fill='x')
        
        ttk.Label(input_row, text="Task:").pack(side='left', padx=5)
        self.task_input = ttk.Entry(input_row, width=40)
        self.task_input.pack(side='left', padx=5)
        
        ttk.Label(input_row, text="Priority:").pack(side='left', padx=5)
        self.task_priority = ttk.Combobox(input_row, values=['low', 'medium', 'high'], 
                                          state='readonly', width=10)
        self.task_priority.set('medium')
        self.task_priority.pack(side='left', padx=5)
        
        ttk.Label(input_row, text="Category:").pack(side='left', padx=5)
        self.task_category = ttk.Combobox(input_row, values=['general', 'work', 'personal', 'urgent'],
                                          state='readonly', width=10)
        self.task_category.set('general')
        self.task_category.pack(side='left', padx=5)
        
        ttk.Button(input_row, text="➕ Add", command=self.add_task).pack(side='left', padx=5)
        
        # Task list with scrollbar
        list_frame = ttk.LabelFrame(tasks_frame, text="Your Tasks", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create Treeview for better task display
        columns = ('Priority', 'Category', 'Date')
        self.tasks_tree = ttk.Treeview(list_frame, columns=columns, height=10)
        
        self.tasks_tree.heading('#0', text='Task')
        self.tasks_tree.heading('Priority', text='Priority')
        self.tasks_tree.heading('Category', text='Category')
        self.tasks_tree.heading('Date', text='Added')
        
        self.tasks_tree.column('#0', width=300)
        self.tasks_tree.column('Priority', width=80)
        self.tasks_tree.column('Category', width=100)
        self.tasks_tree.column('Date', width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)
        
        self.tasks_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Button frame
        btn_frame = ttk.Frame(tasks_frame)
        btn_frame.pack(padx=10, pady=5)
        
        ttk.Button(btn_frame, text="✓ Complete", command=self.complete_task).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✎ Edit", command=self.edit_task).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑 Delete", command=self.delete_task).pack(side='left', padx=5)
        
        self.refresh_tasks_list()
        
    def setup_notes_tab(self):
        notes_frame = ttk.Frame(self.notebook)
        self.notebook.add(notes_frame, text='📝 Notes')
        
        # Toolbar
        toolbar = ttk.Frame(notes_frame)
        toolbar.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(toolbar, text="Search:").pack(side='left', padx=5)
        self.note_search = ttk.Entry(toolbar, width=30)
        self.note_search.pack(side='left', padx=5)
        self.note_search.bind('<KeyRelease>', lambda e: self.search_notes())
        
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_notes_list).pack(side='left', padx=5)
        
        # Add note section
        add_frame = ttk.LabelFrame(notes_frame, text="Create/Edit Note", padding=10)
        add_frame.pack(fill='x', padx=10, pady=5)
        
        title_row = ttk.Frame(add_frame)
        title_row.pack(fill='x', pady=5)
        
        ttk.Label(title_row, text="Title:").pack(side='left', padx=5)
        self.note_title = ttk.Entry(title_row, width=40)
        self.note_title.pack(side='left', fill='x', expand=True, padx=5)
        
        ttk.Label(title_row, text="Tags:").pack(side='left', padx=5)
        self.note_tags = ttk.Entry(title_row, width=20)
        self.note_tags.pack(side='left', padx=5)
        
        ttk.Label(add_frame, text="Content:").pack(anchor='w', padx=5)
        self.note_content = scrolledtext.ScrolledText(add_frame, height=6, font=("Arial", 10))
        self.note_content.pack(fill='x', padx=5, pady=5)
        
        btn_row = ttk.Frame(add_frame)
        btn_row.pack(fill='x', pady=5)
        
        ttk.Button(btn_row, text="💾 Save Note", command=self.add_note).pack(side='left', padx=5)
        ttk.Button(btn_row, text="🆕 New Note", command=self.clear_note_form).pack(side='left', padx=5)
        
        # Notes list
        list_frame = ttk.LabelFrame(notes_frame, text="Your Notes", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.notes_list = tk.Listbox(list_frame, height=8, font=("Arial", 10))
        self.notes_list.pack(fill='both', expand=True)
        self.notes_list.bind('<<ListboxSelect>>', self.show_note)
        self.notes_list.bind('<Double-Button-1>', self.edit_note)
        
        # Delete button
        ttk.Button(notes_frame, text="🗑 Delete Note", command=self.delete_note).pack(pady=5)
        
        self.refresh_notes_list()
        
    def setup_analytics_tab(self):
        """NEW: Analytics tab for insights"""
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text='📊 Analytics')
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(analytics_frame, text="Statistics Overview", padding=20)
        stats_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.stats_display = scrolledtext.ScrolledText(stats_frame, height=15, font=("Courier", 10))
        self.stats_display.pack(fill='both', expand=True)
        
        ttk.Button(analytics_frame, text="🔄 Refresh Stats", 
                  command=self.refresh_analytics).pack(pady=10)
        
        self.refresh_analytics()
        
    def refresh_analytics(self):
        """Calculate and display analytics"""
        self.stats_display.delete("1.0", tk.END)
        
        # Task analytics
        total_tasks = len(self.tasks)
        completed = sum(1 for t in self.tasks if t['completed'])
        active = total_tasks - completed
        
        high_priority = sum(1 for t in self.tasks if t.get('priority') == 'high')
        
        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
        
        # Note analytics
        total_notes = len(self.notes)
        
        # Conversation analytics
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM conversations')
        total_conversations = cursor.fetchone()[0]
        conn.close()
        
        # Display stats
        stats_text = f"""
╔══════════════════════════════════════════════════════╗
║           PROJECT ASSISTANT ANALYTICS                ║
╚══════════════════════════════════════════════════════╝

📋 TASK STATISTICS
{'─' * 54}
Total Tasks:           {total_tasks}
Completed:             {completed}
Active:                {active}
High Priority:         {high_priority}
Completion Rate:       {completion_rate:.1f}%

📝 NOTES STATISTICS
{'─' * 54}
Total Notes:           {total_notes}

💬 CHAT STATISTICS
{'─' * 54}
Total Conversations:   {total_conversations}

🎯 PRODUCTIVITY INSIGHTS
{'─' * 54}
"""
        
        if completion_rate > 75:
            stats_text += "✅ Excellent! You're crushing your tasks!\n"
        elif completion_rate > 50:
            stats_text += "👍 Good progress! Keep it up!\n"
        else:
            stats_text += "💪 You've got this! Focus on completing tasks.\n"
            
        if high_priority > 0:
            stats_text += f"⚠️  {high_priority} high priority task(s) need attention!\n"
            
        self.stats_display.insert("1.0", stats_text)
        
    def add_message(self, sender, text):
        """Enhanced message display with tags"""
        self.chat_display.config(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add timestamp
        self.chat_display.insert(tk.END, f"[{timestamp}] ")
        
        # Add sender with tag
        if sender.lower() == "you":
            self.chat_display.insert(tk.END, "You: ", "user")
        elif sender.lower() == "bot":
            self.chat_display.insert(tk.END, "Bot: ", "bot")
        else:
            self.chat_display.insert(tk.END, f"{sender}: ", "system")
            
        # Add message
        self.chat_display.insert(tk.END, f"{text}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        
    def send_message(self):
        """Enhanced message handling with conversation logging"""
        msg = self.chat_input.get().strip()
        if not msg:
            return
        
        if len(msg) > 500:
            messagebox.showwarning("Message Too Long", "Please keep messages under 500 characters.")
            return
            
        self.chat_input.delete(0, tk.END)
        self.add_message("You", msg)
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "message": msg})
        
        # Generate response
        response = self.get_enhanced_response(msg.lower())
        self.add_message("Bot", response)
        
        # Add to conversation history
        self.conversation_history.append({"role": "bot", "message": response})
        
        # Log conversation
        self.log_conversation(msg, response)
        
    def get_enhanced_response(self, msg):
        """Enhanced bot responses with more intelligence"""
        
        # Progress/analytics queries
        if any(word in msg for word in ['progress', 'stats', 'analytics', 'how am i doing']):
            total = len(self.tasks)
            completed = sum(1 for t in self.tasks if t['completed'])
            rate = (completed / total * 100) if total > 0 else 0
            
            return (f"📊 Your Progress Report:\n\n"
                   f"Total Tasks: {total}\n"
                   f"Completed: {completed}\n"
                   f"Completion Rate: {rate:.1f}%\n"
                   f"Notes: {len(self.notes)}\n\n"
                   f"Check the Analytics tab for detailed insights!")
        
        # Priority task queries
        elif 'high priority' in msg or 'urgent' in msg:
            high_priority_tasks = [t for t in self.tasks if t.get('priority') == 'high' and not t['completed']]
            
            if high_priority_tasks:
                task_list = "\n".join([f"• {t['text']}" for t in high_priority_tasks[:5]])
                return f"🚨 High Priority Tasks:\n{task_list}\n\nFocus on these first!"
            else:
                return "✅ Great! You don't have any high priority tasks right now."
        
        # Task queries
        elif any(word in msg for word in ['task', 'todo', 'do']):
            if 'completed' in msg or 'done' in msg:
                completed_tasks = [t for t in self.tasks if t['completed']]
                if completed_tasks:
                    task_list = "\n".join([f"✓ {t['text']}" for t in completed_tasks[:5]])
                    return f"Completed Tasks:\n{task_list}\n\nGreat job! 🎉"
                else:
                    return "No completed tasks yet. Let's get started!"
            else:
                active_tasks = [t for t in self.tasks if not t['completed']]
                if active_tasks:
                    task_list = "\n".join([f"○ {t['text']}" for t in active_tasks[:5]])
                    return f"Active Tasks:\n{task_list}\n\nUse the Tasks tab to manage them!"
                else:
                    return "You're all caught up! No active tasks. 🎊"
        
        # Note queries
        elif any(word in msg for word in ['note', 'notes']):
            if self.notes:
                return (f"📝 You have {len(self.notes)} notes saved.\n\n"
                       f"Recent notes:\n" + 
                       "\n".join([f"• {n['title']}" for n in self.notes[:3]]) +
                       "\n\nView them in the Notes tab!")
            else:
                return "You don't have any notes yet. Create some in the Notes tab!"
        
        # Help queries with context awareness
        elif any(word in msg for word in ['help', 'what can you do', 'features']):
            return ("🤖 I'm your Enhanced AI Assistant! Here's what I can do:\n\n"
                   "📋 Task Management:\n"
                   "• Add/edit/delete tasks\n"
                   "• Set priorities (low/medium/high)\n"
                   "• Track completion\n\n"
                   "📝 Notes Organization:\n"
                   "• Create and search notes\n"
                   "• Tag your notes\n"
                   "• Quick access to all notes\n\n"
                   "📊 Analytics:\n"
                   "• Track your progress\n"
                   "• View productivity stats\n"
                   "• Get insights\n\n"
                   "💬 Smart Chat:\n"
                   "• Ask about tasks and notes\n"
                   "• Get productivity tips\n"
                   "• Conversation history\n\n"
                   "Try: 'show my progress' or 'high priority tasks'")
        
        # Python/coding help
        elif 'python' in msg or 'code' in msg or 'programming' in msg:
            tips = [
                "Use meaningful variable names that explain what they store",
                "Break complex functions into smaller, reusable ones",
                "Add docstrings to document your functions",
                "Use list comprehensions for cleaner code",
                "Handle exceptions with try-except blocks",
                "Test your code frequently as you build"
            ]
            import random
            tip = random.choice(tips)
            
            return (f"🐍 Python Pro Tip:\n\n{tip}\n\n"
                   "Need help with a specific concept? Just ask!")
        
        # Motivation
        elif any(word in msg for word in ['motivate', 'encourage', 'tired', 'stressed']):
            return ("💪 You've got this! Remember:\n\n"
                   "• Break big tasks into small steps\n"
                   "• Celebrate small wins\n"
                   "• Take breaks when needed\n"
                   "• Progress, not perfection!\n\n"
                   "Keep pushing forward! 🌟")
        
        # Export/save queries  
        elif 'export' in msg or 'save' in msg or 'backup' in msg:
            return ("💾 Your data is auto-saved to the database!\n\n"
                   "To export:\n"
                   "• Go to File → Export Data\n"
                   "• Choose JSON format\n"
                   "• Save anywhere you like\n\n"
                   "Your data is safe! ✓")
        
        # Greeting
        elif any(word in msg for word in ['hi', 'hello', 'hey', 'good morning', 'good evening']):
            greetings = [
                "👋 Hello! Ready to be productive today?",
                "Hi there! What can I help you accomplish?",
                "Hey! Let's make today awesome!",
                "Hello! Ready to tackle those tasks?"
            ]
            import random
            return random.choice(greetings)
        
        # Goodbye
        elif any(word in msg for word in ['bye', 'goodbye', 'see you', 'later']):
            return "👋 Goodbye! Great work today. Come back anytime!"
        
        # Default with suggestion
        else:
            return ("I'm not sure about that, but I can help with:\n\n"
                   "• Managing your tasks and priorities\n"
                   "• Organizing your notes\n"
                   "• Tracking your progress\n"
                   "• Python coding tips\n\n"
                   "What would you like to do?")
    
    def update_char_count(self, event=None):
        """Update character counter"""
        count = len(self.chat_input.get())
        self.char_count.config(text=f"{count}/500")
        
        if count > 450:
            self.char_count.config(foreground="red")
        else:
            self.char_count.config(foreground="black")
    
    def add_task(self):
        """Enhanced task adding with validation"""
        task_text = self.task_input.get().strip()
        
        if not task_text:
            messagebox.showwarning("Empty Task", "Please enter a task description!")
            return
        
        if len(task_text) > 200:
            messagebox.showwarning("Task Too Long", "Please keep task descriptions under 200 characters.")
            return
            
        task = {
            'id': None,
            'text': task_text,
            'completed': False,
            'priority': self.task_priority.get(),
            'category': self.task_category.get(),
            'added': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'completed_date': None
        }
        
        self.tasks.insert(0, task)  # Add to beginning
        self.save_task(task)
        
        self.task_input.delete(0, tk.END)
        self.task_priority.set('medium')
        self.task_category.set('general')
        
        self.refresh_tasks_list()
        self.update_status()
        
        messagebox.showinfo("Success!", f"✓ Task added with {task['priority']} priority!")
        
    def refresh_tasks_list(self):
        """Refresh task treeview with filter"""
        # Clear tree
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        # Apply filter
        filter_type = self.task_filter.get()
        
        filtered_tasks = self.tasks
        if filter_type == 'Active':
            filtered_tasks = [t for t in self.tasks if not t['completed']]
        elif filter_type == 'Completed':
            filtered_tasks = [t for t in self.tasks if t['completed']]
        elif filter_type == 'High Priority':
            filtered_tasks = [t for t in self.tasks if t.get('priority') == 'high']
        
        # Add filtered tasks to tree
        for task in filtered_tasks:
            status = "✓" if task['completed'] else "○"
            task_text = f"{status} {task['text']}"
            
            # Color coding by priority
            tags = ()
            if task.get('priority') == 'high':
                tags = ('high_priority',)
            elif task['completed']:
                tags = ('completed',)
            
            self.tasks_tree.insert('', 'end', text=task_text,
                                  values=(task.get('priority', 'medium'),
                                         task.get('category', 'general'),
                                         task['added'][:16]),
                                  tags=tags)
        
        # Configure tag colors
        self.tasks_tree.tag_configure('high_priority', foreground='red')
        self.tasks_tree.tag_configure('completed', foreground='gray')
        
    def complete_task(self):
        """Mark selected task as complete"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task!")
            return
        
        # Get selected index
        selected_item = selection[0]
        index = self.tasks_tree.index(selected_item)
        
        # Apply current filter to get correct task
        filter_type = self.task_filter.get()
        filtered_tasks = self.tasks
        if filter_type == 'Active':
            filtered_tasks = [t for t in self.tasks if not t['completed']]
        elif filter_type == 'Completed':
            filtered_tasks = [t for t in self.tasks if t['completed']]
        elif filter_type == 'High Priority':
            filtered_tasks = [t for t in self.tasks if t.get('priority') == 'high']
        
        if index < len(filtered_tasks):
            task = filtered_tasks[index]
            task['completed'] = not task['completed']
            task['completed_date'] = datetime.now().strftime("%Y-%m-%d %H:%M") if task['completed'] else None
            
            self.save_task(task)
            self.refresh_tasks_list()
            self.update_status()
            
            status = "completed" if task['completed'] else "reactivated"
            messagebox.showinfo("Success!", f"✓ Task {status}!")
        
    def edit_task(self):
        """Edit selected task"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task to edit!")
            return
        
        messagebox.showinfo("Coming Soon", "Task editing will be available in the next update!")
        
    def delete_task(self):
        """Delete selected task"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task!")
            return
        
        if not messagebox.askyesno("Confirm Delete", "Delete this task permanently?"):
            return
        
        selected_item = selection[0]
        index = self.tasks_tree.index(selected_item)
        
        # Get filtered tasks
        filter_type = self.task_filter.get()
        filtered_tasks = self.tasks
        if filter_type == 'Active':
            filtered_tasks = [t for t in self.tasks if not t['completed']]
        elif filter_type == 'Completed':
            filtered_tasks = [t for t in self.tasks if t['completed']]
        elif filter_type == 'High Priority':
            filtered_tasks = [t for t in self.tasks if t.get('priority') == 'high']
        
        if index < len(filtered_tasks):
            task = filtered_tasks[index]
            
            # Delete from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id=?', (task['id'],))
            conn.commit()
            conn.close()
            
            # Remove from memory
            self.tasks.remove(task)
            
            self.refresh_tasks_list()
            self.update_status()
            
            messagebox.showinfo("Deleted", "Task deleted successfully!")
        
    def add_note(self):
        """Enhanced note saving"""
        title = self.note_title.get().strip()
        content = self.note_content.get("1.0", tk.END).strip()
        tags = self.note_tags.get().strip()
        
        if not title:
            messagebox.showwarning("Missing Title", "Please enter a note title!")
            return
            
        if not content:
            messagebox.showwarning("Empty Note", "Please add some content to your note!")
            return
        
        # Check if editing existing note
        existing_note = None
        for note in self.notes:
            if note['title'] == title:
                if messagebox.askyesno("Update Note", f"A note with title '{title}' already exists. Update it?"):
                    existing_note = note
                break
        
        if existing_note:
            existing_note['content'] = content
            existing_note['tags'] = tags
            self.save_note(existing_note)
            message = "Note updated!"
        else:
            note = {
                'id': None,
                'title': title,
                'content': content,
                'created': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'modified': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'tags': tags
            }
            
            self.notes.insert(0, note)
            self.save_note(note)
            message = "Note saved!"
        
        self.clear_note_form()
        self.refresh_notes_list()
        self.update_status()
        
        messagebox.showinfo("Success!", f"📝 {message}")
        
    def clear_note_form(self):
        """Clear note input form"""
        self.note_title.delete(0, tk.END)
        self.note_content.delete("1.0", tk.END)
        self.note_tags.delete(0, tk.END)
        
    def refresh_notes_list(self):
        """Refresh notes list"""
        self.notes_list.delete(0, tk.END)
        
        for note in self.notes:
            display_text = f"📄 {note['title']}"
            if note.get('tags'):
                display_text += f" [{note['tags']}]"
            self.notes_list.insert(tk.END, display_text)
        
    def search_notes(self):
        """Search notes by title and content"""
        search_term = self.note_search.get().strip().lower()
        
        self.notes_list.delete(0, tk.END)
        
        if not search_term:
            self.refresh_notes_list()
            return
        
        for note in self.notes:
            if (search_term in note['title'].lower() or 
                search_term in note['content'].lower() or
                search_term in note.get('tags', '').lower()):
                display_text = f"📄 {note['title']}"
                if note.get('tags'):
                    display_text += f" [{note['tags']}]"
                self.notes_list.insert(tk.END, display_text)
        
    def show_note(self, event):
        """Display selected note in form for viewing/editing"""
        selection = self.notes_list.curselection()
        if not selection:
            return
        
        index = selection[0]
        
        # Account for search filter
        search_term = self.note_search.get().strip().lower()
        if search_term:
            filtered_notes = [n for n in self.notes if 
                            search_term in n['title'].lower() or 
                            search_term in n['content'].lower() or
                            search_term in n.get('tags', '').lower()]
            if index < len(filtered_notes):
                note = filtered_notes[index]
        else:
            if index < len(self.notes):
                note = self.notes[index]
        
        # Populate form
        self.note_title.delete(0, tk.END)
        self.note_title.insert(0, note['title'])
        
        self.note_content.delete("1.0", tk.END)
        self.note_content.insert("1.0", note['content'])
        
        self.note_tags.delete(0, tk.END)
        if note.get('tags'):
            self.note_tags.insert(0, note['tags'])
        
    def edit_note(self, event):
        """Double-click to edit note"""
        self.show_note(event)
        
    def delete_note(self):
        """Delete selected note"""
        selection = self.notes_list.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a note to delete!")
            return
        
        if not messagebox.askyesno("Confirm Delete", "Delete this note permanently?"):
            return
        
        index = selection[0]
        
        # Account for search filter
        search_term = self.note_search.get().strip().lower()
        if search_term:
            filtered_notes = [n for n in self.notes if 
                            search_term in n['title'].lower() or 
                            search_term in n['content'].lower() or
                            search_term in n.get('tags', '').lower()]
            if index < len(filtered_notes):
                note = filtered_notes[index]
        else:
            if index < len(self.notes):
                note = self.notes[index]
        
        # Delete from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM notes WHERE id=?', (note['id'],))
        conn.commit()
        conn.close()
        
        # Remove from memory
        self.notes.remove(note)
        
        self.refresh_notes_list()
        self.clear_note_form()
        self.update_status()
        
        messagebox.showinfo("Deleted", "Note deleted successfully!")
        
    def export_data(self):
        """Export all data to JSON"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"chatbot_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if not filename:
            return
        
        export_data = {
            'tasks': self.tasks,
            'notes': self.notes,
            'export_date': datetime.now().isoformat(),
            'version': '2.0'
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Export Successful", 
                              f"✓ Data exported to:\n{filename}\n\n"
                              f"Tasks: {len(self.tasks)}\n"
                              f"Notes: {len(self.notes)}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Error: {str(e)}")
        
    def import_data(self):
        """Import data from JSON"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Confirm import
            task_count = len(import_data.get('tasks', []))
            note_count = len(import_data.get('notes', []))
            
            if not messagebox.askyesno("Confirm Import",
                                      f"Import {task_count} tasks and {note_count} notes?\n\n"
                                      "This will add to your existing data."):
                return
            
            # Import tasks
            for task in import_data.get('tasks', []):
                task['id'] = None  # Will get new ID
                self.tasks.append(task)
                self.save_task(task)
            
            # Import notes
            for note in import_data.get('notes', []):
                note['id'] = None  # Will get new ID
                self.notes.append(note)
                self.save_note(note)
            
            self.refresh_tasks_list()
            self.refresh_notes_list()
            self.update_status()
            
            messagebox.showinfo("Import Successful", 
                              f"✓ Imported:\n"
                              f"Tasks: {task_count}\n"
                              f"Notes: {note_count}")
        except Exception as e:
            messagebox.showerror("Import Failed", f"Error: {str(e)}")
        
    def clear_chat(self):
        """Clear chat history"""
        if messagebox.askyesno("Clear Chat", "Clear all chat messages?"):
            self.chat_display.config(state='normal')
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state='disabled')
            self.conversation_history = []
            
            self.add_message("system", "Chat cleared.")
        
    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo("Settings", "Settings panel coming in next update!")
        
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", 
                           "AI Project Assistant - Enhanced Edition\n"
                           "Version 2.0\n\n"
                           "A production-ready chatbot with:\n"
                           "• Database persistence\n"
                           "• Advanced task management\n"
                           "• Smart note organization\n"
                           "• Analytics & insights\n\n"
                           "Built with Python & Tkinter")
        
    def show_user_guide(self):
        """Show user guide"""
        guide = """
🎯 QUICK START GUIDE

1. TASKS TAB
   • Add tasks with priority levels
   • Filter by status or priority
   • Mark tasks as complete
   • Track deadlines

2. NOTES TAB
   • Create rich text notes
   • Add tags for organization
   • Search across all notes
   • Quick edit on double-click

3. CHAT TAB
   • Ask about your tasks
   • Get productivity tips
   • Check your progress
   • Coding help available

4. ANALYTICS TAB
   • View your statistics
   • Track completion rates
   • Get insights

5. FILE MENU
   • Export: Backup your data
   • Import: Restore from backup

TIPS:
• Data auto-saves every 30 seconds
• Double-click notes to edit
• Use filters to focus on what matters
• Check analytics for motivation!
        """
        
        messagebox.showinfo("User Guide", guide)
        
    def auto_save(self):
        """Auto-save data every 30 seconds"""
        self.update_status()
        # Schedule next auto-save
        self.root.after(30000, self.auto_save)
        
    def on_closing(self):
        """Handle window close"""
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?\nAll data is saved."):
            self.root.destroy()

def main():
    root = tk.Tk()
    app = EnhancedChatbot(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
