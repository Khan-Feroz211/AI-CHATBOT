import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import json
from datetime import datetime

class SimpleChatbotDemo:
    """Lightweight chatbot demo - easy to show and modify"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Project Assistant Demo")
        self.root.geometry("800x600")
        
        # Simple in-memory storage (no files for demo)
        self.tasks = []
        self.notes = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Chat tab
        self.setup_chat_tab()
        
        # Tasks tab
        self.setup_tasks_tab()
        
        # Notes tab
        self.setup_notes_tab()
        
    def setup_chat_tab(self):
        chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(chat_frame, text='💬 Chat')
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, height=20, font=("Arial", 10)
        )
        self.chat_display.pack(padx=10, pady=10, fill='both', expand=True)
        self.chat_display.config(state='disabled')
        
        # Input area
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill='x', padx=10, pady=5)
        
        self.chat_input = ttk.Entry(input_frame, font=("Arial", 10))
        self.chat_input.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.chat_input.bind('<Return>', lambda e: self.send_message())
        
        ttk.Button(input_frame, text="Send", command=self.send_message).pack(side='right')
        
        # Welcome message
        self.add_message("Bot", "👋 Welcome! I'm your Project Assistant Demo.\n\n"
                        "Try asking:\n"
                        "• 'show my tasks'\n"
                        "• 'help with Python'\n"
                        "• 'how do I start?'\n\n"
                        "Use the tabs to add tasks and notes!")
        
    def setup_tasks_tab(self):
        tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(tasks_frame, text='✅ Tasks')
        
        # Add task section
        add_frame = ttk.LabelFrame(tasks_frame, text="Quick Add Task", padding=10)
        add_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(add_frame, text="Task:").pack(anchor='w')
        self.task_input = ttk.Entry(add_frame, width=50)
        self.task_input.pack(fill='x', pady=5)
        
        ttk.Button(add_frame, text="➕ Add Task", 
                  command=self.add_task).pack(anchor='e', pady=5)
        
        # Task list
        list_frame = ttk.LabelFrame(tasks_frame, text="Your Tasks", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tasks_list = tk.Listbox(list_frame, height=12, font=("Arial", 10))
        self.tasks_list.pack(fill='both', expand=True)
        
        # Buttons
        btn_frame = ttk.Frame(tasks_frame)
        btn_frame.pack(padx=10, pady=5)
        
        ttk.Button(btn_frame, text="✓ Complete", 
                  command=self.complete_task).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑 Delete", 
                  command=self.delete_task).pack(side='left', padx=5)
        
    def setup_notes_tab(self):
        notes_frame = ttk.Frame(self.notebook)
        self.notebook.add(notes_frame, text='📝 Notes')
        
        # Add note section
        add_frame = ttk.LabelFrame(notes_frame, text="Quick Add Note", padding=10)
        add_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(add_frame, text="Title:").pack(anchor='w')
        self.note_title = ttk.Entry(add_frame, width=50)
        self.note_title.pack(fill='x', pady=5)
        
        ttk.Label(add_frame, text="Content:").pack(anchor='w')
        self.note_content = scrolledtext.ScrolledText(add_frame, height=4)
        self.note_content.pack(fill='x', pady=5)
        
        ttk.Button(add_frame, text="💾 Save Note", 
                  command=self.add_note).pack(anchor='e', pady=5)
        
        # Notes list
        list_frame = ttk.LabelFrame(notes_frame, text="Your Notes", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.notes_list = tk.Listbox(list_frame, height=8, font=("Arial", 10))
        self.notes_list.pack(fill='both', expand=True)
        self.notes_list.bind('<<ListboxSelect>>', self.show_note)
        
        # Note display
        self.note_display = scrolledtext.ScrolledText(list_frame, height=6)
        self.note_display.pack(fill='both', expand=True, pady=(10, 0))
        
        # Delete button
        ttk.Button(notes_frame, text="🗑 Delete Note", 
                  command=self.delete_note).pack(pady=5)
        
    def add_message(self, sender, text):
        """Add message to chat"""
        self.chat_display.config(state='normal')
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {text}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        
    def send_message(self):
        """Handle chat messages"""
        msg = self.chat_input.get().strip()
        if not msg:
            return
            
        self.chat_input.delete(0, tk.END)
        self.add_message("You", msg)
        
        # Simple responses
        response = self.get_response(msg.lower())
        self.add_message("Bot", response)
        
    def get_response(self, msg):
        """Generate simple bot responses"""
        
        # Check for tasks query
        if any(word in msg for word in ['task', 'todo', 'do']):
            if self.tasks:
                task_list = "\n".join([f"• {t['text']}" for t in self.tasks[:5]])
                return f"Your current tasks:\n{task_list}\n\nUse the Tasks tab to manage them!"
            else:
                return "You don't have any tasks yet. Add some in the Tasks tab!"
        
        # Check for notes query
        elif any(word in msg for word in ['note', 'notes']):
            if self.notes:
                return f"You have {len(self.notes)} notes saved. Check the Notes tab to view them!"
            else:
                return "You don't have any notes yet. Create some in the Notes tab!"
        
        # Python help
        elif 'python' in msg or 'code' in msg or 'function' in msg:
            return ("🐍 Python Tips:\n\n"
                   "• Use descriptive variable names\n"
                   "• Add comments to explain complex logic\n"
                   "• Break large functions into smaller ones\n"
                   "• Test your code frequently\n\n"
                   "Need specific help? Ask me about loops, functions, or errors!")
        
        # Help request
        elif 'help' in msg or 'how' in msg or 'start' in msg:
            return ("I can help you:\n\n"
                   "1. 📋 Manage tasks - Use the Tasks tab\n"
                   "2. 📝 Organize notes - Use the Notes tab\n"
                   "3. 💻 Get coding tips - Ask about Python\n"
                   "4. 🎯 Stay organized - Track your work\n\n"
                   "What would you like to do?")
        
        # Greeting
        elif any(word in msg for word in ['hi', 'hello', 'hey']):
            return "👋 Hello! How can I help you with your project today?"
        
        # Default
        else:
            return ("I'm here to help! Try asking about:\n"
                   "• Your tasks and deadlines\n"
                   "• Python coding tips\n"
                   "• How to get started\n"
                   "• Your saved notes")
    
    def add_task(self):
        """Add a new task"""
        task_text = self.task_input.get().strip()
        if not task_text:
            messagebox.showwarning("Oops!", "Please enter a task!")
            return
            
        task = {
            'text': task_text,
            'completed': False,
            'added': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        self.tasks.append(task)
        self.tasks_list.insert(tk.END, f"○ {task_text}")
        self.task_input.delete(0, tk.END)
        
        messagebox.showinfo("Success!", "Task added! ✓")
        
    def complete_task(self):
        """Mark task as complete"""
        selection = self.tasks_list.curselection()
        if not selection:
            messagebox.showwarning("Oops!", "Please select a task!")
            return
            
        index = selection[0]
        self.tasks[index]['completed'] = True
        
        # Update display
        task_text = self.tasks[index]['text']
        self.tasks_list.delete(index)
        self.tasks_list.insert(index, f"✓ {task_text}")
        
        messagebox.showinfo("Great job!", "Task completed! 🎉")
        
    def delete_task(self):
        """Delete a task"""
        selection = self.tasks_list.curselection()
        if not selection:
            messagebox.showwarning("Oops!", "Please select a task!")
            return
            
        if messagebox.askyesno("Confirm", "Delete this task?"):
            index = selection[0]
            del self.tasks[index]
            self.tasks_list.delete(index)
            
    def add_note(self):
        """Add a new note"""
        title = self.note_title.get().strip()
        content = self.note_content.get("1.0", tk.END).strip()
        
        if not title:
            messagebox.showwarning("Oops!", "Please enter a title!")
            return
            
        if not content:
            messagebox.showwarning("Oops!", "Please enter some content!")
            return
            
        note = {
            'title': title,
            'content': content,
            'created': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        self.notes.append(note)
        self.notes_list.insert(tk.END, f"📄 {title}")
        
        self.note_title.delete(0, tk.END)
        self.note_content.delete("1.0", tk.END)
        
        messagebox.showinfo("Success!", "Note saved! 📝")
        
    def show_note(self, event):
        """Display selected note"""
        selection = self.notes_list.curselection()
        if not selection:
            return
            
        index = selection[0]
        note = self.notes[index]
        
        self.note_display.delete("1.0", tk.END)
        display_text = (f"Title: {note['title']}\n"
                       f"Created: {note['created']}\n"
                       f"\n{note['content']}")
        self.note_display.insert("1.0", display_text)
        
    def delete_note(self):
        """Delete a note"""
        selection = self.notes_list.curselection()
        if not selection:
            messagebox.showwarning("Oops!", "Please select a note!")
            return
            
        if messagebox.askyesno("Confirm", "Delete this note?"):
            index = selection[0]
            del self.notes[index]
            self.notes_list.delete(index)
            self.note_display.delete("1.0", tk.END)

def main():
    root = tk.Tk()
    app = SimpleChatbotDemo(root)
    root.mainloop()

if __name__ == "__main__":
    main()
