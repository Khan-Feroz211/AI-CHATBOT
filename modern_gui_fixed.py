"""
FIXED MODERN GUI - All Content Visible with Scrolling
This version ensures EVERYTHING is visible!
"""

import customtkinter as ctk
from tkinter import messagebox
import sqlite3
from datetime import datetime
from pathlib import Path
import random
import string
import threading
import secrets

try:
    from src.core.security import hash_password, verify_password, is_legacy_sha256_hash
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from src.core.security import hash_password, verify_password, is_legacy_sha256_hash

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class UserAuthSystem:
    """Handle user authentication"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.current_user = None
        self.setup_users_table()
    
    def setup_users_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
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
        return hash_password(password)
    
    def register_user(self, username, password, email="", is_guest=False):
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
    
    def login_user(self, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, role, is_guest, password_hash FROM users
            WHERE username = ?
        ''', (username,))
        user = cursor.fetchone()
        
        if user:
            stored_hash = user[4]
            if not verify_password(password, stored_hash):
                conn.close()
                return False, "Invalid credentials!"

            if is_legacy_sha256_hash(stored_hash):
                cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                              (self.hash_password(password), user[0]))

            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?',
                          (datetime.now().isoformat(), user[0]))
            conn.commit()
            self.current_user = {
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'is_guest': bool(user[3])
            }
            conn.close()
            return True, f"Welcome {username}!"
        conn.close()
        return False, "Invalid credentials!"
    
    def create_guest_user(self):
        timestamp = datetime.now().strftime("%H%M%S")
        random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        guest_username = f"guest_{timestamp}_{random_chars}"
        guest_password = secrets.token_urlsafe(16)
        
        success, _ = self.register_user(guest_username, guest_password, is_guest=True)
        if success:
            login_success, _ = self.login_user(guest_username, guest_password)
            if login_success:
                return True, f"Guest: {guest_username}"
        return False, "Failed to create guest"


class ModernLoginWindow:
    """Fixed login window with scrolling"""
    
    def __init__(self, auth_system, on_success_callback):
        self.auth = auth_system
        self.on_success = on_success_callback
        
        # Create window - BIGGER SIZE
        self.window = ctk.CTkToplevel()
        self.window.title("AI Project Assistant Pro - Welcome")
        self.window.geometry("700x900")  # ← INCREASED HEIGHT!
        
        # Center window
        self.center_window()
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Create scrollable UI
        self.create_scrollable_ui()
    
    def center_window(self):
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 900) // 2
        self.window.geometry(f"700x900+{x}+{y}")
    
    def create_scrollable_ui(self):
        """Create UI with scrollable frame"""
        
        # Create scrollable frame that contains everything
        scroll_frame = ctk.CTkScrollableFrame(self.window, width=650, height=850)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ============= HEADER =============
        header = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="🤖", font=("Arial", 72)).pack()
        ctk.CTkLabel(header, text="AI Project Assistant",
                    font=("Arial", 32, "bold")).pack(pady=(10, 0))
        ctk.CTkLabel(header, text="Professional Edition v2.1",
                    font=("Arial", 16), text_color="gray").pack()
        
        # ============= FEATURES =============
        features_card = ctk.CTkFrame(scroll_frame, corner_radius=15)
        features_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(features_card, text="✨ Premium Features",
                    font=("Arial", 16, "bold")).pack(pady=(20, 15))
        
        features = [
            "✓ AI-Powered Task Management",
            "✓ Smart Notes with Tags",
            "✓ File Uploads & Attachments",
            "✓ Guest Mode Available",
            "✓ PDF & Markdown Export",
            "✓ Advanced Analytics Dashboard"
        ]
        
        for feature in features:
            ctk.CTkLabel(features_card, text=feature,
                        font=("Arial", 13),
                        anchor="w").pack(padx=30, pady=3, anchor="w")
        
        ctk.CTkLabel(features_card, text="").pack(pady=10)
        
        # ============= GUEST BUTTON (HUGE!) =============
        guest_card = ctk.CTkFrame(scroll_frame, corner_radius=15,
                                 fg_color=("#2fa572", "#106A43"))
        guest_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(guest_card, text="🚀 Quick Start - No Registration",
                    font=("Arial", 18, "bold"),
                    text_color="white").pack(pady=(25, 10))
        
        ctk.CTkLabel(guest_card, 
                    text="Try all premium features instantly!",
                    font=("Arial", 13),
                    text_color="white").pack(pady=(0, 15))
        
        self.guest_btn = ctk.CTkButton(
            guest_card,
            text="🎮 START AS GUEST",
            font=("Arial", 18, "bold"),
            height=55,
            fg_color="white",
            text_color="#106A43",
            hover_color="#e0e0e0",
            command=self.start_guest
        )
        self.guest_btn.pack(pady=(0, 25), padx=40, fill="x")
        
        # ============= SEPARATOR =============
        sep = ctk.CTkFrame(scroll_frame, height=2, fg_color="gray30")
        sep.pack(fill="x", pady=20)
        
        ctk.CTkLabel(scroll_frame, text="or use your account",
                    font=("Arial", 12), text_color="gray").pack(pady=10)
        
        # ============= LOGIN/REGISTER TABS =============
        # Create tabs with MORE HEIGHT
        self.tabview = ctk.CTkTabview(scroll_frame, height=350)  # ← INCREASED HEIGHT!
        self.tabview.pack(fill="x", pady=(10, 20))
        
        # Add tabs
        self.tabview.add("🔑 Login")
        self.tabview.add("📝 Register")
        
        # ===== LOGIN TAB =====
        login_tab = self.tabview.tab("🔑 Login")
        
        ctk.CTkLabel(login_tab, text="Welcome Back!",
                    font=("Arial", 18, "bold")).pack(pady=(15, 20))
        
        ctk.CTkLabel(login_tab, text="Username:",
                    font=("Arial", 13)).pack(anchor="w", padx=20, pady=(10, 5))
        self.login_username = ctk.CTkEntry(login_tab, height=45,
                                          font=("Arial", 14),
                                          placeholder_text="Enter username")
        self.login_username.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(login_tab, text="Password:",
                    font=("Arial", 13)).pack(anchor="w", padx=20, pady=(0, 5))
        self.login_password = ctk.CTkEntry(login_tab, height=45,
                                          font=("Arial", 14),
                                          show="•",
                                          placeholder_text="Enter password")
        self.login_password.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(login_tab, text="LOGIN",
                     font=("Arial", 15, "bold"),
                     height=50,
                     command=self.do_login).pack(fill="x", padx=20, pady=(0, 20))
        
        self.login_password.bind('<Return>', lambda e: self.do_login())
        
        # ===== REGISTER TAB =====
        register_tab = self.tabview.tab("📝 Register")
        
        ctk.CTkLabel(register_tab, text="Create Account",
                    font=("Arial", 18, "bold")).pack(pady=(15, 20))
        
        ctk.CTkLabel(register_tab, text="Username:",
                    font=("Arial", 12)).pack(anchor="w", padx=20, pady=(5, 3))
        self.reg_username = ctk.CTkEntry(register_tab, height=40,
                                        font=("Arial", 13))
        self.reg_username.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(register_tab, text="Password:",
                    font=("Arial", 12)).pack(anchor="w", padx=20, pady=(0, 3))
        self.reg_password = ctk.CTkEntry(register_tab, height=40,
                                        font=("Arial", 13), show="•")
        self.reg_password.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(register_tab, text="Confirm Password:",
                    font=("Arial", 12)).pack(anchor="w", padx=20, pady=(0, 3))
        self.reg_confirm = ctk.CTkEntry(register_tab, height=40,
                                       font=("Arial", 13), show="•")
        self.reg_confirm.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkButton(register_tab, text="CREATE ACCOUNT",
                     font=("Arial", 14, "bold"),
                     height=45,
                     command=self.do_register).pack(fill="x", padx=20, pady=(0, 20))
        
        self.reg_confirm.bind('<Return>', lambda e: self.do_register())
        
        # ============= FOOTER =============
        footer = ctk.CTkLabel(scroll_frame,
                             text="💡 Guest users get full access to all features!",
                             font=("Arial", 11),
                             text_color="gray")
        footer.pack(pady=20)
    
    def start_guest(self):
        self.guest_btn.configure(state="disabled", text="Creating session...")
        
        def create():
            success, message = self.auth.create_guest_user()
            self.window.after(0, lambda: self.finish_guest(success, message))
        
        threading.Thread(target=create, daemon=True).start()
    
    def finish_guest(self, success, message):
        if success:
            messagebox.showinfo("Success!", f"✅ {message}\n\nWelcome to AI Project Assistant!")
            self.window.destroy()
            self.on_success()
        else:
            self.guest_btn.configure(state="normal", text="🎮 START AS GUEST")
            messagebox.showerror("Error", message)
    
    def do_login(self):
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        if not username or not password:
            messagebox.showwarning("Required", "Please enter both username and password!")
            return
        
        success, message = self.auth.login_user(username, password)
        if success:
            messagebox.showinfo("Success!", f"✅ {message}")
            self.window.destroy()
            self.on_success()
        else:
            messagebox.showerror("Login Failed", message)
    
    def do_register(self):
        username = self.reg_username.get().strip()
        password = self.reg_password.get()
        confirm = self.reg_confirm.get()
        
        if not username or not password:
            messagebox.showwarning("Required", "Please fill all fields!")
            return
        
        if len(password) < 6:
            messagebox.showwarning("Weak Password", "Password must be at least 6 characters!")
            return
        
        if password != confirm:
            messagebox.showwarning("Mismatch", "Passwords don't match!")
            return
        
        success, message = self.auth.register_user(username, password)
        if success:
            messagebox.showinfo("Success!", "✅ Account created!\n\nPlease login now.")
            self.tabview.set("🔑 Login")
            self.login_username.delete(0, "end")
            self.login_username.insert(0, username)
        else:
            messagebox.showerror("Failed", message)
    
    def on_close(self):
        if messagebox.askyesno("Exit", "Exit application?"):
            self.window.quit()


class ModernApp:
    """Main application"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("AI Project Assistant Pro")
        self.root.geometry("1200x800")
        
        # Setup
        self.data_dir = Path("chatbot_data")
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "chatbot.db"
        self.auth = UserAuthSystem(self.db_path)
        
        # Hide main window
        self.root.withdraw()
        
        # Show login
        self.show_login()
    
    def show_login(self):
        login = ModernLoginWindow(self.auth, self.on_success)
    
    def on_success(self):
        self.root.deiconify()
        self.setup_main()
    
    def setup_main(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Header
        header = ctk.CTkFrame(self.root, height=70, corner_radius=0,
                             fg_color=("#1f538d", "#1f538d"))
        header.pack(fill="x")
        header.pack_propagate(False)
        
        username = self.auth.current_user['username']
        is_guest = self.auth.current_user.get('is_guest', False)
        
        icon = "👥" if is_guest else "👤"
        ctk.CTkLabel(header, text=f"{icon} {username}",
                    font=("Arial", 16, "bold"),
                    text_color="white").pack(side="left", padx=30)
        
        if is_guest:
            ctk.CTkButton(header, text="⭐ Upgrade Account",
                         width=150, height=40,
                         fg_color="#2fa572",
                         hover_color="#25824f").pack(side="right", padx=10)
        
        ctk.CTkButton(header, text="🚪 Logout",
                     width=120, height=40,
                     command=self.logout).pack(side="right", padx=10)
        
        # Main content
        main = ctk.CTkFrame(self.root)
        main.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(main, text="🎉 Welcome to AI Project Assistant Pro!",
                    font=("Arial", 32, "bold")).pack(pady=(100, 20))
        
        ctk.CTkLabel(main, text="Your productivity workspace is ready",
                    font=("Arial", 18),
                    text_color="gray").pack()
        
        # Quick actions
        actions = ctk.CTkFrame(main)
        actions.pack(pady=50)
        
        btns = [
            ("📋 Tasks", "#3498db"),
            ("📝 Notes", "#9b59b6"),
            ("💬 Chat", "#2ecc71"),
            ("📊 Analytics", "#e74c3c")
        ]
        
        for text, color in btns:
            ctk.CTkButton(actions, text=text,
                         font=("Arial", 16, "bold"),
                         width=200, height=60,
                         fg_color=color).pack(side="left", padx=10)
    
    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.auth.current_user = None
            self.root.withdraw()
            self.show_login()
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ModernApp()
    app.run()
