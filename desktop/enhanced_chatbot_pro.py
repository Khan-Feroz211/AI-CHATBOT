import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog
import json
from datetime import datetime
import sqlite3
import os
from pathlib import Path
import base64
import random
import string
import webbrowser
import threading
import time
import secrets

try:
    from src.core.security import hash_password, verify_password, is_legacy_sha256_hash
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.core.security import hash_password, verify_password, is_legacy_sha256_hash

# For PDF export
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# For AI backend (optional)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class UserAuthSystem:
    """Handle user authentication and sessions"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.current_user = None
        self.setup_users_table()
    
    def setup_users_table(self):
        """Create users table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # First, check if is_guest column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_guest' not in columns:
                # Add is_guest column if it doesn't exist
                cursor.execute('''
                    ALTER TABLE users ADD COLUMN is_guest INTEGER DEFAULT 0
                ''')
                print("✅ Added is_guest column to users table")
        except sqlite3.OperationalError:
            # Table doesn't exist yet, will be created below
            pass
        
        # Create table if it doesn't exist (with all columns)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_date TEXT,
                last_login TEXT,
                role TEXT DEFAULT 'user',
                is_guest INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password with salt"""
        return hash_password(password)
    
    def register_user(self, username, password, email="", is_guest=False):
        """Register a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, created_date, role, is_guest)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, password_hash, email, datetime.now().isoformat(), 
                  'user' if not is_guest else 'guest', 1 if is_guest else 0))
            
            conn.commit()
            conn.close()
            return True, "✅ User registered successfully!"
        except sqlite3.IntegrityError:
            conn.close()
            return False, "❌ Username already exists!"
        except Exception as e:
            conn.close()
            return False, f"❌ Registration failed: {str(e)}"
    
    def login_user(self, username, password):
        """Authenticate user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, username, role, is_guest, password_hash FROM users
                WHERE username = ?
            ''', (username,))
            user = cursor.fetchone()
        except sqlite3.OperationalError as e:
            if "no such column: is_guest" in str(e):
                # Handle old database schema
                cursor.execute('''
                    SELECT id, username, role, password_hash FROM users
                    WHERE username = ?
                ''', (username,))
                legacy_user = cursor.fetchone()
                if legacy_user:
                    # Add is_guest column with default value
                    try:
                        cursor.execute('ALTER TABLE users ADD COLUMN is_guest INTEGER DEFAULT 0')
                        cursor.execute('UPDATE users SET is_guest = 0 WHERE id = ?', (legacy_user[0],))
                        conn.commit()
                    except Exception:
                        pass  # Column might already exist
                    user = (legacy_user[0], legacy_user[1], legacy_user[2], 0, legacy_user[3])
                else:
                    user = None
            else:
                conn.close()
                return False, f"❌ Database error: {str(e)}"
        
        if user:
            stored_hash = user[4]
            if not verify_password(password, stored_hash):
                conn.close()
                return False, "Invalid username or password!"

            if is_legacy_sha256_hash(stored_hash):
                cursor.execute('''
                    UPDATE users SET password_hash = ? WHERE id = ?
                ''', (self.hash_password(password), user[0]))
            
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.now().isoformat(), user[0]))
            conn.commit()
            
            self.current_user = {
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'is_guest': bool(user[3])
            }
            conn.close()
            return True, f"🎉 Welcome back, {username}!"
        
        conn.close()
        return False, "Invalid username or password!"
    
    def create_guest_user(self):
        """Create a temporary guest user"""
        # Generate random guest username
        timestamp = datetime.now().strftime("%H%M%S")
        random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        guest_username = f"guest_{timestamp}_{random_chars}"
        guest_password = secrets.token_urlsafe(16)
        
        success, message = self.register_user(
            guest_username, 
            guest_password, 
            is_guest=True
        )
        
        if success:
            # Auto-login the guest
            login_success, login_message = self.login_user(guest_username, guest_password)
            if login_success:
                return True, f"🎉 Guest session created: {guest_username}"
        
        return False, "❌ Failed to create guest session"
    
    def cleanup_old_guest_users(self):
        """Remove guest users older than 24 hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # First ensure is_guest column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_guest' not in columns:
                conn.close()
                return
            
            # Get guest users older than 24 hours
            cursor.execute('''
                SELECT id, username FROM users 
                WHERE is_guest = 1 AND last_login < datetime('now', '-1 day')
            ''')
            old_guests = cursor.fetchall()
            
            for guest in old_guests:
                guest_id, guest_username = guest
                
                # Delete associated data
                cursor.execute('DELETE FROM tasks WHERE user_id = ?', (guest_id,))
                cursor.execute('DELETE FROM notes WHERE user_id = ?', (guest_id,))
                cursor.execute('DELETE FROM conversations WHERE user_id = ?', (guest_id,))
                cursor.execute('DELETE FROM files WHERE user_id = ?', (guest_id,))
                cursor.execute('DELETE FROM settings WHERE user_id = ?', (guest_id,))
                cursor.execute('DELETE FROM users WHERE id = ?', (guest_id,))
                
                print(f"🧹 Cleaned up old guest: {guest_username}")
            
            conn.commit()
        except Exception as e:
            print(f"⚠️ Error cleaning up guest users: {e}")
        finally:
            conn.close()
    
    def logout_user(self):
        """Logout current user"""
        user_was_guest = self.current_user and self.current_user.get('is_guest', False)
        self.current_user = None
        return user_was_guest


class ModernTkinterTheme:
    """Modern theme configuration for Tkinter"""
    
    @staticmethod
    def configure_styles():
        """Configure modern Tkinter styles"""
        style = ttk.Style()
        
        # Try to use a modern theme if available
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        else:
            style.theme_use('default')
        
        # Modern color palette
        colors = {
            'primary': '#3498db',
            'primary_dark': '#2980b9',
            'secondary': '#2c3e50',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'info': '#3498db',
            'light': '#ecf0f1',
            'dark': '#34495e',
            'background': '#f5f7fa',
            'surface': '#ffffff',
            'text': '#2c3e50',
            'text_light': '#7f8c8d',
            'border': '#dcdde1'
        }
        
        # Configure styles
        style.configure('TFrame', background=colors['background'])
        style.configure('Card.TFrame', 
                       background=colors['surface'], 
                       relief='solid', 
                       borderwidth=1,
                       bordercolor=colors['border'])
        
        # Label styles
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 16, 'bold'), 
                       foreground=colors['primary'])
        style.configure('Subtitle.TLabel', 
                       font=('Segoe UI', 11), 
                       foreground=colors['text_light'])
        style.configure('Heading.TLabel', 
                       font=('Segoe UI', 12, 'bold'), 
                       foreground=colors['dark'])
        
        # Button styles
        style.configure('Primary.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       background=colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       padding=10,
                       focuscolor='none')
        style.map('Primary.TButton',
                 background=[('active', colors['primary_dark']),
                           ('disabled', '#bdc3c7')])
        
        style.configure('Secondary.TButton',
                       font=('Segoe UI', 10),
                       background=colors['light'],
                       foreground=colors['text'],
                       borderwidth=1,
                       padding=8)
        
        style.configure('Success.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       background=colors['success'],
                       foreground='white',
                       borderwidth=0,
                       padding=10)
        
        style.configure('Danger.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       background=colors['danger'],
                       foreground='white',
                       borderwidth=0,
                       padding=10)
        
        # Entry styles
        style.configure('Modern.TEntry',
                       font=('Segoe UI', 10),
                       fieldbackground=colors['surface'],
                       borderwidth=1,
                       relief='solid',
                       padding=5)
        
        # Notebook styles
        style.configure('Modern.TNotebook',
                       background=colors['background'],
                       borderwidth=0)
        style.configure('Modern.TNotebook.Tab',
                       font=('Segoe UI', 10, 'bold'),
                       padding=[20, 8],
                       background=colors['light'],
                       foreground=colors['text'])
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', colors['primary'])],
                 foreground=[('selected', 'white')])
        
        # Treeview styles
        style.configure('Modern.Treeview',
                       font=('Segoe UI', 9),
                       background=colors['surface'],
                       fieldbackground=colors['surface'],
                       rowheight=28,
                       borderwidth=1,
                       relief='solid')
        style.configure('Modern.Treeview.Heading',
                       font=('Segoe UI', 10, 'bold'),
                       background=colors['primary'],
                       foreground='white',
                       relief='flat',
                       padding=5)
        style.map('Modern.Treeview.Heading',
                 background=[('active', colors['primary_dark'])])
        
        # Scrollbar style
        style.configure('Modern.Vertical.TScrollbar',
                       background=colors['light'],
                       troughcolor=colors['background'],
                       borderwidth=0,
                       arrowsize=14)
        
        # Progressbar style
        style.configure('Modern.Horizontal.TProgressbar',
                       background=colors['primary'],
                       troughcolor=colors['light'],
                       borderwidth=0,
                       lightcolor=colors['primary'],
                       darkcolor=colors['primary'])
        
        return style, colors


class SplashScreen:
    """Show a splash screen during loading"""
    
    def __init__(self, root):
        self.root = root
        
        # Create splash window
        self.splash = tk.Toplevel(root)
        self.splash.title("Loading...")
        self.splash.geometry("400x300")
        self.splash.overrideredirect(True)  # Remove window decorations
        
        # Center the splash screen
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 300) // 2
        self.splash.geometry(f"400x300+{x}+{y}")
        
        # Make it stay on top
        self.splash.attributes('-topmost', True)
        
        # Configure background
        self.splash.configure(bg='#2c3e50')
        
        # Add content
        self.create_content()
        
        # Animate
        self.animate_logo()
    
    def create_content(self):
        """Create splash screen content"""
        # Main frame
        main_frame = tk.Frame(self.splash, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True)
        
        # Logo/Icon
        self.logo_label = tk.Label(main_frame, text="🤖", 
                                  font=("Arial", 64), 
                                  bg='#2c3e50', fg='#3498db')
        self.logo_label.pack(pady=(40, 10))
        
        # App name
        title_label = tk.Label(main_frame, text="AI Project Assistant", 
                              font=("Segoe UI", 20, "bold"), 
                              bg='#2c3e50', fg='white')
        title_label.pack(pady=(0, 5))
        
        subtitle_label = tk.Label(main_frame, text="Pro Edition v2.1", 
                                 font=("Segoe UI", 12), 
                                 bg='#2c3e50', fg='#bdc3c7')
        subtitle_label.pack()
        
        # Loading text
        self.loading_label = tk.Label(main_frame, text="Loading...", 
                                      font=("Segoe UI", 10), 
                                      bg='#2c3e50', fg='#95a5a6')
        self.loading_label.pack(pady=(30, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate',
                                       style='Modern.Horizontal.TProgressbar')
        self.progress.pack(pady=10, padx=50, fill='x')
        self.progress.start()
        
        # Version info
        version_label = tk.Label(main_frame, text="© 2024 AI Assistant Pro", 
                                font=("Segoe UI", 8), 
                                bg='#2c3e50', fg='#7f8c8d')
        version_label.pack(side='bottom', pady=10)
    
    def animate_logo(self):
        """Animate the logo"""
        colors = ['#3498db', '#9b59b6', '#2ecc71', '#e74c3c', '#f39c12']
        current_color = 0
        
        def change_color():
            nonlocal current_color
            self.logo_label.config(fg=colors[current_color])
            current_color = (current_color + 1) % len(colors)
            self.splash.after(500, change_color)
        
        change_color()
    
    def update_status(self, text):
        """Update loading status text"""
        self.loading_label.config(text=text)
        self.splash.update()
    
    def destroy(self):
        """Destroy splash screen"""
        self.progress.stop()
        self.splash.destroy()


class EnhancedChatbotPro:
    """Enhanced chatbot with premium features and guest access"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AI Project Assistant Pro v2.1")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f5f7fa')
        
        # Set minimum window size
        self.root.minsize(900, 600)
        
        # Center window on screen
        self.center_window()
        
        # Apply modern theme
        self.style, self.colors = ModernTkinterTheme.configure_styles()
        
        # Show splash screen
        self.splash = SplashScreen(root)
        self.splash.update_status("Initializing...")
        
        # Initialize in background thread
        self.init_thread = threading.Thread(target=self.initialize_app, daemon=True)
        self.init_thread.start()
        
        # Check initialization status
        self.check_initialization()
    
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def initialize_app(self):
        """Initialize application components"""
        try:
            # Setup data directory and database
            self.data_dir = Path("chatbot_data")
            self.data_dir.mkdir(exist_ok=True)
            
            self.db_path = self.data_dir / "chatbot.db"
            
            # Initialize authentication
            self.auth = UserAuthSystem(self.db_path)
            self.splash.update_status("Setting up database...")
            time.sleep(0.5)
            
            # Clean up old guest users on startup
            self.auth.cleanup_old_guest_users()
            self.splash.update_status("Cleaning up old sessions...")
            time.sleep(0.5)
            
            # Show login/guest window
            self.splash.update_status("Preparing login...")
            time.sleep(0.5)
            
            # We'll handle login in main thread
            self.initialized = True
            
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            self.initialized = False
            self.error = str(e)
    
    def check_initialization(self):
        """Check if initialization is complete"""
        if hasattr(self, 'initialized'):
            if self.initialized:
                self.splash.destroy()
                self.show_login()
            else:
                self.splash.destroy()
                messagebox.showerror("❌ Initialization Failed", 
                                   f"Failed to initialize app:\n{getattr(self, 'error', 'Unknown error')}")
                self.root.quit()
        else:
            # Check again after 100ms
            self.root.after(100, self.check_initialization)
    
    def show_login(self):
        """Show modern login/register/guest dialog"""
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("AI Project Assistant Pro - Welcome")
        self.login_window.geometry("500x650")
        self.login_window.transient(self.root)
        self.login_window.grab_set()
        self.login_window.resizable(False, False)
        self.login_window.configure(bg=self.colors['background'])
        
        # Center the window
        self.login_window.update_idletasks()
        x = (self.login_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.login_window.winfo_screenheight() // 2) - (650 // 2)
        self.login_window.geometry(f"500x650+{x}+{y}")
        
        # Bind escape key to close
        self.login_window.bind('<Escape>', lambda e: self.login_window.destroy())
        
        # Main container with scrollbar
        main_container = tk.Frame(self.login_window, bg=self.colors['background'])
        main_container.pack(fill='both', expand=True)
        
        # Create a canvas for scrolling
        canvas = tk.Canvas(main_container, bg=self.colors['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Card.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Content
        content_frame = ttk.Frame(scrollable_frame, style='Card.TFrame', padding=30)
        content_frame.pack(fill='both', expand=True)
        
        # Title Section
        title_frame = ttk.Frame(content_frame)
        title_frame.pack(pady=(0, 20))
        
        # Icon with animation
        self.login_icon = ttk.Label(title_frame, text="🤖", font=("Segoe UI", 48))
        self.login_icon.pack()
        
        # App name
        ttk.Label(title_frame, text="AI Project Assistant", 
                 style='Title.TLabel').pack()
        ttk.Label(title_frame, text="Professional Edition v2.1", 
                 style='Subtitle.TLabel').pack()
        
        # Feature highlights
        features_frame = ttk.LabelFrame(content_frame, text="✨ Premium Features", 
                                       style='Card.TFrame', padding=15)
        features_frame.pack(fill='x', pady=(0, 20))
        
        features = [
            "✅ AI-Powered Task Management",
            "✅ Smart Notes with Tags",
            "✅ File Uploads & Attachments",
            "✅ Guest Mode Available",
            "✅ PDF & Markdown Export",
            "✅ Advanced Analytics Dashboard"
        ]
        
        for feature in features:
            ttk.Label(features_frame, text=feature, 
                     font=("Segoe UI", 9)).pack(anchor='w', pady=2)
        
        # Option Buttons
        options_frame = ttk.Frame(content_frame)
        options_frame.pack(fill='both', expand=True, pady=20)
        
        # Guest Access Button
        guest_frame = ttk.LabelFrame(options_frame, text="🚀 Quick Start", 
                                    style='Card.TFrame', padding=20)
        guest_frame.pack(fill='both', pady=(0, 15))
        
        ttk.Label(guest_frame, text="Try without registration:", 
                 font=("Segoe UI", 10, 'bold')).pack(pady=(0, 10))
        
        def start_guest():
            success, message = self.auth.create_guest_user()
            if success:
                self.login_window.destroy()
                self.complete_initialization()
                messagebox.showinfo("🎉 Guest Session Started", 
                                  f"{message}\n\n"
                                  "✨ **Full Access Granted:**\n"
                                  "• All premium features enabled\n"
                                  "• Local data storage\n"
                                  "• AI backend configuration\n"
                                  "• Export to PDF/Markdown\n\n"
                                  "💡 **Tip:** Upgrade anytime for permanent storage!")
            else:
                messagebox.showerror("❌ Guest Failed", message)
        
        self.guest_btn = ttk.Button(guest_frame, text="🎮 Start as Guest", 
                                   style='Primary.TButton',
                                   command=start_guest)
        self.guest_btn.pack(pady=10, fill='x')
        
        ttk.Label(guest_frame, text="No registration needed • Full features • Try now", 
                 font=("Segoe UI", 8), 
                 foreground=self.colors['text_light']).pack()
        
        # Or Separator
        separator = ttk.Label(options_frame, text="───── or ─────", 
                             font=("Segoe UI", 10), 
                             foreground=self.colors['text_light'],
                             background=self.colors['background'])
        separator.pack(pady=10)
        
        # Login/Register Section
        auth_frame = ttk.LabelFrame(options_frame, text="🔐 Registered Users", 
                                   style='Card.TFrame', padding=15)
        auth_frame.pack(fill='both', pady=(0, 10))
        
        # Tabbed interface for login/register
        auth_notebook = ttk.Notebook(auth_frame, style='Modern.TNotebook')
        auth_notebook.pack(fill='both')
        
        # Login Tab
        login_tab = ttk.Frame(auth_notebook, padding=10)
        auth_notebook.add(login_tab, text='🔑 Login')
        
        login_content = ttk.Frame(login_tab)
        login_content.pack(fill='both', expand=True)
        
        ttk.Label(login_content, text="Username:", 
                 font=("Segoe UI", 10)).pack(anchor='w', pady=(10, 5))
        self.login_user_entry = ttk.Entry(login_content, style='Modern.TEntry')
        self.login_user_entry.pack(pady=5, fill='x')
        
        ttk.Label(login_content, text="Password:", 
                 font=("Segoe UI", 10)).pack(anchor='w', pady=(10, 5))
        self.login_pass_entry = ttk.Entry(login_content, show="*", style='Modern.TEntry')
        self.login_pass_entry.pack(pady=5, fill='x')
        
        def do_login():
            username = self.login_user_entry.get().strip()
            password = self.login_pass_entry.get()
            
            if not username or not password:
                messagebox.showwarning("⚠️ Input Required", 
                                     "Please enter username and password!")
                return
            
            success, message = self.auth.login_user(username, password)
            if success:
                self.login_window.destroy()
                self.complete_initialization()
                messagebox.showinfo("🎉 Welcome Back", f"Welcome back, {username}!")
            else:
                messagebox.showerror("❌ Login Failed", message)
        
        self.login_btn = ttk.Button(login_content, text="Login", 
                                   style='Success.TButton',
                                   command=do_login)
        self.login_btn.pack(pady=20, fill='x')
        
        # Register Tab
        register_tab = ttk.Frame(auth_notebook, padding=10)
        auth_notebook.add(register_tab, text='📝 Register')
        
        register_content = ttk.Frame(register_tab)
        register_content.pack(fill='both', expand=True)
        
        ttk.Label(register_content, text="Username:", 
                 font=("Segoe UI", 10)).pack(anchor='w', pady=(10, 5))
        self.reg_user_entry = ttk.Entry(register_content, style='Modern.TEntry')
        self.reg_user_entry.pack(pady=5, fill='x')
        
        ttk.Label(register_content, text="Password:", 
                 font=("Segoe UI", 10)).pack(anchor='w', pady=(10, 5))
        self.reg_pass_entry = ttk.Entry(register_content, show="*", style='Modern.TEntry')
        self.reg_pass_entry.pack(pady=5, fill='x')
        
        ttk.Label(register_content, text="Confirm Password:", 
                 font=("Segoe UI", 10)).pack(anchor='w', pady=(10, 5))
        self.reg_confirm_entry = ttk.Entry(register_content, show="*", style='Modern.TEntry')
        self.reg_confirm_entry.pack(pady=5, fill='x')
        
        ttk.Label(register_content, text="Email (optional):", 
                 font=("Segoe UI", 10)).pack(anchor='w', pady=(10, 5))
        self.reg_email_entry = ttk.Entry(register_content, style='Modern.TEntry')
        self.reg_email_entry.pack(pady=5, fill='x')
        
        def do_register():
            username = self.reg_user_entry.get().strip()
            password = self.reg_pass_entry.get()
            confirm = self.reg_confirm_entry.get()
            email = self.reg_email_entry.get().strip()
            
            if not username or not password:
                messagebox.showwarning("⚠️ Input Required", 
                                     "Please enter username and password!")
                return
            
            if len(password) < 6:
                messagebox.showwarning("⚠️ Weak Password", 
                                     "Password must be at least 6 characters!")
                return
            
            if password != confirm:
                messagebox.showwarning("⚠️ Password Mismatch", 
                                     "Passwords don't match!")
                return
            
            success, message = self.auth.register_user(username, password, email)
            if success:
                messagebox.showinfo("✅ Success", 
                                  message + "\n\nPlease login now.")
                # Switch to login tab
                auth_notebook.select(0)
                self.login_user_entry.delete(0, tk.END)
                self.login_user_entry.insert(0, username)
                self.login_pass_entry.delete(0, tk.END)
            else:
                messagebox.showerror("❌ Registration Failed", message)
        
        self.register_btn = ttk.Button(register_content, text="Create Account", 
                                      style='Primary.TButton',
                                      command=do_register)
        self.register_btn.pack(pady=20, fill='x')
        
        # Info text at bottom
        info_frame = ttk.Frame(content_frame)
        info_frame.pack(fill='x', pady=(10, 0))
        
        info_label = ttk.Label(info_frame, 
            text="💡 Guest users get full access to all premium features!\n"
                 "👤 Registered users get permanent data storage and backup.",
            font=("Segoe UI", 9), 
            foreground=self.colors['text_light'],
            justify='center')
        info_label.pack()
        
        # Bind Enter keys
        self.login_pass_entry.bind('<Return>', lambda e: do_login())
        self.reg_confirm_entry.bind('<Return>', lambda e: do_register())
        
        # Focus on guest button by default
        self.login_window.after(100, self.guest_btn.focus)
        
        # Animate icon
        self.animate_login_icon()
        
        # Make window modal
        self.root.wait_window(self.login_window)
    
    def animate_login_icon(self):
        """Animate the login icon"""
        icons = ['🤖', '🚀', '🎯', '💡', '✨']
        current_icon = 0
        
        def change_icon():
            nonlocal current_icon
            self.login_icon.config(text=icons[current_icon])
            current_icon = (current_icon + 1) % len(icons)
            if self.login_window.winfo_exists():
                self.login_window.after(1000, change_icon)
        
        change_icon()
    
    def complete_initialization(self):
        """Complete app initialization after login"""
        try:
            # Initialize remaining components
            from enhanced_chatbot_pro import AIBackend, FileManager, ExportManager
            self.ai_backend = AIBackend()
            self.file_manager = FileManager(self.db_path, self.data_dir)
            
            # Setup database
            self.setup_database()
            
            # Load data from database
            self.load_data()
            
            # Initialize export manager
            self.export_manager = ExportManager(self.tasks, self.notes)
            
            # Conversation history for context
            self.conversation_history = []
            
            # Setup main UI
            self.setup_ui()
            
            # Start auto-save
            self.auto_save()
            
        except Exception as e:
            messagebox.showerror("❌ Initialization Error", 
                               f"Failed to initialize app:\n{str(e)}")
            self.root.quit()
    
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
                category TEXT DEFAULT 'general',
                user_id INTEGER
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
                tags TEXT,
                user_id INTEGER
            )
        ''')
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_message TEXT,
                bot_response TEXT,
                session_id TEXT,
                user_id INTEGER
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                setting_key TEXT,
                setting_value TEXT,
                UNIQUE(user_id, setting_key)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_data(self):
        """Load tasks and notes from database for current user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        user_id = self.auth.current_user['id']
        
        # Load tasks
        cursor.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY added_date DESC', (user_id,))
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
        cursor.execute('SELECT * FROM notes WHERE user_id = ? ORDER BY modified_date DESC', (user_id,))
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
        
        # Load AI settings
        cursor.execute('SELECT setting_value FROM settings WHERE user_id = ? AND setting_key = ?',
                      (user_id, 'ai_provider'))
        result = cursor.fetchone()
        if result:
            self.ai_backend.provider = result[0]
        
        cursor.execute('SELECT setting_value FROM settings WHERE user_id = ? AND setting_key = ?',
                      (user_id, 'ai_api_key'))
        result = cursor.fetchone()
        if result:
            self.ai_backend.api_key = result[0]
        
        conn.close()
    
    def setup_ui(self):
        """Setup modern main UI"""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Configure root window
        self.root.configure(bg=self.colors['background'])
        self.root.title(f"AI Project Assistant Pro - {self.auth.current_user['username']}")
        
        # Menu bar
        self.setup_menu()
        
        # Header with user info
        header_frame = ttk.Frame(self.root, style='Card.TFrame', padding=15)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        # User info
        username = self.auth.current_user['username']
        is_guest = self.auth.current_user.get('is_guest', False)
        
        user_icon = "👥" if is_guest else "👤"
        user_text = f"{user_icon} {username}"
        if is_guest:
            user_text += " (Guest)"
        
        user_label = ttk.Label(header_frame, text=user_text, 
                              font=("Segoe UI", 11, 'bold'),
                              foreground=self.colors['primary' if not is_guest else 'warning'])
        user_label.pack(side='left')
        
        # Status indicator
        status_text = "🟢 Online" if not is_guest else "🟡 Guest Mode"
        status_label = ttk.Label(header_frame, text=status_text,
                                font=("Segoe UI", 9),
                                foreground=self.colors['text_light'])
        status_label.pack(side='left', padx=(10, 0))
        
        # Header buttons
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side='right')
        
        if is_guest:
            upgrade_btn = ttk.Button(btn_frame, text="⭐ Upgrade", 
                                    style='Success.TButton',
                                    command=self.upgrade_guest,
                                    width=12)
            upgrade_btn.pack(side='left', padx=3)
        
        ai_btn = ttk.Button(btn_frame, text="⚙️ AI Settings", 
                           style='Secondary.TButton',
                           command=self.show_ai_settings,
                           width=12)
        ai_btn.pack(side='left', padx=3)
        
        logout_btn = ttk.Button(btn_frame, text="🚪 Logout", 
                               style='Secondary.TButton',
                               command=self.logout,
                               width=10)
        logout_btn.pack(side='left', padx=3)
        
        # Create tabs with modern styling
        self.notebook = ttk.Notebook(self.root, style='Modern.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Setup tabs
        self.setup_chat_tab()
        self.setup_tasks_tab()
        self.setup_notes_tab()
        self.setup_files_tab()
        self.setup_analytics_tab()
        
        # Status bar
        self.setup_status_bar()
        
        # Welcome message
        self.show_welcome_message()
        
        # Select chat tab by default
        self.notebook.select(0)
    
    def setup_menu(self):
        """Add modern menu bar"""
        menubar = tk.Menu(self.root, bg=self.colors['surface'], 
                         fg=self.colors['text'], font=("Segoe UI", 9))
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['surface'], 
                           fg=self.colors['text'], font=("Segoe UI", 9))
        menubar.add_cascade(label="📁 File", menu=file_menu)
        file_menu.add_command(label="📤 Export to PDF", command=self.export_to_pdf)
        file_menu.add_command(label="📄 Export to Markdown", command=self.export_to_markdown)
        file_menu.add_separator()
        file_menu.add_command(label="📥 Import Data", command=self.import_data)
        file_menu.add_separator()
        
        # Add upgrade option for guests
        if self.auth.current_user.get('is_guest', False):
            file_menu.add_command(label="⭐ Create Permanent Account", 
                                 command=self.upgrade_guest)
            file_menu.add_separator()
        
        file_menu.add_command(label="🚪 Logout", command=self.logout)
        file_menu.add_command(label="❌ Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['surface'], 
                           fg=self.colors['text'], font=("Segoe UI", 9))
        menubar.add_cascade(label="✏️ Edit", menu=edit_menu)
        edit_menu.add_command(label="🗑️ Clear Chat", command=self.clear_chat)
        edit_menu.add_command(label="🤖 AI Settings", command=self.show_ai_settings)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['surface'], 
                           fg=self.colors['text'], font=("Segoe UI", 9))
        menubar.add_cascade(label="👁️ View", menu=view_menu)
        view_menu.add_command(label="💬 Chat", command=lambda: self.notebook.select(0))
        view_menu.add_command(label="📋 Tasks", command=lambda: self.notebook.select(1))
        view_menu.add_command(label="📝 Notes", command=lambda: self.notebook.select(2))
        view_menu.add_command(label="📎 Files", command=lambda: self.notebook.select(3))
        view_menu.add_command(label="📊 Analytics", command=lambda: self.notebook.select(4))
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['surface'], 
                            fg=self.colors['text'], font=("Segoe UI", 9))
        menubar.add_cascade(label="🛠️ Tools", menu=tools_menu)
        tools_menu.add_command(label="📊 Analytics Dashboard", 
                              command=lambda: self.notebook.select(4))
        tools_menu.add_command(label="📎 File Manager", 
                              command=lambda: self.notebook.select(3))
        tools_menu.add_separator()
        tools_menu.add_command(label="🧹 Cleanup Database", command=self.cleanup_database)
        tools_menu.add_command(label="🔄 Refresh Data", command=self.refresh_all_data)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['surface'], 
                           fg=self.colors['text'], font=("Segoe UI", 9))
        menubar.add_cascade(label="❓ Help", menu=help_menu)
        help_menu.add_command(label="📖 User Guide", command=self.show_user_guide)
        help_menu.add_command(label="👥 Guest Information", command=self.show_guest_info)
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ About", command=self.show_about)
        help_menu.add_command(label="🌐 Visit GitHub", command=self.open_github)
        help_menu.add_command(label="📧 Report Issue", command=self.report_issue)
    
    def setup_status_bar(self):
        """Add modern status bar at bottom"""
        self.status_bar = ttk.Frame(self.root, style='Card.TFrame', padding=10)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
        
        # Status labels
        self.task_status = ttk.Label(self.status_bar, text="📋 Tasks: 0/0", 
                                    font=("Segoe UI", 9))
        self.task_status.pack(side='left', padx=10)
        
        self.note_status = ttk.Label(self.status_bar, text="📝 Notes: 0", 
                                    font=("Segoe UI", 9))
        self.note_status.pack(side='left', padx=10)
        
        self.ai_status = ttk.Label(self.status_bar, text="🤖 AI: Local", 
                                  font=("Segoe UI", 9))
        self.ai_status.pack(side='left', padx=10)
        
        self.user_status = ttk.Label(self.status_bar, text="👤 User: Guest", 
                                    font=("Segoe UI", 9))
        self.user_status.pack(side='left', padx=10)
        
        self.time_status = ttk.Label(self.status_bar, text="🕐 00:00:00", 
                                    font=("Segoe UI", 9))
        self.time_status.pack(side='right', padx=10)
        
        self.update_status()
    
    def update_status(self):
        """Update status bar with stats"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks if t['completed'])
        total_notes = len(self.notes)
        
        # Update labels
        self.task_status.config(text=f"📋 Tasks: {completed_tasks}/{total_tasks}")
        self.note_status.config(text=f"📝 Notes: {total_notes}")
        
        ai_provider = self.ai_backend.provider if hasattr(self, 'ai_backend') else 'Local'
        self.ai_status.config(text=f"🤖 AI: {ai_provider.title()}")
        
        is_guest = self.auth.current_user.get('is_guest', False)
        user_type = "Guest" if is_guest else "User"
        username = self.auth.current_user['username'][:12]
        if len(self.auth.current_user['username']) > 12:
            username += "..."
        self.user_status.config(text=f"{'👥' if is_guest else '👤'} {user_type}: {username}")
        
        self.time_status.config(text=f"🕐 {datetime.now().strftime('%H:%M:%S')}")
        
        # Schedule next update
        self.root.after(1000, self.update_status)
    
    def show_welcome_message(self):
        """Show welcome message in chat"""
        username = self.auth.current_user['username']
        is_guest = self.auth.current_user.get('is_guest', False)
        
        welcome_msg = f"""
╔{'═' * 60}╗
║{'🤖 AI PROJECT ASSISTANT PRO v2.1'.center(60)}║
╠{'═' * 60}╣
║{' ' * 60}║
║{'Welcome!'.center(60)}║
║{' ' * 60}║
║{'👤 User:'.ljust(20)}{username:<40}║
║{'🎯 Status:'.ljust(20)}{'🎮 Guest Account' if is_guest else '✅ Registered User':<40}║
║{' ' * 60}║
╚{'═' * 60}╝

✨ **Getting Started:**
• Type 'help' to see what I can do
• Use tabs to manage tasks, notes, and files
• Configure AI in ⚙️ AI Settings

💡 **Quick Tips:**
• Add task: 'Add a task: [description]'
• Ask: 'What's my progress?'
• Export data from File menu

{'⚠️ **Note:** You are using a guest account. Data may be cleaned up after 24 hours.' if is_guest else '✅ **Note:** Your data is securely stored.'}
"""
        
        self.add_message("system", welcome_msg)
    
    def setup_chat_tab(self):
        """Setup modern chat interface"""
        chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(chat_frame, text='💬 Chat')
        
        # Chat display with modern styling
        display_frame = ttk.LabelFrame(chat_frame, text="💬 Conversation", 
                                      style='Card.TFrame', padding=10)
        display_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.chat_display = scrolledtext.ScrolledText(
            display_frame, wrap=tk.WORD, height=20, font=("Segoe UI", 10),
            bg=self.colors['surface'], fg=self.colors['text'],
            relief='flat', borderwidth=0, padx=10, pady=10
        )
        self.chat_display.pack(fill='both', expand=True)
        self.chat_display.config(state='disabled')
        
        # Configure tags for different message types
        self.chat_display.tag_config("user", foreground="#2980b9", 
                                    font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("bot", foreground="#27ae60", 
                                    font=("Segoe UI", 10))
        self.chat_display.tag_config("system", foreground="#7f8c8d", 
                                    font=("Segoe UI", 9, "italic"))
        self.chat_display.tag_config("highlight", background="#fff9e6")
        
        # Input area
        input_frame = ttk.Frame(chat_frame, style='Card.TFrame', padding=10)
        input_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Input field with placeholder
        self.chat_input = ttk.Entry(input_frame, font=("Segoe UI", 10),
                                   style='Modern.TEntry')
        self.chat_input.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.chat_input.bind('<Return>', lambda e: self.send_message())
        self.chat_input.bind('<KeyRelease>', self.update_char_count)
        
        # Character counter
        self.char_count = ttk.Label(input_frame, text="0/500", 
                                   font=("Segoe UI", 9),
                                   foreground=self.colors['text_light'])
        self.char_count.pack(side='right', padx=(0, 10))
        
        # Send button
        send_btn = ttk.Button(input_frame, text="📤 Send", 
                             style='Primary.TButton',
                             command=self.send_message)
        send_btn.pack(side='right')
        
        # Quick action buttons
        quick_frame = ttk.Frame(chat_frame, padding=5)
        quick_frame.pack(fill='x', padx=10, pady=(0, 5))
        
        quick_actions = [
            ("🤖 Help", lambda: self.chat_input.insert(0, "help")),
            ("📋 Add Task", lambda: self.chat_input.insert(0, "Add a task: ")),
            ("📊 Progress", lambda: self.chat_input.insert(0, "What's my progress?")),
            ("🗑️ Clear", self.clear_chat)
        ]
        
        for text, command in quick_actions:
            btn = ttk.Button(quick_frame, text=text, style='Secondary.TButton',
                           command=command)
            btn.pack(side='left', padx=2)
    
    def setup_tasks_tab(self):
        """Setup modern tasks interface"""
        tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(tasks_frame, text='📋 Tasks')
        
        # Control panel
        control_frame = ttk.Frame(tasks_frame, style='Card.TFrame', padding=15)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        # Add task button
        add_btn = ttk.Button(control_frame, text="➕ Add Task", 
                            style='Success.TButton',
                            command=self.add_task_dialog)
        add_btn.pack(side='left', padx=5)
        
        # Clear completed button
        clear_btn = ttk.Button(control_frame, text="🗑️ Clear Completed", 
                              style='Secondary.TButton',
                              command=self.clear_completed_tasks)
        clear_btn.pack(side='left', padx=5)
        
        # Filter frame
        filter_frame = ttk.LabelFrame(control_frame, text="🔍 Filters", 
                                     style='Card.TFrame', padding=10)
        filter_frame.pack(side='right', padx=10)
        
        # Status filter
        ttk.Label(filter_frame, text="Status:", font=("Segoe UI", 9)).pack(side='left', padx=5)
        self.task_filter = tk.StringVar(value="all")
        ttk.Radiobutton(filter_frame, text="All", variable=self.task_filter, 
                       value="all", command=self.refresh_tasks_list).pack(side='left', padx=5)
        ttk.Radiobutton(filter_frame, text="Active", variable=self.task_filter, 
                       value="active", command=self.refresh_tasks_list).pack(side='left', padx=5)
        ttk.Radiobutton(filter_frame, text="Completed", variable=self.task_filter, 
                       value="completed", command=self.refresh_tasks_list).pack(side='left', padx=5)
        
        # Tasks list
        list_frame = ttk.Frame(tasks_frame, style='Card.TFrame', padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Treeview for tasks with modern styling
        columns = ('Status', 'Task', 'Priority', 'Category', 'Date')
        self.tasks_tree = ttk.Treeview(list_frame, columns=columns, height=15,
                                      style='Modern.Treeview', selectmode='extended')
        
        self.tasks_tree.heading('#0', text='ID')
        self.tasks_tree.heading('Status', text='✅')
        self.tasks_tree.heading('Task', text='Task Description')
        self.tasks_tree.heading('Priority', text='Priority')
        self.tasks_tree.heading('Category', text='Category')
        self.tasks_tree.heading('Date', text='Added')
        
        self.tasks_tree.column('#0', width=0, stretch=False)
        self.tasks_tree.column('Status', width=50, anchor='center')
        self.tasks_tree.column('Task', width=350)
        self.tasks_tree.column('Priority', width=100, anchor='center')
        self.tasks_tree.column('Category', width=100, anchor='center')
        self.tasks_tree.column('Date', width=120, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', 
                                 command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)
        
        self.tasks_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Action buttons
        action_frame = ttk.Frame(tasks_frame, padding=5)
        action_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        actions = [
            ("🔄 Refresh", self.refresh_tasks_list),
            ("✅ Complete", self.toggle_task_completion),
            ("✏️ Edit", self.edit_task_dialog),
            ("🗑️ Delete", self.delete_selected_task)
        ]
        
        for text, command in actions:
            btn = ttk.Button(action_frame, text=text, style='Secondary.TButton',
                           command=command)
            btn.pack(side='left', padx=5)
        
        self.refresh_tasks_list()
    
    def setup_notes_tab(self):
        """Setup modern notes interface"""
        notes_frame = ttk.Frame(self.notebook)
        self.notebook.add(notes_frame, text='📝 Notes')
        
        # Control panel
        control_frame = ttk.Frame(notes_frame, style='Card.TFrame', padding=15)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        # Add note button
        add_btn = ttk.Button(control_frame, text="➕ Add Note", 
                            style='Success.TButton',
                            command=self.add_note_dialog)
        add_btn.pack(side='left', padx=5)
        
        # Search frame
        search_frame = ttk.LabelFrame(control_frame, text="🔍 Search Notes", 
                                     style='Card.TFrame', padding=10)
        search_frame.pack(side='right', padx=10)
        
        ttk.Label(search_frame, text="Search:", font=("Segoe UI", 9)).pack(side='left', padx=5)
        self.note_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.note_search_var, 
                                width=25, style='Modern.TEntry')
        search_entry.pack(side='left', padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.refresh_notes_list())
        
        # Notes list
        list_frame = ttk.Frame(notes_frame, style='Card.TFrame', padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Treeview for notes
        columns = ('Title', 'Tags', 'Modified')
        self.notes_tree = ttk.Treeview(list_frame, columns=columns, height=15,
                                      style='Modern.Treeview')
        
        self.notes_tree.heading('#0', text='ID')
        self.notes_tree.heading('Title', text='Title')
        self.notes_tree.heading('Tags', text='🏷️ Tags')
        self.notes_tree.heading('Modified', text='📅 Last Modified')
        
        self.notes_tree.column('#0', width=0, stretch=False)
        self.notes_tree.column('Title', width=350)
        self.notes_tree.column('Tags', width=150)
        self.notes_tree.column('Modified', width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', 
                                 command=self.notes_tree.yview)
        self.notes_tree.configure(yscrollcommand=scrollbar.set)
        
        self.notes_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Action buttons
        action_frame = ttk.Frame(notes_frame, padding=5)
        action_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        actions = [
            ("🔄 Refresh", self.refresh_notes_list),
            ("👁️ View", self.view_note),
            ("✏️ Edit", self.edit_note_dialog),
            ("🗑️ Delete", self.delete_selected_note)
        ]
        
        for text, command in actions:
            btn = ttk.Button(action_frame, text=text, style='Secondary.TButton',
                           command=command)
            btn.pack(side='left', padx=5)
        
        self.refresh_notes_list()
    
    def setup_files_tab(self):
        """Setup modern files/attachments tab"""
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text='📎 Files')
        
        # Upload section
        upload_frame = ttk.LabelFrame(files_frame, text="📤 Upload File", 
                                     style='Card.TFrame', padding=15)
        upload_frame.pack(fill='x', padx=10, pady=10)
        
        upload_btn = ttk.Button(upload_frame, text="📁 Choose File", 
                               style='Primary.TButton',
                               command=self.upload_file)
        upload_btn.pack(side='left', padx=5)
        
        ttk.Label(upload_frame, 
                 text="Upload files for reference or attach to tasks/notes",
                 font=("Segoe UI", 9)).pack(side='left', padx=10)
        
        # Files list
        list_frame = ttk.LabelFrame(files_frame, text="📂 Uploaded Files", 
                                   style='Card.TFrame', padding=15)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview for files
        columns = ('Filename', 'Type', 'Size', 'Date')
        self.files_tree = ttk.Treeview(list_frame, columns=columns, height=15,
                                      style='Modern.Treeview')
        
        self.files_tree.heading('#0', text='ID')
        self.files_tree.heading('Filename', text='📄 Filename')
        self.files_tree.heading('Type', text='Type')
        self.files_tree.heading('Size', text='Size')
        self.files_tree.heading('Date', text='📅 Uploaded')
        
        self.files_tree.column('#0', width=0, stretch=False)
        self.files_tree.column('Filename', width=350)
        self.files_tree.column('Type', width=100)
        self.files_tree.column('Size', width=100)
        self.files_tree.column('Date', width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', 
                                 command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        self.files_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Action buttons
        action_frame = ttk.Frame(files_frame, padding=5)
        action_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        actions = [
            ("🔄 Refresh", self.refresh_files_list),
            ("📂 Open", self.open_selected_file),
            ("🗑️ Delete", self.delete_selected_file)
        ]
        
        for text, command in actions:
            btn = ttk.Button(action_frame, text=text, style='Secondary.TButton',
                           command=command)
            btn.pack(side='left', padx=5)
        
        self.refresh_files_list()
    
    def setup_analytics_tab(self):
        """Setup modern analytics dashboard"""
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text='📊 Analytics')
        
        # Stats cards
        stats_frame = ttk.Frame(analytics_frame)
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        stats_data = [
            ("📋 Total Tasks", len(self.tasks), "#3498db"),
            ("✅ Completed", sum(1 for t in self.tasks if t['completed']), "#27ae60"),
            ("⚡ Active", sum(1 for t in self.tasks if not t['completed']), "#f39c12"),
            ("📝 Total Notes", len(self.notes), "#9b59b6"),
            ("🔴 High Priority", sum(1 for t in self.tasks if t.get('priority') == 'high'), "#e74c3c"),
            ("📈 Completion Rate", 
             f"{sum(1 for t in self.tasks if t['completed']) / len(self.tasks) * 100:.1f}%" 
             if self.tasks else "0%", "#1abc9c")
        ]
        
        for i, (label, value, color) in enumerate(stats_data):
            card = ttk.Frame(stats_frame, style='Card.TFrame', padding=15)
            card.grid(row=i//3, column=i%3, padx=5, pady=5, sticky='nsew')
            
            ttk.Label(card, text=label, font=("Segoe UI", 9),
                     foreground=self.colors['text_light']).pack(anchor='w')
            ttk.Label(card, text=str(value), font=("Segoe UI", 18, 'bold'),
                     foreground=color).pack(anchor='w', pady=(5, 0))
        
        # Make columns expand equally
        for i in range(3):
            stats_frame.columnconfigure(i, weight=1)
        
        # Charts/Visualizations frame
        charts_frame = ttk.LabelFrame(analytics_frame, text="📈 Visualizations", 
                                     style='Card.TFrame', padding=15)
        charts_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Text-based visualization
        chart_text = scrolledtext.ScrolledText(charts_frame, height=12, 
                                              font=("Courier New", 9),
                                              bg=self.colors['surface'],
                                              fg=self.colors['text'])
        chart_text.pack(fill='both', expand=True)
        
        # Generate ASCII chart
        chart_data = self.generate_ascii_chart()
        chart_text.insert('1.0', chart_data)
        chart_text.config(state='disabled')
        
        # Export button
        export_frame = ttk.Frame(analytics_frame, padding=10)
        export_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(export_frame, text="📊 Export Analytics Report", 
                  style='Primary.TButton',
                  command=self.export_analytics).pack()
    
    def generate_ascii_chart(self):
        """Generate ASCII-based charts for analytics"""
        if not self.tasks:
            return "No data available. Start by adding some tasks!"
        
        chart = "📊 PRODUCTIVITY ANALYTICS\n"
        chart += "=" * 60 + "\n\n"
        
        # Task completion chart
        completed = sum(1 for t in self.tasks if t['completed'])
        active = len(self.tasks) - completed
        
        chart += "📋 TASK COMPLETION:\n"
        chart += f"✅ Completed: {completed} ({completed/len(self.tasks)*100:.1f}%)\n"
        chart += f"⚡ Active: {active} ({active/len(self.tasks)*100:.1f}%)\n\n"
        
        # Visual progress bar
        total_width = 40
        completed_width = int((completed / len(self.tasks)) * total_width) if self.tasks else 0
        
        chart += "[" + "█" * completed_width + "░" * (total_width - completed_width) + "]\n\n"
        
        # Priority distribution
        priorities = {'high': 0, 'medium': 0, 'low': 0}
        for task in self.tasks:
            prio = task.get('priority', 'medium')
            if prio in priorities:
                priorities[prio] += 1
        
        chart += "🎯 PRIORITY DISTRIBUTION:\n"
        max_count = max(priorities.values()) if priorities else 1
        
        for prio, count in priorities.items():
            bar_width = int((count / max_count) * 30) if max_count > 0 else 0
            emoji = "🔴" if prio == 'high' else "🟡" if prio == 'medium' else "🟢"
            chart += f"{emoji} {prio.capitalize():7} [{'█' * bar_width:<30}] {count}\n"
        
        chart += "\n" + "=" * 60 + "\n"
        chart += f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        
        return chart
    
    def add_message(self, sender, text):
        """Add message to chat display with modern styling"""
        self.chat_display.config(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add timestamp
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "system")
        
        # Add sender with appropriate tag
        if sender.lower() == "you":
            self.chat_display.insert(tk.END, "👤 You: ", "user")
        elif sender.lower() == "bot":
            self.chat_display.insert(tk.END, "🤖 Assistant: ", "bot")
        else:
            self.chat_display.insert(tk.END, f"📢 {sender}: ", "system")
            
        # Add message text
        self.chat_display.insert(tk.END, f"{text}\n\n")
        
        # Auto-scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
    
    def send_message(self):
        """Send message and get AI response"""
        msg = self.chat_input.get().strip()
        if not msg:
            return
        
        if len(msg) > 500:
            messagebox.showwarning("⚠️ Message Too Long", 
                                 "Please keep messages under 500 characters.")
            return
            
        # Clear input and update counter
        self.chat_input.delete(0, tk.END)
        self.update_char_count()
        
        # Add user message to chat
        self.add_message("You", msg)
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": msg})
        
        # Show typing indicator
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, "🤖 Assistant is typing...\n", "system")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        self.root.update()
        
        # Get response from AI backend (simulated delay)
        def get_response():
            time.sleep(0.5)  # Simulate thinking time
            response = self.ai_backend.generate_response(msg, self.conversation_history if self.ai_backend.provider != "local" else None)
            
            # Remove typing indicator and add response
            self.root.after(0, lambda: self.display_response(response))
        
        # Run in thread to avoid freezing UI
        threading.Thread(target=get_response, daemon=True).start()
    
    def display_response(self, response):
        """Display AI response in chat"""
        self.chat_display.config(state='normal')
        
        # Remove typing indicator (last 2 lines)
        end_index = self.chat_display.index("end")
        line2 = self.chat_display.index(f"{end_index} - 2 lines")
        line1 = self.chat_display.index(f"{end_index} - 1 lines")
        self.chat_display.delete(line2, line1)
        
        self.add_message("Bot", response)
        
        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Keep only last 20 messages to avoid token limits
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        # Log conversation
        self.log_conversation(msg, response)
    
    def update_char_count(self, event=None):
        """Update character counter"""
        count = len(self.chat_input.get())
        self.char_count.config(text=f"{count}/500")
        
        if count > 450:
            self.char_count.config(foreground=self.colors['danger'])
        elif count > 400:
            self.char_count.config(foreground=self.colors['warning'])
        else:
            self.char_count.config(foreground=self.colors['text_light'])
    
    def log_conversation(self, user_msg, bot_response):
        """Log conversation to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            session_id = datetime.now().strftime("%Y%m%d")
            user_id = self.auth.current_user['id']
            
            cursor.execute('''
                INSERT INTO conversations (timestamp, user_message, bot_response, session_id, user_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), user_msg, bot_response, session_id, user_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Failed to log conversation: {e}")
    
    # Task management methods
    def add_task_dialog(self):
        """Show modern dialog to add new task"""
        dialog = tk.Toplevel(self.root)
        dialog.title("➕ Add New Task")
        dialog.geometry("450x400")
        dialog.transient(self.root)
        dialog.configure(bg=self.colors['background'])
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"450x400+{x}+{y}")
        
        frame = ttk.Frame(dialog, style='Card.TFrame', padding=20)
        frame.pack(fill='both', expand=True)
        
        # Title
        ttk.Label(frame, text="➕ Add New Task", style='Title.TLabel').pack(pady=(0, 20))
        
        # Task description
        ttk.Label(frame, text="Task Description:", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        task_text = scrolledtext.ScrolledText(frame, height=4, width=40, 
                                             font=("Segoe UI", 10))
        task_text.pack(pady=(0, 10), fill='x')
        task_text.focus()
        
        # Priority selection
        ttk.Label(frame, text="Priority:", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        priority_var = tk.StringVar(value="medium")
        priority_frame = ttk.Frame(frame)
        priority_frame.pack(anchor='w', pady=(0, 10))
        
        priorities = [("🔴 High", "high"), ("🟡 Medium", "medium"), ("🟢 Low", "low")]
        for text, value in priorities:
            ttk.Radiobutton(priority_frame, text=text, variable=priority_var, 
                           value=value).pack(side='left', padx=5)
        
        # Category
        ttk.Label(frame, text="Category:", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        category_entry = ttk.Entry(frame, width=30, style='Modern.TEntry')
        category_entry.pack(pady=(0, 20), fill='x')
        category_entry.insert(0, "general")
        
        def save_task():
            text = task_text.get("1.0", tk.END).strip()
            if not text:
                messagebox.showwarning("⚠️ Input Required", 
                                     "Please enter task description!")
                return
            
            task = {
                'text': text,
                'completed': False,
                'priority': priority_var.get(),
                'added': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'category': category_entry.get().strip() or "general"
            }
            
            self.tasks.append(task)
            self.save_task(task)
            self.refresh_tasks_list()
            self.update_status()
            dialog.destroy()
            
            # Show success message
            self.add_message("system", f"✅ Task added: {text[:50]}...")
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="Save", style='Success.TButton',
                  command=save_task, width=10).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", style='Secondary.TButton',
                  command=dialog.destroy, width=10).pack(side='right', padx=5)
    
    def refresh_tasks_list(self):
        """Refresh tasks list with filters"""
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        filtered_tasks = self.tasks
        
        # Apply status filter
        status_filter = self.task_filter.get()
        if status_filter == "active":
            filtered_tasks = [t for t in filtered_tasks if not t['completed']]
        elif status_filter == "completed":
            filtered_tasks = [t for t in filtered_tasks if t['completed']]
        
        # Add tasks to treeview
        for task in filtered_tasks:
            status = "✅" if task['completed'] else "⚡"
            
            # Color code priority
            priority = task.get('priority', 'medium')
            if priority == 'high':
                priority_display = "🔴 High"
            elif priority == 'medium':
                priority_display = "🟡 Medium"
            else:
                priority_display = "🟢 Low"
            
            category = task.get('category', 'general').capitalize()
            
            self.tasks_tree.insert('', 'end', iid=task['id'],
                                  values=(status, task['text'], priority_display, 
                                          category, task['added'][:16]))
    
    def toggle_task_completion(self):
        """Toggle task completion status"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("⚠️ No Selection", "Please select a task!")
            return
        
        item = selection[0]
        task_id = int(item)
        
        # Find and update task
        for task in self.tasks:
            if task['id'] == task_id:
                task['completed'] = not task['completed']
                if task['completed']:
                    task['completed_date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    messagebox.showinfo("✅ Task Completed", 
                                      f"Task marked as completed!")
                else:
                    task['completed_date'] = None
                    messagebox.showinfo("⚡ Task Reactivated", 
                                      f"Task marked as active!")
                
                self.save_task(task)
                break
        
        self.refresh_tasks_list()
        self.update_status()
    
    def edit_task_dialog(self):
        """Edit selected task"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("⚠️ No Selection", "Please select a task!")
            return
        
        item = selection[0]
        task_id = int(item)
        
        # Find task
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        if not task:
            return
        
        # Create edit dialog similar to add_task_dialog
        # (Implementation omitted for brevity - similar to add_task_dialog)
        messagebox.showinfo("✏️ Edit Task", "Edit feature would open here")
    
    def delete_selected_task(self):
        """Delete selected task"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("⚠️ No Selection", "Please select a task!")
            return
        
        if not messagebox.askyesno("🗑️ Confirm Delete", 
                                  "Delete selected task permanently?"):
            return
        
        item = selection[0]
        task_id = int(item)
        
        # Remove from database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("❌ Database Error", f"Failed to delete task: {e}")
            return
        
        # Remove from list
        self.tasks = [t for t in self.tasks if t['id'] != task_id]
        
        self.refresh_tasks_list()
        self.update_status()
        messagebox.showinfo("✅ Deleted", "Task deleted successfully!")
    
    def clear_completed_tasks(self):
        """Clear all completed tasks"""
        completed_tasks = [t for t in self.tasks if t['completed']]
        
        if not completed_tasks:
            messagebox.showinfo("ℹ️ No Tasks", "No completed tasks to delete!")
            return
        
        if not messagebox.askyesno("🗑️ Confirm Clear", 
                                  f"Delete {len(completed_tasks)} completed tasks?"):
            return
        
        # Remove from database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for task in completed_tasks:
                cursor.execute('DELETE FROM tasks WHERE id = ?', (task['id'],))
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("❌ Database Error", f"Failed to delete tasks: {e}")
            return
        
        # Remove from list
        self.tasks = [t for t in self.tasks if not t['completed']]
        
        self.refresh_tasks_list()
        self.update_status()
        messagebox.showinfo("✅ Cleared", f"Deleted {len(completed_tasks)} completed tasks!")
    
    # Note management methods
    def add_note_dialog(self):
        """Show modern dialog to add new note"""
        dialog = tk.Toplevel(self.root)
        dialog.title("➕ Add New Note")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.configure(bg=self.colors['background'])
        
        frame = ttk.Frame(dialog, style='Card.TFrame', padding=20)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="➕ Add New Note", style='Title.TLabel').pack(pady=(0, 20))
        
        ttk.Label(frame, text="Note Title:", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        title_entry = ttk.Entry(frame, width=50, style='Modern.TEntry')
        title_entry.pack(pady=(0, 10), fill='x')
        title_entry.focus()
        
        ttk.Label(frame, text="Tags (comma separated):", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        tags_entry = ttk.Entry(frame, width=50, style='Modern.TEntry')
        tags_entry.pack(pady=(0, 10), fill='x')
        
        ttk.Label(frame, text="Content:", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        content_text = scrolledtext.ScrolledText(frame, height=15, width=50, 
                                                font=("Segoe UI", 10))
        content_text.pack(pady=(0, 10), fill='both', expand=True)
        
        def save_note():
            title = title_entry.get().strip()
            content = content_text.get("1.0", tk.END).strip()
            tags = tags_entry.get().strip()
            
            if not title:
                messagebox.showwarning("⚠️ Input Required", "Please enter note title!")
                return
            
            if not content:
                content = "(Empty note)"
            
            note = {
                'title': title,
                'content': content,
                'created': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'tags': tags
            }
            
            self.notes.append(note)
            self.save_note(note)
            self.refresh_notes_list()
            self.update_status()
            dialog.destroy()
            
            self.add_message("system", f"✅ Note added: {title}")
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="Save", style='Success.TButton',
                  command=save_note, width=10).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", style='Secondary.TButton',
                  command=dialog.destroy, width=10).pack(side='right', padx=5)
    
    def refresh_notes_list(self):
        """Refresh notes list with search"""
        for item in self.notes_tree.get_children():
            self.notes_tree.delete(item)
        
        search_term = self.note_search_var.get().lower()
        
        for note in self.notes:
            # Check if note matches search
            matches = (search_term in note['title'].lower() or 
                      search_term in note.get('tags', '').lower() or
                      search_term in note['content'].lower())
            
            if search_term and not matches:
                continue
            
            self.notes_tree.insert('', 'end', iid=note['id'],
                                  values=(note['title'], note.get('tags', ''), 
                                          note['created'][:16]))
    
    def view_note(self):
        """View selected note"""
        selection = self.notes_tree.selection()
        if not selection:
            messagebox.showwarning("⚠️ No Selection", "Please select a note!")
            return
        
        item = selection[0]
        note_id = int(item)
        
        # Find note
        note = next((n for n in self.notes if n['id'] == note_id), None)
        if not note:
            return
        
        # Create view dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"📝 {note['title'][:30]}...")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.configure(bg=self.colors['background'])
        
        frame = ttk.Frame(dialog, style='Card.TFrame', padding=20)
        frame.pack(fill='both', expand=True)
        
        # Title
        ttk.Label(frame, text=note['title'], style='Title.TLabel',
                 wraplength=550).pack(anchor='w', pady=(0, 10))
        
        # Metadata
        meta_frame = ttk.Frame(frame)
        meta_frame.pack(anchor='w', pady=(0, 20), fill='x')
        
        ttk.Label(meta_frame, text=f"📅 Created: {note['created'][:16]}",
                 font=("Segoe UI", 9)).pack(side='left', padx=(0, 20))
        
        if note.get('tags'):
            ttk.Label(meta_frame, text=f"🏷️ Tags: {note['tags']}",
                     font=("Segoe UI", 9)).pack(side='left')
        
        # Content
        content_frame = ttk.LabelFrame(frame, text="Content", 
                                      style='Card.TFrame', padding=10)
        content_frame.pack(fill='both', expand=True, pady=10)
        
        content_text = scrolledtext.ScrolledText(content_frame, 
                                                font=("Segoe UI", 10))
        content_text.pack(fill='both', expand=True)
        content_text.insert('1.0', note['content'])
        content_text.config(state='disabled')
        
        # Close button
        ttk.Button(frame, text="Close", style='Secondary.TButton',
                  command=dialog.destroy, width=10).pack(pady=20)
    
    def delete_selected_note(self):
        """Delete selected note"""
        selection = self.notes_tree.selection()
        if not selection:
            messagebox.showwarning("⚠️ No Selection", "Please select a note!")
            return
        
        if not messagebox.askyesno("🗑️ Confirm Delete", 
                                  "Delete selected note permanently?"):
            return
        
        item = selection[0]
        note_id = int(item)
        
        # Remove from database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("❌ Database Error", f"Failed to delete note: {e}")
            return
        
        # Remove from list
        self.notes = [n for n in self.notes if n['id'] != note_id]
        
        self.refresh_notes_list()
        self.update_status()
        messagebox.showinfo("✅ Deleted", "Note deleted successfully!")
    
    # File management methods
    def upload_file(self):
        """Upload a file"""
        file_path = filedialog.askopenfilename(
            title="📁 Select File to Upload",
            filetypes=[
                ("📄 All Files", "*.*"),
                ("📊 PDF Files", "*.pdf"),
                ("📝 Text Files", "*.txt"),
                ("🖼️ Images", "*.png *.jpg *.jpeg *.gif"),
                ("📑 Documents", "*.docx *.doc *.pptx *.ppt")
            ]
        )
        
        if not file_path:
            return
        
        # Show upload progress
        progress = ttk.Progressbar(self.root, mode='indeterminate',
                                  style='Modern.Horizontal.TProgressbar')
        progress.place(relx=0.5, rely=0.5, anchor='center')
        progress.start()
        
        # Upload in thread
        def upload_thread():
            from enhanced_chatbot_pro import FileManager
            user_id = self.auth.current_user['id']
            success, file_id, message = self.file_manager.upload_file(file_path, user_id=user_id)
            
            self.root.after(0, lambda: complete_upload(success, message))
        
        def complete_upload(success, message):
            progress.stop()
            progress.destroy()
            
            if success:
                messagebox.showinfo("✅ Success", message)
                self.refresh_files_list()
            else:
                messagebox.showerror("❌ Upload Failed", message)
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def refresh_files_list(self):
        """Refresh files list"""
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        user_id = self.auth.current_user['id']
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM files WHERE user_id = ?', (user_id,))
            files = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"⚠️ Failed to load files: {e}")
            return
        
        for file in files:
            file_id, filename, original_name, file_path, file_type, file_size, uploaded_date, user_id, task_id, note_id = file
            
            # Format file size
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024*1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024*1024):.1f} MB"
            
            # Get file type icon
            file_icon = self.get_file_icon(file_type)
            
            self.files_tree.insert('', 'end', iid=file_id,
                                  values=(f"{file_icon} {original_name}", 
                                          file_type, size_str, uploaded_date[:16]))
    
    def get_file_icon(self, file_type):
        """Get appropriate icon for file type"""
        if not file_type:
            return "📄"
        
        file_type = file_type.lower()
        
        if '.pdf' in file_type:
            return "📊"
        elif any(ext in file_type for ext in ['.txt', '.md', '.rtf', '.json', '.xml']):
            return "📝"
        elif any(ext in file_type for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']):
            return "🖼️"
        elif any(ext in file_type for ext in ['.doc', '.docx']):
            return "📑"
        elif any(ext in file_type for ext in ['.xls', '.xlsx', '.csv']):
            return "📊"
        elif any(ext in file_type for ext in ['.zip', '.rar', '.7z', '.tar', '.gz']):
            return "📦"
        elif any(ext in file_type for ext in ['.mp3', '.wav', '.flac']):
            return "🎵"
        elif any(ext in file_type for ext in ['.mp4', '.avi', '.mkv', '.mov']):
            return "🎬"
        else:
            return "📄"
    
    def open_selected_file(self):
        """Open selected file"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("⚠️ No Selection", "Please select a file!")
            return
        
        file_id = int(selection[0])
        
        # Get file path from database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT file_path FROM files WHERE id = ?', (file_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                file_path = result[0]
                webbrowser.open(f"file://{os.path.abspath(file_path)}")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Could not open file: {str(e)}")
    
    def delete_selected_file(self):
        """Delete selected file"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("⚠️ No Selection", "Please select a file!")
            return
        
        if not messagebox.askyesno("🗑️ Confirm Delete", 
                                  "Delete this file permanently?\nThis action cannot be undone."):
            return
        
        file_id = int(selection[0])
        
        # Delete file and database record
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT file_path FROM files WHERE id = ?', (file_id,))
            result = cursor.fetchone()
            
            if result:
                file_path = result[0]
                try:
                    os.remove(file_path)
                except:
                    pass
                
                cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
                conn.commit()
            
            conn.close()
            self.refresh_files_list()
            messagebox.showinfo("✅ Deleted", "File deleted successfully!")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to delete file: {str(e)}")
    
    def save_task(self, task):
        """Save task to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            user_id = self.auth.current_user['id']
            
            if 'id' in task and task['id']:
                cursor.execute('''
                    UPDATE tasks 
                    SET text=?, completed=?, priority=?, completed_date=?, category=?
                    WHERE id=? AND user_id=?
                ''', (task['text'], int(task['completed']), task['priority'],
                      task.get('completed_date'), task.get('category', 'general'), 
                      task['id'], user_id))
            else:
                cursor.execute('''
                    INSERT INTO tasks (text, completed, priority, added_date, category, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (task['text'], int(task['completed']), task.get('priority', 'medium'),
                      task['added'], task.get('category', 'general'), user_id))
                task['id'] = cursor.lastrowid
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Failed to save task: {e}")
    
    def save_note(self, note):
        """Save note to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            user_id = self.auth.current_user['id']
            
            if 'id' in note and note['id']:
                cursor.execute('''
                    UPDATE notes 
                    SET title=?, content=?, modified_date=?, tags=?
                    WHERE id=? AND user_id=?
                ''', (note['title'], note['content'], 
                      datetime.now().strftime("%Y-%m-%d %H:%M"), 
                      note.get('tags', ''), note['id'], user_id))
            else:
                cursor.execute('''
                    INSERT INTO notes (title, content, created_date, modified_date, tags, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (note['title'], note['content'], note['created'], note['created'],
                      note.get('tags', ''), user_id))
                note['id'] = cursor.lastrowid
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Failed to save note: {e}")
    
    # Export methods
    def export_to_pdf(self):
        """Export data to PDF"""
        if not PDF_AVAILABLE:
            messagebox.showerror("❌ PDF Not Available", 
                               "PDF export requires reportlab library.\n\n"
                               "💡 Install with: pip install reportlab")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("📊 PDF files", "*.pdf")],
            initialfile=f"chatbot_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
        if not filename:
            return
        
        # Show progress
        progress = ttk.Progressbar(self.root, mode='indeterminate',
                                  style='Modern.Horizontal.TProgressbar')
        progress.place(relx=0.5, rely=0.5, anchor='center')
        progress.start()
        
        def export_thread():
            from enhanced_chatbot_pro import ExportManager
            export_manager = ExportManager(self.tasks, self.notes)
            success, message = export_manager.export_to_pdf(filename)
            
            self.root.after(0, lambda: complete_export(success, message))
        
        def complete_export(success, message):
            progress.stop()
            progress.destroy()
            
            if success:
                if messagebox.askyesno("✅ Success", message + "\n\nOpen the file now?"):
                    webbrowser.open(f"file://{os.path.abspath(filename)}")
            else:
                messagebox.showerror("❌ Export Failed", message)
        
        threading.Thread(target=export_thread, daemon=True).start()
    
    def export_to_markdown(self):
        """Export data to Markdown"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("📝 Markdown files", "*.md"), ("📄 Text files", "*.txt")],
            initialfile=f"chatbot_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        
        if not filename:
            return
        
        progress = ttk.Progressbar(self.root, mode='indeterminate',
                                  style='Modern.Horizontal.TProgressbar')
        progress.place(relx=0.5, rely=0.5, anchor='center')
        progress.start()
        
        def export_thread():
            from enhanced_chatbot_pro import ExportManager
            export_manager = ExportManager(self.tasks, self.notes)
            success, message = export_manager.export_to_markdown(filename)
            
            self.root.after(0, lambda: complete_export(success, message))
        
        def complete_export(success, message):
            progress.stop()
            progress.destroy()
            
            if success:
                if messagebox.askyesno("✅ Success", message + "\n\nOpen the file now?"):
                    webbrowser.open(f"file://{os.path.abspath(filename)}")
            else:
                messagebox.showerror("❌ Export Failed", message)
        
        threading.Thread(target=export_thread, daemon=True).start()
    
    def export_analytics(self):
        """Export analytics report"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("📄 Text files", "*.txt"), ("📝 Markdown files", "*.md")],
            initialfile=f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.generate_ascii_chart())
            
            messagebox.showinfo("✅ Success", 
                              f"Analytics report exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("❌ Export Failed", f"Error: {str(e)}")
    
    def import_data(self):
        """Import data from JSON"""
        filename = filedialog.askopenfilename(
            title="📥 Import Data",
            filetypes=[("📊 JSON files", "*.json"), ("📄 All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            task_count = len(import_data.get('tasks', []))
            note_count = len(import_data.get('notes', []))
            
            if not messagebox.askyesno("📥 Confirm Import",
                                      f"Import {task_count} tasks and {note_count} notes?\n\n"
                                      "This will add to your existing data."):
                return
            
            # Import tasks
            imported_tasks = 0
            for task in import_data.get('tasks', []):
                task['id'] = None
                self.tasks.append(task)
                self.save_task(task)
                imported_tasks += 1
            
            # Import notes
            imported_notes = 0
            for note in import_data.get('notes', []):
                note['id'] = None
                self.notes.append(note)
                self.save_note(note)
                imported_notes += 1
            
            self.update_status()
            
            messagebox.showinfo("✅ Import Successful", 
                              f"✓ Imported:\n"
                              f"📋 Tasks: {imported_tasks}\n"
                              f"📝 Notes: {imported_notes}")
        except Exception as e:
            messagebox.showerror("❌ Import Failed", f"Error: {str(e)}")
    
    # AI Settings
    def show_ai_settings(self):
        """Show modern AI configuration dialog"""
        from enhanced_chatbot_pro import AIBackend
        
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ AI Settings")
        settings_window.geometry("500x500")
        settings_window.transient(self.root)
        settings_window.configure(bg=self.colors['background'])
        
        # Center window
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (settings_window.winfo_screenheight() // 2) - (500 // 2)
        settings_window.geometry(f"500x500+{x}+{y}")
        
        frame = ttk.Frame(settings_window, style='Card.TFrame', padding=25)
        frame.pack(fill='both', expand=True)
        
        # Title
        ttk.Label(frame, text="⚙️ AI Backend Configuration", 
                 style='Title.TLabel').pack(pady=(0, 20))
        
        # Provider selection
        ttk.Label(frame, text="AI Provider:", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        provider_var = tk.StringVar(value=self.ai_backend.provider)
        provider_combo = ttk.Combobox(frame, textvariable=provider_var, 
                                     values=['local', 'openai', 'anthropic'], 
                                     state='readonly', style='Modern.TCombobox')
        provider_combo.pack(pady=(0, 10), fill='x')
        
        # API Key
        ttk.Label(frame, text="API Key:", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        api_key_entry = ttk.Entry(frame, style='Modern.TEntry', show="*")
        if self.ai_backend.api_key:
            api_key_entry.insert(0, self.ai_backend.api_key)
        api_key_entry.pack(pady=(0, 10), fill='x')
        
        # Model
        ttk.Label(frame, text="Model (optional):", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        model_entry = ttk.Entry(frame, style='Modern.TEntry')
        if self.ai_backend.model:
            model_entry.insert(0, self.ai_backend.model)
        model_entry.pack(pady=(0, 20), fill='x')
        
        # Info text
        info_frame = ttk.LabelFrame(frame, text="📚 Configuration Guide", 
                                   style='Card.TFrame', padding=15)
        info_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        info_text = """
🤖 **Local:** No API needed, basic responses
⚡ **OpenAI:** Requires OpenAI API key
   • Models: gpt-4, gpt-3.5-turbo
🎨 **Anthropic:** Requires Anthropic API key
   • Models: claude-3-sonnet-20240229

🔑 **Get API keys from:**
• OpenAI: https://platform.openai.com
• Anthropic: https://console.anthropic.com

💡 **Tip:** Start with Local if you don't have API keys
        """
        
        info_label = ttk.Label(info_frame, text=info_text, 
                              font=("Segoe UI", 9), justify='left')
        info_label.pack()
        
        def save_settings():
            provider = provider_var.get()
            api_key = api_key_entry.get().strip()
            model = model_entry.get().strip()
            
            self.ai_backend.set_provider(provider, api_key if api_key else None, model if model else None)
            
            # Save to database
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                user_id = self.auth.current_user['id']
                
                cursor.execute('''
                    INSERT OR REPLACE INTO settings (user_id, setting_key, setting_value)
                    VALUES (?, ?, ?)
                ''', (user_id, 'ai_provider', provider))
                
                if api_key:
                    cursor.execute('''
                        INSERT OR REPLACE INTO settings (user_id, setting_key, setting_value)
                        VALUES (?, ?, ?)
                    ''', (user_id, 'ai_api_key', api_key))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("✅ Settings Saved", 
                                  "AI settings updated successfully!")
                settings_window.destroy()
                self.update_status()
            except Exception as e:
                messagebox.showerror("❌ Save Failed", f"Failed to save settings: {e}")
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="Save", style='Success.TButton',
                  command=save_settings, width=10).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", style='Secondary.TButton',
                  command=settings_window.destroy, width=10).pack(side='right', padx=5)
    
    # Guest features
    def upgrade_guest(self):
        """Upgrade guest to permanent account"""
        if not self.auth.current_user.get('is_guest', False):
            messagebox.showinfo("ℹ️ Already Registered", 
                              "You already have a permanent account!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("⭐ Upgrade to Permanent Account")
        dialog.geometry("450x450")
        dialog.transient(self.root)
        dialog.configure(bg=self.colors['background'])
        
        frame = ttk.Frame(dialog, style='Card.TFrame', padding=25)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="⭐ Create Permanent Account", 
                 style='Title.TLabel').pack(pady=(0, 10))
        
        ttk.Label(frame, text="Keep your data permanently by creating an account.",
                 font=("Segoe UI", 10)).pack(pady=(0, 20))
        
        ttk.Label(frame, text="Choose a username:", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        username_entry = ttk.Entry(frame, style='Modern.TEntry')
        username_entry.pack(pady=(0, 10), fill='x')
        
        ttk.Label(frame, text="Choose a password:", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        password_entry = ttk.Entry(frame, style='Modern.TEntry', show="*")
        password_entry.pack(pady=(0, 10), fill='x')
        
        ttk.Label(frame, text="Confirm password:", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        confirm_entry = ttk.Entry(frame, style='Modern.TEntry', show="*")
        confirm_entry.pack(pady=(0, 10), fill='x')
        
        ttk.Label(frame, text="Email (optional):", font=("Segoe UI", 10)).pack(anchor='w', pady=(0, 5))
        email_entry = ttk.Entry(frame, style='Modern.TEntry')
        email_entry.pack(pady=(0, 20), fill='x')
        
        def create_account():
            username = username_entry.get().strip()
            password = password_entry.get()
            confirm = confirm_entry.get()
            email = email_entry.get().strip()
            
            if not username or not password:
                messagebox.showwarning("⚠️ Input Required", 
                                     "Please enter username and password!")
                return
            
            if len(password) < 6:
                messagebox.showwarning("⚠️ Weak Password", 
                                     "Password must be at least 6 characters!")
                return
            
            if password != confirm:
                messagebox.showwarning("⚠️ Password Mismatch", 
                                     "Passwords don't match!")
                return
            
            # Create new account
            success, message = self.auth.register_user(username, password, email, is_guest=False)
            if not success:
                messagebox.showerror("❌ Registration Failed", message)
                return
            
            # Get current user ID and data
            old_user_id = self.auth.current_user['id']
            
            # Login to new account
            login_success, login_message = self.auth.login_user(username, password)
            if not login_success:
                messagebox.showerror("❌ Login Failed", login_message)
                return
            
            # Transfer data from guest to new account
            self.transfer_guest_data(old_user_id, self.auth.current_user['id'])
            
            dialog.destroy()
            messagebox.showinfo("✅ Success!", 
                              "🎉 Account created successfully!\n\n"
                              "✨ All your guest data has been transferred.\n"
                              "🔒 You're now using a permanent account.")
            
            # Refresh UI to show registered user status
            self.setup_ui()
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="Create Account", style='Success.TButton',
                  command=create_account, width=15).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", style='Secondary.TButton',
                  command=dialog.destroy, width=10).pack(side='right', padx=5)
    
    def transfer_guest_data(self, old_user_id, new_user_id):
        """Transfer data from guest account to new account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Transfer tasks
            cursor.execute('UPDATE tasks SET user_id = ? WHERE user_id = ?', (new_user_id, old_user_id))
            
            # Transfer notes
            cursor.execute('UPDATE notes SET user_id = ? WHERE user_id = ?', (new_user_id, old_user_id))
            
            # Transfer conversations
            cursor.execute('UPDATE conversations SET user_id = ? WHERE user_id = ?', (new_user_id, old_user_id))
            
            # Transfer files
            cursor.execute('UPDATE files SET user_id = ? WHERE user_id = ?', (new_user_id, old_user_id))
            
            # Transfer settings
            cursor.execute('UPDATE settings SET user_id = ? WHERE user_id = ?', (new_user_id, old_user_id))
            
            # Delete old guest user
            cursor.execute('DELETE FROM users WHERE id = ?', (old_user_id,))
            
            conn.commit()
            conn.close()
            
            # Reload data
            self.load_data()
            self.update_status()
            
        except Exception as e:
            messagebox.showerror("❌ Transfer Failed", f"Failed to transfer data: {e}")
    
    def show_guest_info(self):
        """Show guest information"""
        info = """
👥 **GUEST ACCOUNT INFORMATION**

🎉 **You're currently using a guest account.**

✅ **What you get:**
• Full access to all premium features
• AI backend configuration (OpenAI/Claude)
• File uploads and attachments
• PDF and Markdown export
• Local data storage

⚠️ **Important notes:**
• Guest data may be cleaned up after 24 hours of inactivity
• For permanent storage, create an account
• You can upgrade anytime from File menu

💡 **Tips:**
• Export important data regularly
• Use the upgrade feature to keep your data
• Guest accounts are perfect for trying out features

✨ **To upgrade:** File → ⭐ Create Permanent Account
        """
        
        messagebox.showinfo("👥 Guest Account Info", info)
    
    def show_about(self):
        """Show about dialog"""
        version = "2.1"
        is_guest = self.auth.current_user.get('is_guest', False)
        user_type = "👥 Guest" if is_guest else "👤 Registered User"
        
        about_text = f"""
🤖 **AI Project Assistant Pro**
**Version {version}**

👤 **User:** {self.auth.current_user['username']}
🎯 **Status:** {user_type}

🌟 **Premium Features:**
• AI Backend Integration (OpenAI/Claude)
• User Authentication System
• Guest Access Mode
• File Attachments Management
• PDF & Markdown Export
• Advanced Analytics Dashboard

🛠️ **Built with:** Python, Tkinter, SQLite

📧 **Support:** GitHub Issues
🔗 **GitHub:** https://github.com/Khan-Feroz211/AI-CHATBOT
        """
        
        messagebox.showinfo("ℹ️ About", about_text)
    
    def open_github(self):
        """Open GitHub repository"""
        try:
            webbrowser.open("https://github.com/Khan-Feroz211/AI-CHATBOT")
        except:
            messagebox.showinfo("🌐 GitHub", 
                              "GitHub Repository:\n"
                              "https://github.com/Khan-Feroz211/AI-CHATBOT")
    
    def report_issue(self):
        """Report an issue"""
        messagebox.showinfo("📧 Report Issue", 
                          "To report an issue or suggest improvements:\n\n"
                          "1. Visit the GitHub repository\n"
                          "2. Create a new issue\n"
                          "3. Describe the problem or suggestion\n\n"
                          "GitHub: https://github.com/Khan-Feroz211/AI-CHATBOT")
    
    def show_user_guide(self):
        """Show user guide"""
        is_guest = self.auth.current_user.get('is_guest', False)
        
        guide = f"""
🎯 **QUICK START GUIDE** - Pro Version {'(Guest Mode)' if is_guest else '(Registered)'}

{'👥 **GUEST MODE FEATURES:**' if is_guest else '👤 **REGISTERED FEATURES:**'}
• Tasks, Notes, Files, Analytics
• AI Chat with configurable backend
• PDF/Markdown Export
• Data saved {'temporarily (24h)' if is_guest else 'permanently'}

📋 **1. TASK MANAGEMENT**
   • Add tasks in Tasks tab or via chat
   • Set priority (High/Medium/Low)
   • Mark as complete
   • Filter and organize tasks

📝 **2. NOTES & FILES**
   • Create notes with tags
   • Upload files for reference
   • Search and organize content

🤖 **3. AI ASSISTANT**
   • Chat naturally with the AI
   • Ask for help or suggestions
   • Configure AI backend in settings

📊 **4. ANALYTICS & EXPORT**
   • Track your productivity
   • Export data to PDF/Markdown
   • View detailed statistics

💡 **TIPS:**
• Type 'help' in chat for assistance
• Use filters to focus on important tasks
• Configure AI for smarter responses
• Export regularly for backup
{'• ⭐ Upgrade to save permanently' if is_guest else ''}
        """
        
        messagebox.showinfo("📖 User Guide", guide)
    
    def cleanup_database(self):
        """Clean up database (remove orphaned records)"""
        if not messagebox.askyesno("🧹 Cleanup Database", 
                                  "Clean up database?\n\n"
                                  "This will remove orphaned records and optimize performance."):
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Remove tasks without users
            cursor.execute('DELETE FROM tasks WHERE user_id NOT IN (SELECT id FROM users)')
            
            # Remove notes without users
            cursor.execute('DELETE FROM notes WHERE user_id NOT IN (SELECT id FROM users)')
            
            # Remove conversations without users
            cursor.execute('DELETE FROM conversations WHERE user_id NOT IN (SELECT id FROM users)')
            
            # Remove files without users
            cursor.execute('DELETE FROM files WHERE user_id NOT IN (SELECT id FROM users)')
            
            # Remove settings without users
            cursor.execute('DELETE FROM settings WHERE user_id NOT IN (SELECT id FROM users)')
            
            # Vacuum database
            cursor.execute('VACUUM')
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("✅ Cleanup Complete", 
                              "Database cleaned up successfully!")
        except Exception as e:
            messagebox.showerror("❌ Cleanup Failed", f"Failed to clean database: {e}")
    
    def refresh_all_data(self):
        """Refresh all data from database"""
        self.load_data()
        self.refresh_tasks_list()
        self.refresh_notes_list()
        self.refresh_files_list()
        self.update_status()
        messagebox.showinfo("🔄 Refresh Complete", "All data refreshed from database!")
    
    def clear_chat(self):
        """Clear chat history"""
        if messagebox.askyesno("🗑️ Clear Chat", 
                              "Clear all chat messages?\n\n"
                              "This action cannot be undone."):
            self.chat_display.config(state='normal')
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state='disabled')
            self.conversation_history = []
            
            self.add_message("system", "💬 Chat cleared.")
    
    def logout(self):
        """Logout user"""
        if messagebox.askyesno("🚪 Logout", 
                              "Are you sure you want to logout?"):
            was_guest = self.auth.logout_user()
            
            if was_guest:
                # Clean up guest user on logout
                self.auth.cleanup_old_guest_users()
            
            self.root.destroy()
            # Restart the app
            main()
    
    def auto_save(self):
        """Auto-save data periodically"""
        # Save tasks and notes periodically
        for task in self.tasks:
            self.save_task(task)
        
        for note in self.notes:
            self.save_note(note)
        
        # Schedule next auto-save
        self.root.after(30000, self.auto_save)  # Every 30 seconds
    
    def on_closing(self):
        """Handle window close"""
        if messagebox.askokcancel("❌ Quit", 
                                 "Are you sure you want to quit?\n\n"
                                 "All data is saved automatically."):
            self.root.destroy()


def main():
    root = tk.Tk()
    app = EnhancedChatbotPro(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

