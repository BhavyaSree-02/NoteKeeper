import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('notepad.db')
cursor = conn.cursor()

# Create the notes table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS notepad (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    password TEXT,
    hidden INTEGER DEFAULT 0
)
''')
conn.commit()


tab_note_id = {}   

def _get_current_text_widget():
    """Return the Text widget of the selected tab, else None."""
    try:
        current_tab = notebook.select()
        if not current_tab:
            return None
        frame = root.nametowidget(current_tab)
        # find Text widget inside this tab frame
        for child in frame.winfo_children():
            if isinstance(child, tk.Text):
                return child
        return None
    except Exception:
        return None

def _open_note_tab(note_id, title, content):
    """Create a tab (Frame + Text) and store mapping to DB note_id."""
    frame = ttk.Frame(notebook)
    note_content = tk.Text(frame, width=80, height=20, wrap="word")
    note_content.pack(fill=tk.BOTH, expand=True)
    note_content.insert(tk.END, content)

    notebook.add(frame, text=title)
    tab_id = notebook.tabs()[-1]       # newest tab id string
    tab_note_id[tab_id] = note_id
    notebook.select(frame)

def add_note():
    def save_note():
        title = title_entry.get().strip()
        content = content_entry.get("1.0", tk.END).rstrip("\n")
        password = password_entry.get().strip()
        hidden = hidden_var.get()

        if not title:
            messagebox.showerror("Error", "Title cannot be empty.")
            return

        cursor.execute(
            'INSERT INTO notepad (title, content, password, hidden) VALUES (?, ?, ?, ?)',
            (title, content, password, hidden)
        )
        conn.commit()

        note_id = cursor.lastrowid  

       
        # (Hidden notes should be opened only after password)
        if hidden == 0 and (password == "" or password is None):
            _open_note_tab(note_id, title, content)

        new_note_window.destroy()

    new_note_window = tk.Toplevel(root)
    new_note_window.title("New Note")

    title_label = ttk.Label(new_note_window, text="Title:")
    title_label.grid(row=0, column=0, padx=10, pady=10, sticky="W")

    title_entry = ttk.Entry(new_note_window, width=80)
    title_entry.grid(row=0, column=1, padx=10, pady=10)

    content_label = ttk.Label(new_note_window, text="Content:")
    content_label.grid(row=1, column=0, padx=10, pady=10, sticky="W")

    content_entry = tk.Text(new_note_window, width=80, height=10)
    content_entry.grid(row=1, column=1, padx=10, pady=10)

    password_label = ttk.Label(new_note_window, text="Password:")
    password_label.grid(row=2, column=0, padx=10, pady=10, sticky="W")

    password_entry = ttk.Entry(new_note_window, width=30, show='*')
    password_entry.grid(row=2, column=1, padx=10, pady=10, sticky="W")

    hidden_var = tk.IntVar()
    hidden_checkbox = ttk.Checkbutton(new_note_window, text="Hide Note", variable=hidden_var)
    hidden_checkbox.grid(row=3, columnspan=2, padx=10, pady=10, sticky="W")

    save_button = ttk.Button(new_note_window, text="Save", command=save_note)
    save_button.grid(row=4, columnspan=2, padx=10, pady=10)

def load_notes():
    cursor.execute('SELECT id, title, content FROM notepad WHERE hidden=0 AND (password IS NULL OR password="")')
    rows = cursor.fetchall()

    for note_id, title, content in rows:
        _open_note_tab(note_id, title, content)

def show_hidden_notes():
    password = simpledialog.askstring("Show Hidden Note", "Enter the password for the hidden note:", show="*")
    if password is None:
        return

    # do NOT hide all tabs; just open the hidden note if password matches
    cursor.execute('SELECT id, title, content FROM notepad WHERE password=? AND hidden=1', (password,))
    row = cursor.fetchone()

    if row:
        note_id, title, content = row
        _open_note_tab(note_id, title, content)
    else:
        messagebox.showerror("Error", "Incorrect password or no hidden note found with this password.")

def delete_note():
    current_tab = notebook.select()
    if not current_tab:
        messagebox.showinfo("Delete Note", "No note selected.")
        return

    note_id = tab_note_id.get(current_tab)
    note_title = notebook.tab(current_tab, "text")

    confirm = messagebox.askyesno("Delete Note", f"Are you sure you want to delete '{note_title}'?")
    if not confirm:
        return

    # delete by id (not title)
    if note_id is not None:
        cursor.execute('DELETE FROM notepad WHERE id=?', (note_id,))
        conn.commit()

    # remove tab + mapping
    notebook.forget(current_tab)
    tab_note_id.pop(current_tab, None)


#Save/update current note

def save_current_note():
    current_tab = notebook.select()
    if not current_tab:
        messagebox.showinfo("Save", "No note selected.")
        return

    note_id = tab_note_id.get(current_tab)
    if note_id is None:
        messagebox.showerror("Save Error", "This tab is not linked to a database note.")
        return

    text_widget = _get_current_text_widget()
    if text_widget is None:
        messagebox.showerror("Save Error", "Text box not found in this tab.")
        return

    content = text_widget.get("1.0", "end-1c")
    title = notebook.tab(current_tab, "text")

    cursor.execute("UPDATE notepad SET title=?, content=? WHERE id=?", (title, content, note_id))
    conn.commit()
    messagebox.showinfo("Saved", "Note updated successfully.")


root = tk.Tk()
root.title("BuildingNote App")
root.geometry("800x500")
root.configure(bg="#f2f2f2")

style = ttk.Style()
style.configure("TNotebook.Tab", font=("TkDefaultFont", 14, "bold"),
                background="#f2f2f2", foreground="#343a40")

notebook = ttk.Notebook(root, style="TNotebook")
notebook.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Buttons
style.configure("info.TButton", font=("TkDefaultFont", 12, "bold"),
                foreground="green", activeforeground="white",
                highlightbackground="#f2f2f2")

style.configure("primary.TButton", font=("TkDefaultFont", 12, "bold"),
                foreground="green", activeforeground="white",
                highlightbackground="#f2f2f2")

new_button = ttk.Button(root, text="New Note", command=add_note, style="info.TButton")
new_button.pack(side=tk.LEFT, padx=10, pady=10)

show_hidden_button = ttk.Button(root, text="Show Hidden Notes", command=show_hidden_notes, style="info.TButton")
show_hidden_button.pack(side=tk.LEFT, padx=10, pady=10)

# Save button
save_button = ttk.Button(root, text="Save", command=save_current_note, style="info.TButton")
save_button.pack(side=tk.LEFT, padx=10, pady=10)

delete_button = ttk.Button(root, text="Delete", command=delete_note, style="primary.TButton")
delete_button.pack(side=tk.LEFT, padx=10, pady=10)

load_notes()
root.mainloop()
