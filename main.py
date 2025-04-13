import tkinter as tk
from tkinter import font, filedialog, messagebox
import time
import os
import threading
import datetime
import webbrowser  
from tkinter import Menu 
from urllib.parse import quote 


class FreewriteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Freewrite")
        self.default_width = 1024
        self.default_height = 576
        self.root.geometry(f"{self.default_width}x{self.default_height}")
        self.root.minsize(800, 450)
        self.root.configure(bg='white')
        self.font_styles = ["Lato", "Arial", "Times New Roman", "Courier", "Georgia", "Verdana"]
        self.current_font_index = 0
        self.font_sizes = [16, 18, 20, 22, 24, 26]  
        self.current_font_size_index = 1  
        self.current_font_size = 18
        self.session_length_minutes = 15
        self.backspace_disabled = True
        self.dark_mode = False
        self.start_time = None
        self.word_count = 0
        self.goal_word_count = 500
        self.running = False
        self.paused = False
        self.timer_started = False
        self.themes = [
            {"name": "White", "bg": "white", "fg": "black", "cursor": "black"},  # Original White Theme
            {"name": "Dark", "bg": "#282c34", "fg": "#abb2bf", "cursor": "#61afef"},  # Original Dark Theme
            {"name": "Palette 1", "bg": "#4A2040", "fg": "#FFFFFF", "cursor": "#FFB85F"},
            {"name": "Palette 2", "bg": "#E8E8D3", "fg": "#5A5A42", "cursor": "#A89F91"},
            {"name": "Palette 3", "bg": "#7A1F3D", "fg": "#F5C6D0", "cursor": "#F28E8E"},
            {"name": "Palette 4", "bg": "#F9E4C8", "fg": "#5DA9E9", "cursor": "#F4A259"},
            {"name": "Palette 5", "bg": "#D9D9C3", "fg": "#3C5A3E", "cursor": "#6B8E23"},
            {"name": "Warm Red", "bg": "#8B0000", "fg": "#FFD700", "cursor": "#FF6347"},  # New Theme
            {"name": "Cool Blue", "bg": "#1E3A5F", "fg": "#A9D6E5", "cursor": "#4682B4"},  # New Theme
            {"name": "Muted Purple", "bg": "#5D3A9B", "fg": "#D4C4FB", "cursor": "#9370DB"},  # New Theme
            {"name": "Forest Green", "bg": "#013220", "fg": "#A7C957", "cursor": "#228B22"},  # New Theme
            {"name": "Earthy Brown", "bg": "#4E342E", "fg": "#D7CCC8", "cursor": "#8B4513"}   # New Theme
        ]
        self.current_theme_index = 0
        
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.create_menu()
        self.create_ui_elements()
        self.bind_shortcuts()
        self.autosave_interval = 60
        self.schedule_autosave()
        self.timer_label.config(text=f"{self.session_length_minutes}:00")
        self.text.focus_set()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Session", command=self.new_session)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Exit", command=self.exit_app)
        menubar.add_cascade(label="File", menu=file_menu)
        format_menu = tk.Menu(menubar, tearoff=0)
        font_menu = tk.Menu(format_menu, tearoff=0)
        for font_name in self.font_styles:
            font_menu.add_command(label=font_name, command=lambda f=font_name: self.change_font(f))
        format_menu.add_cascade(label="Font", menu=font_menu)
        size_menu = tk.Menu(format_menu, tearoff=0)
        for size in [14, 16, 18, 20, 24]:
            size_menu.add_command(label=str(size), command=lambda s=size: self.change_font_size(s))
        format_menu.add_cascade(label="Size", menu=size_menu)  
        format_menu.add_command(label="Toggle Dark Mode", command=self.toggle_theme)
        menubar.add_cascade(label="Format", menu=format_menu)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Set Word Goal", command=self.set_word_goal)
        settings_menu.add_command(label="Set Timer", command=self.set_timer)
        settings_menu.add_command(label="Toggle Backspace", command=self.toggle_backspace)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Freewriting Guide", command=self.show_guide)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)

    def create_ui_elements(self):
        self.main_container = tk.Frame(self.root, bg="white")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=0)  # Bottom bar doesn't resize
        self.main_container.grid_columnconfigure(0, weight=1)
        
        self.text_frame = tk.Frame(self.main_container, bg="white")
        self.text_frame.grid(row=0, column=0, sticky="nsew")

        self.text = tk.Text(
            self.text_frame,
            wrap='word',
            font=(self.font_styles[self.current_font_index], self.current_font_size),
            bg="white",
            fg="black",
            bd=0,
            padx=100,
            pady=50,
            insertbackground="black",
            highlightthickness=0
        )
        self.text.pack(expand=True, fill='both')
        self.text.bind('<KeyRelease>', self.update_word_count)
        self.text.bind('<Key>', self.start_timer_on_typing)
        if self.backspace_disabled:
            self.text.bind('<BackSpace>', self.handle_backspace)
        

        self.bottom_frame = tk.Frame(self.main_container, bg="white", height=40)
        self.bottom_frame.grid(row=1, column=0, sticky="ew")
        self.bottom_frame.grid_propagate(False)  # Prevent the frame from resizing based on content
        

        self.create_bottom_bar_contents()

    def create_bottom_bar_contents(self):
        # Left controls
        self.left_controls = tk.Frame(self.bottom_frame, bg="white", height=40)
        self.left_controls.pack(side=tk.LEFT, padx=20, fill='y')
        
        self.size_display = tk.Label(
            self.left_controls, 
            text="18px", 
            font=("Arial", 12),
            bg="white",
            fg="gray"
        )
        self.size_display.pack(side=tk.LEFT, padx=5)
        self.size_display.bind("<Button-1>", self.cycle_font_sizes)  # Bind click to cycle font sizes
        
        self.font_display = tk.Label(
            self.left_controls, 
            text="Lato", 
            font=("Arial", 12),
            bg="white",
            fg="gray"
        )
        self.font_display.pack(side=tk.LEFT, padx=5)
        self.font_display.bind("<Button-1>", self.cycle_fonts)
        
        # Right controls
        self.right_controls = tk.Frame(self.bottom_frame, bg="white", height=40)
        self.right_controls.pack(side=tk.RIGHT, padx=20, fill='y')
        
        self.timer_label = tk.Label(
            self.right_controls, 
            text="15:00", 
            font=("Arial", 12), 
            bg="white", 
            fg="gray" 
        )
        self.timer_label.pack(side=tk.LEFT, padx=5)
        self.timer_label.bind("<Button-1>", self.start_timer_on_click)
        
        self.chat_btn = tk.Label(
            self.right_controls,
            text="Chat",  
            font=("Arial", 12),
            bg="white",
            fg="gray"
        )
        self.chat_btn.pack(side=tk.LEFT, padx=5)
        self.chat_btn.bind("<Button-1>", lambda e: self.open_chat())
        
        self.new_entry_btn = tk.Label(
            self.right_controls, 
            text="New Entry", 
            font=("Arial", 12),
            bg="white",
            fg="gray"
        )
        self.new_entry_btn.pack(side=tk.LEFT, padx=5)
        self.new_entry_btn.bind("<Button-1>", lambda e: self.new_session())

        self.history_btn = tk.Label(
            self.right_controls, 
            text="History", 
            font=("Arial", 12),
            bg="white",
            fg="gray"
        )
        self.history_btn.pack(side=tk.LEFT, padx=5)
        self.history_btn.bind("<Button-1>", lambda e: self.toggle_history_menu())

        self.theme_btn = tk.Label(
            self.right_controls,  
            text="Theme", 
            font=("Arial", 12),
            bg="white",
            fg="gray"
        )
        self.theme_btn.pack(side=tk.LEFT, padx=5)
        self.theme_btn.bind("<Button-1>", lambda e: self.toggle_theme())

    def open_chat(self):
        text_content = self.text.get("1.0", 'end-1c').strip()
        if text_content:
            query = quote(text_content)
            webbrowser.open(f"https://chat.openai.com/?q={query}")  
        else:
            messagebox.showinfo("ChatGPT", "The text area is empty. Please write something first.")

    def bind_shortcuts(self):
        self.root.bind('<Escape>', self.toggle_fullscreen)
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-n>', lambda e: self.new_session())
        self.root.bind('<Control-q>', lambda e: self.exit_app())
        self.root.bind('<Control-p>', lambda e: self.toggle_pause())
    
    def start_timer_on_typing(self, event=None):
        if not self.timer_started and event.char:
            self.timer_started = True
            self.running = True
            self.start_time = time.time()
            self.update_timer()
        
    def start_timer_on_click(self, event=None):
        if not self.timer_started:
            self.timer_started = True
            self.running = True
            self.start_time = time.time()
            self.update_timer()
        
    def update_word_count(self, event=None):
        text_content = self.text.get("1.0", 'end-1c')
        words = text_content.split()
        self.word_count = len(words)

    def update_timer(self):
        if not self.running:
            return
        if not self.paused and self.start_time:
            elapsed_time = int(time.time() - self.start_time)
            remaining_time = max(0, self.session_length_minutes * 60 - elapsed_time)
            if remaining_time <= 0 and self.running:
                self.times_up()
                return
            minutes = remaining_time // 60
            seconds = remaining_time % 60
            timer_text = f"{minutes:02d}:{seconds:02d}"
            self.timer_label.config(text=timer_text)
        self.root.after(1000, self.update_timer)

    def handle_backspace(self, event):
        if self.backspace_disabled:
            return 'break'
        return None

    def change_font(self, font_name):
        self.text.config(font=(font_name, self.current_font_size))
        self.font_display.config(text=font_name)

    def change_font_size(self, size):
        self.current_font_size = size
        current_font = font.Font(font=self.text["font"])
        family = current_font.actual()["family"]
        self.text.config(font=(family, size))
        self.size_display.config(text=f"{size}px")

    def toggle_theme(self):
        self.current_theme_index = (self.current_theme_index + 1) % len(self.themes)
        self.apply_theme(self.themes[self.current_theme_index])

    def apply_theme(self, theme):
        bg_color = theme["bg"]
        fg_color = theme["fg"]
        cursor_color = theme["cursor"]


        self.root.configure(bg=bg_color)
        self.main_container.configure(bg=bg_color)
        self.text_frame.configure(bg=bg_color)
        self.text.configure(bg=bg_color, fg=fg_color, insertbackground=cursor_color)
        self.bottom_frame.configure(bg=bg_color)
        self.left_controls.configure(bg=bg_color)
        self.right_controls.configure(bg=bg_color)
        

        for widget in [self.size_display, self.font_display, self.timer_label, 
                      self.chat_btn, self.new_entry_btn, self.history_btn, self.theme_btn]:
            widget.configure(bg=bg_color, fg=fg_color)
        

        self.timer_label.configure(font=("Arial", 12), fg=fg_color)

    def show_theme_menu(self):
        theme_menu = tk.Toplevel(self.root)
        theme_menu.title("Select Theme")
        theme_menu.geometry("300x300")
        theme_menu.configure(bg="white")

        for index, theme in enumerate(self.themes):
            theme_button = tk.Button(
                theme_menu,
                text=theme["name"],
                font=("Arial", 12),
                bg=theme["bg"],
                fg=theme["fg"],
                command=lambda i=index: self.select_theme(i)
            )
            theme_button.pack(fill=tk.X, padx=10, pady=5)

    def select_theme(self, index):
        self.current_theme_index = index
        self.apply_theme(self.themes[index])

    def toggle_fullscreen(self, event=None):
        is_fullscreen = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not is_fullscreen)
        return "break"
        
    def toggle_pause(self, event=None):
        if not self.timer_started:
            return
        self.paused = not self.paused
        if self.paused:
            self.pause_time = time.time()
        else:
            pause_duration = time.time() - self.pause_time
            self.start_time += pause_duration

    def toggle_backspace(self):
        self.backspace_disabled = not self.backspace_disabled
        if self.backspace_disabled:
            self.text.bind('<BackSpace>', self.handle_backspace)
            messagebox.showinfo("Settings", "Backspace has been disabled.")
        else:
            self.text.unbind('<BackSpace>')
            messagebox.showinfo("Settings", "Backspace has been enabled.")

    def set_word_goal(self):
        try:
            new_goal = tk.simpledialog.askinteger(
                "Word Goal", 
                "Set your word count goal:",
                minvalue=1, 
                maxvalue=10000,
                initialvalue=self.goal_word_count
            )
            if new_goal:
                self.goal_word_count = new_goal
                self.update_word_count()
        except:
            pass

    def set_timer(self):
        try:
            new_time = tk.simpledialog.askinteger(
                "Timer Setting", 
                "Set session length (minutes):",
                minvalue=1, 
                maxvalue=120,
                initialvalue=self.session_length_minutes
            )
            if new_time:
                self.session_length_minutes = new_time
                self.timer_label.config(text=f"{new_time}:00")
                if self.timer_started:
                    self.start_time = time.time()
        except:
            pass

    def autosave(self):
        try:
            text_content = self.text.get("1.0", 'end-1c')
            if not text_content.strip():
                return
            if not os.path.exists("drafts"):
                os.makedirs("drafts")
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f'drafts/freewrite_{timestamp}.txt'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text_content)
        except Exception as e:
            print(f"Autosave failed: {e}")

    def schedule_autosave(self):
        if self.running:
            self.autosave()
        self.root.after(self.autosave_interval * 1000, self.schedule_autosave)

    def save_file(self):
        try:
            text_content = self.text.get("1.0", 'end-1c')
            if not text_content.strip():
                messagebox.showwarning("Save", "Nothing to save. The document is empty.")
                return
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialdir="./drafts" if os.path.exists("./drafts") else "./",
                title="Save Your Writing"
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                messagebox.showinfo("Save", f"File saved successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {e}")

    def new_session(self):
        if self.word_count > 0:
            response = messagebox.askyesnocancel(
                "New Session", 
                "Do you want to save your current work before starting a new session?"
            )
            if response is None:
                return
            elif response:
                self.save_file()
        self.text.delete("1.0", tk.END)
        self.timer_started = False
        self.running = False
        self.paused = False
        self.word_count = 0
        self.timer_label.config(text=f"{self.session_length_minutes}:00")

    def times_up(self):
        self.running = False
        self.timer_label.config(text="00:00")
        self.autosave()
        result = messagebox.askyesno(
            "Time's Up!", 
            f"Your {self.session_length_minutes}-minute freewriting session is complete!\n\n"
            f"You wrote {self.word_count} words.\n\n"
            "Do you want to continue writing?"
        )
        if result:
            self.start_time = time.time()
            self.running = True
            self.update_timer()
        else:
            self.save_file()

    def show_about(self):
        about_text = """
        Freewrite App
        Version 1.0
        
        A minimalist writing application designed to help you
        focus on getting words on the page without distraction.
        
        Tips:
        - Write continuously without editing
        - Turn off your inner critic
        - Just keep typing, even if you write "I don't know what to write"
        - Quantity over quality - editing comes later
        """
        messagebox.showinfo("About Freewrite", about_text)

    def show_guide(self):
        guide_text = """
        FREEWRITING GUIDE
        
        What is freewriting?
        -------------------
        Freewriting is a writing strategy developed in 1973 — it's where you write 
        continuously for a set time without worrying about grammar, spelling, or anything 
        like that. A pure stream of consciousness.
        
        Rules of Freewriting:
        --------------------
        1. Set a time limit (like 15 minutes)
        2. Write continuously - don't stop typing
        3. Don't edit as you go (backspace is disabled by default)
        4. Don't worry about quality - just get words on the page
        5. If you get stuck, write about being stuck
        
        Benefits:
        --------
        • Overcomes writer's block
        • Generates new ideas
        • Improves writing fluency
        • Reduces anxiety about writing
        • Creates a daily writing habit
        
        When you're done:
        ---------------
        Save your work and then decide if you want to keep any parts for future
        use. Not everything you freewrite will be usable, and that's perfectly fine!
        """
        guide_window = tk.Toplevel(self.root)
        guide_window.title("Freewriting Guide")
        guide_window.geometry("600x500")
        guide_area = tk.Text(
            guide_window, 
            wrap=tk.WORD, 
            font=("Arial", 12),
            padx=20, 
            pady=20
        )
        guide_area.pack(expand=True, fill=tk.BOTH)
        guide_area.insert(tk.END, guide_text)
        guide_area.config(state=tk.DISABLED)
        close_button = tk.Button(
            guide_window, 
            text="Close", 
            command=guide_window.destroy,
            padx=10,
            pady=5
        )
        close_button.pack(pady=10)

    def exit_app(self):
        """Ensure proper cleanup before exiting the application."""
        if self.word_count > 0:
            response = messagebox.askyesnocancel(
                "Exit", 
                "You have unsaved work. Do you want to save your work before exiting?"
            )
            if response is None:  
                return
            elif response: 
                self.save_file()
        
        self.root.unbind_all("<MouseWheel>")
        self.root.destroy()

    def change_aspect_ratio(self, width, height):
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(width, height)
        self.root.maxsize(width, height)

    def cycle_fonts(self, event=None):
        self.current_font_index = (self.current_font_index + 1) % len(self.font_styles)
        new_font = self.font_styles[self.current_font_index]
        self.text.config(font=(new_font, self.current_font_size))
        self.font_display.config(text=new_font)

    def cycle_font_sizes(self, event=None):
        self.current_font_size_index = (self.current_font_size_index + 1) % len(self.font_sizes)
        new_size = self.font_sizes[self.current_font_size_index]
        self.current_font_size = new_size
        self.text.config(font=(self.font_styles[self.current_font_index], new_size))
        self.size_display.config(text=f"{new_size}px")

    def show_history(self):
        history_window = tk.Toplevel(self.root)
        history_window.title("Freewrite History")
        history_window.geometry("300x400")
        history_window.configure(bg="white")

        history_label = tk.Label(
            history_window, 
            text="Select a file to view:", 
            font=("Arial", 14), 
            bg="white", 
            fg="black"
        )
        history_label.pack(pady=10)

        drafts_dir = "drafts"
        if not os.path.exists(drafts_dir):
            os.makedirs(drafts_dir)

        files = sorted(
            [f for f in os.listdir(drafts_dir) if f.endswith(".txt")], 
            reverse=True
        )

        for file in files:
            file_button = tk.Button(
                history_window,
                text=file,
                font=("Arial", 12),
                bg="white",
                fg="black",
                anchor="w",
                command=lambda f=file: self.open_history_file(f)
            )
            file_button.pack(fill=tk.X, padx=10, pady=5)

        close_button = tk.Button(
            history_window, 
            text="Close", 
            font=("Arial", 12), 
            bg="white", 
            fg="black", 
            command=history_window.destroy
        )
        close_button.pack(pady=10)

    def toggle_history_menu(self):
        if hasattr(self, 'history_menu') and self.history_menu.winfo_exists():
            self.close_history_menu()
        else:
            self.open_history_menu()

    def open_history_menu(self):

        current_theme = self.themes[self.current_theme_index]
        bg_color = current_theme["bg"]
        fg_color = current_theme["fg"]
        accent_color = current_theme["cursor"]
        
        self.history_menu = tk.Frame(self.root, bg=bg_color, width=350, borderwidth=0, 
                                     highlightthickness=1, highlightbackground=accent_color)
        self.history_menu.place(x=self.root.winfo_width(), y=0, height=self.root.winfo_height())
        

        header_frame = tk.Frame(self.history_menu, bg=bg_color, pady=15, padx=20)
        header_frame.pack(fill=tk.X)
        
        history_label = tk.Label(
            header_frame, 
            text="Writing History", 
            font=("Arial", 18, "bold"), 
            bg=bg_color, 
            fg=fg_color
        )
        history_label.pack(side=tk.LEFT, pady=5)
        
        close_btn = tk.Label(
            header_frame, 
            text="×", 
            font=("Arial", 22), 
            bg=bg_color, 
            fg=accent_color,
            cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.close_history_menu())
        

        search_frame = tk.Frame(self.history_menu, bg=bg_color, padx=20, pady=10)
        search_frame.pack(fill=tk.X)
        
        search_border = tk.Frame(search_frame, bg=accent_color, padx=1, pady=1, borderwidth=0)
        search_border.pack(fill=tk.X)
        
        search_inner = tk.Frame(search_border, bg=bg_color, borderwidth=0)
        search_inner.pack(fill=tk.X)
        
        self.search_entry = tk.Entry(
            search_inner,
            font=("Arial", 12),
            bg=bg_color,
            fg=fg_color,
            insertbackground=accent_color,
            relief=tk.FLAT,
            highlightthickness=0,
            borderwidth=0
        )
        self.search_entry.pack(fill=tk.X, padx=10, pady=8)
        self.search_entry.insert(0, "Search entries...")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, tk.END) 
                              if self.search_entry.get() == "Search entries..." else None)
        self.search_entry.bind("<FocusOut>", lambda e: self.search_entry.insert(0, "Search entries...") 
                              if not self.search_entry.get() else None)
        self.search_entry.bind("<KeyRelease>", self.filter_history_entries)
        

        divider = tk.Frame(self.history_menu, height=1, bg=accent_color)
        divider.pack(fill=tk.X, padx=20, pady=10)

        self.files_scroll_frame = tk.Frame(self.history_menu, bg=bg_color)
        self.files_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        self.files_canvas = tk.Canvas(self.files_scroll_frame, bg=bg_color, 
                                      highlightthickness=0, borderwidth=0)
        self.files_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(self.files_scroll_frame, orient="vertical", 
                                 command=self.files_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.files_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.files_frame = tk.Frame(self.files_canvas, bg=bg_color)
        canvas_window = self.files_canvas.create_window((0, 0), window=self.files_frame, 
                                                        anchor="nw", tags="self.files_frame")
        
        def configure_canvas(event):
            self.files_canvas.configure(scrollregion=self.files_canvas.bbox("all"))
            self.files_canvas.itemconfig(canvas_window, width=event.width)
        
        self.files_frame.bind("<Configure>", configure_canvas)
        
        def _on_mousewheel(event):
            self.files_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.files_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        

        def _cleanup_bindings():
            if hasattr(self, 'files_canvas'):
                self.files_canvas.unbind_all("<MouseWheel>")
                self.files_frame.unbind("<Configure>")
        
        self.history_menu.bind("<Destroy>", lambda e: _cleanup_bindings())
        

        self.load_history_files()
        

        button_frame = tk.Frame(self.history_menu, bg=bg_color, padx=20, pady=15)
        button_frame.pack(fill=tk.X)
        
        new_session_btn = tk.Button(
            button_frame,
            text="New Session",
            font=("Arial", 12),
            bg=accent_color,
            fg=bg_color,
            activebackground=fg_color,
            activeforeground=bg_color,
            relief=tk.FLAT,
            borderwidth=0,
            padx=15,
            pady=8,
            cursor="hand2",
            command=self.start_new_session_from_history
        )
        new_session_btn.pack(side=tk.RIGHT)
        

        self.animate_history_menu_in()
        
        def _cleanup_bindings():
            if hasattr(self, 'files_canvas'):
                self.files_canvas.unbind_all("<MouseWheel>")
        
        self.history_menu.bind("<Destroy>", lambda e: _cleanup_bindings())

    def start_new_session_from_history(self):
        """Close the history menu and start a new session safely."""
        if hasattr(self, 'history_menu') and self.history_menu.winfo_exists():
            self.close_history_menu()
        self.new_session()

    def load_history_files(self):
        for widget in self.files_frame.winfo_children():
            widget.destroy()
        
        drafts_dir = "drafts"
        if not os.path.exists(drafts_dir):
            os.makedirs(drafts_dir)
        
      
        files = sorted(
            [f for f in os.listdir(drafts_dir) if f.endswith(".txt")], 
            reverse=True
        )
        
        search_query = ""
        if hasattr(self, 'search_entry'):
            search_query = self.search_entry.get().lower()
            if search_query == "search entries...":
                search_query = ""
        

        if search_query:
            filtered_files = []
            for file in files:
                with open(os.path.join(drafts_dir, file), 'r', encoding='utf-8') as f:
                    try:
                        content = f.read()
                        if search_query in content.lower() or search_query in file.lower():
                            filtered_files.append(file)
                    except:
                        pass  
            files = filtered_files
        
        if not files:
            no_files_label = tk.Label(
                self.files_frame,
                text="No entries found",
                font=("Arial", 12, "italic"),
                bg=self.themes[self.current_theme_index]["bg"],
                fg=self.themes[self.current_theme_index]["fg"]
            )
            no_files_label.pack(pady=20)
            return
        

        for file in files:
            current_theme = self.themes[self.current_theme_index]
            bg_color = current_theme["bg"]
            fg_color = current_theme["fg"]
            accent_color = current_theme["cursor"]
            
           
            try:
                date_str = file.replace("freewrite_", "").replace(".txt", "")
                date_obj = datetime.datetime.strptime(date_str, "%Y%m%d-%H%M%S")
                formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
            except:
                formatted_date = file
            

            preview_text = ""
            try:
                with open(os.path.join(drafts_dir, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    words = content.split()
                    word_count = len(words)
                    preview_text = content[:100] + ("..." if len(content) > 100 else "")
            except:
                preview_text = "Error reading file"
                word_count = 0

            entry_frame = tk.Frame(
                self.files_frame,
                bg=bg_color,
                padx=20,
                pady=12,
                borderwidth=0
            )
            entry_frame.pack(fill=tk.X)
            entry_frame.bind("<Enter>", lambda e, f=entry_frame: f.configure(bg=self.lighten_color(bg_color)))
            entry_frame.bind("<Leave>", lambda e, f=entry_frame: f.configure(bg=bg_color))
            entry_frame.bind("<Button-1>", lambda e, f=file: self.open_history_file(f))
            

            date_label = tk.Label(
                entry_frame,
                text=formatted_date,
                font=("Arial", 12, "bold"),
                bg=entry_frame["bg"],
                fg=fg_color,
                anchor="w"
            )
            date_label.pack(fill=tk.X, anchor="w")
            date_label.bind("<Button-1>", lambda e, f=file: self.open_history_file(f))
            
            word_label = tk.Label(
                entry_frame,
                text=f"{word_count} words",
                font=("Arial", 10),
                bg=entry_frame["bg"],
                fg=accent_color,
                anchor="w"
            )
            word_label.pack(fill=tk.X, anchor="w", pady=(2, 5))
            word_label.bind("<Button-1>", lambda e, f=file: self.open_history_file(f))
            

            preview_label = tk.Label(
                entry_frame,
                text=preview_text,
                font=("Arial", 11),
                bg=entry_frame["bg"],
                fg=fg_color,
                anchor="w",
                justify=tk.LEFT,
                wraplength=280
            )
            preview_label.pack(fill=tk.X, anchor="w")
            preview_label.bind("<Button-1>", lambda e, f=file: self.open_history_file(f))
            

            if file != files[-1]:
                divider = tk.Frame(self.files_frame, height=1, bg=accent_color)
                divider.pack(fill=tk.X, padx=20, pady=0)

    def filter_history_entries(self, event=None):
        self.load_history_files()

    def lighten_color(self, hex_color, factor=0.1):
        """Lighten a hex color by a factor (0.0-1.0)"""
        try:

            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            
            # Lighten
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            

            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return hex_color  

    def animate_history_menu_in(self):
        def slide_in():
            x = self.history_menu.winfo_x()
            target_x = self.root.winfo_width() - 350
            if x > target_x:
                distance = x - target_x
                step = max(10, int(distance * 0.25))
                x -= step
                self.history_menu.place(x=x, y=0)
                self.root.after(10, slide_in)
            else:
                self.history_menu.place(x=target_x, y=0)
        slide_in()

    def close_history_menu(self):
        def slide_out():
            x = self.history_menu.winfo_x()
            if x < self.root.winfo_width():

                distance = self.root.winfo_width() - x
                step = max(10, int(distance * 0.20)) 
                x += step
                self.history_menu.place(x=x, y=0)
                self.root.after(10, slide_out)
            else:
                self.history_menu.destroy()
                del self.history_menu  
        slide_out()

    def open_history_file(self, file_name):
        """Open a history file in a new window with improved styling"""
        drafts_dir = "drafts"
        file_path = os.path.join(drafts_dir, file_name)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            messagebox.showerror("Error", f"Could not open file: {file_name}")
            return
        

        current_theme = self.themes[self.current_theme_index]
        bg_color = current_theme["bg"]
        fg_color = current_theme["fg"]
        accent_color = current_theme["cursor"]

        content_window = tk.Toplevel(self.root)
        content_window.title(f"Freewrite - {file_name}")
        content_window.geometry("700x500")
        content_window.minsize(600, 400)
        content_window.configure(bg=bg_color)
        
        # Get word count
        word_count = len(content.split())
        

        try:
            date_str = file_name.replace("freewrite_", "").replace(".txt", "")
            date_obj = datetime.datetime.strptime(date_str, "%Y%m%d-%H%M%S")
            formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
        except:
            formatted_date = file_name
        

        header_frame = tk.Frame(content_window, bg=bg_color, pady=10, padx=30)
        header_frame.pack(fill=tk.X)
        
        date_label = tk.Label(
            header_frame,
            text=formatted_date,
            font=("Arial", 16, "bold"),
            bg=bg_color,
            fg=fg_color
        )
        date_label.pack(side=tk.LEFT)
        
        stats_label = tk.Label(
            header_frame,
            text=f"{word_count} words",
            font=("Arial", 14),
            bg=bg_color,
            fg=accent_color
        )
        stats_label.pack(side=tk.RIGHT)
        

        divider = tk.Frame(content_window, height=1, bg=accent_color)
        divider.pack(fill=tk.X, padx=30, pady=5)
        

        content_frame = tk.Frame(content_window, bg=bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=5)
        
        scrollbar = tk.Scrollbar(content_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        content_area = tk.Text(
            content_frame,
            wrap=tk.WORD,
            font=(self.font_styles[self.current_font_index], self.current_font_size),
            bg=bg_color,
            fg=fg_color,
            borderwidth=0,
            highlightthickness=0,
            padx=5,
            pady=5,
            yscrollcommand=scrollbar.set
        )
        content_area.pack(expand=True, fill=tk.BOTH)
        scrollbar.config(command=content_area.yview)
        
        content_area.insert(tk.END, content)
        content_area.config(state=tk.DISABLED)
        

        button_frame = tk.Frame(content_window, bg=bg_color, pady=15, padx=30)
        button_frame.pack(fill=tk.X)
        
        edit_button = tk.Button(
            button_frame,
            text="Edit Text",
            font=("Arial", 12),
            bg=accent_color,
            fg=bg_color,
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=lambda: self.load_text_for_editing(content, content_window)
        )
        edit_button.pack(side=tk.LEFT, padx=5)
        
        export_button = tk.Button(
            button_frame,
            text="Export",
            font=("Arial", 12),
            bg=bg_color,
            fg=accent_color,
            relief=tk.FLAT,
            borderwidth=1,
            highlightbackground=accent_color,
            padx=15,
            pady=8,
            command=lambda: self.export_file(file_path)
        )
        export_button.pack(side=tk.LEFT, padx=5)
        
        close_button = tk.Button(
            button_frame,
            text="Close",
            font=("Arial", 12),
            bg=bg_color,
            fg=fg_color,
            relief=tk.FLAT,
            padx=15,
            pady=8,
            command=content_window.destroy
        )
        close_button.pack(side=tk.RIGHT, padx=5)

    def load_text_for_editing(self, content, parent_window=None):
        """Loads text from history into the main editor and closes history windows"""
        if parent_window:
            parent_window.destroy()
        
        if hasattr(self, 'history_menu') and self.history_menu.winfo_exists():
            self.close_history_menu()
        
        current_text = self.text.get("1.0", 'end-1c').strip()
        if current_text and current_text != content.strip():
            response = messagebox.askyesno(
                "Replace Text",
                "Loading this text will replace your current work. Continue?"
            )
            if not response:
                return
        

        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, content)
        self.update_word_count()

    def export_file(self, source_path):
        """Export a file to a user-selected location"""
        target_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("All files", "*.*")
            ],
            title="Export File"
        )
        
        if target_path:
            try:
                with open(source_path, 'r', encoding='utf-8') as src:
                    content = src.read()
                
                with open(target_path, 'w', encoding='utf-8') as dst:
                    dst.write(content)
                
                messagebox.showinfo("Export Successful", f"File exported to {target_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Error exporting file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    def on_closing():
        app.exit_app()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = FreewriteApp(root)
    app.text.insert(tk.END, """Hi. Welcome to Freewrite :)
Plz read this guide.

I beg of you.

It's 5 min max.

My name is Farza.

I made this app.

This is not a journaling app or a note-taking app.
If you use it for that, you'll probably use it once or twice,
and then never touch it again.

This is a tool purely to help you freewrite.

Freewriting is a writing strategy developed in 1973 — it's where you write
continuously for a set time without worrying about grammar, spelling, or anything 
like that. A pure stream of consciousness.
                    
This is a Python Rewrite of the original Freewrite app, which was made in Native Swift.
Now this Application is cross-platform and works on Windows, Mac, and Linux.
This is a fork of Farza's original Freewrite app!
                    
- Paramveer :) 

""")
    root.mainloop()