import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import io
import os
from nltk.corpus import wordnet as wn
from tkinter import messagebox

class PDFReader:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Reader")
        # self.primary_directory = r"C:\Users\himit\Desktop\Novel and Stories"
        self.sidebar_visible = True
        self.doc = None
        self.page_number = 0
        self.zoom = 1.0  # Default zoom level
        self.settings_file = "pdf_reader_settings.txt"
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.load_settings()

        # Button frame
        btn_frame = tk.Frame(root, bg='#f0f0f0', padx=10, pady=5)
        btn_frame.pack(fill='x', side='top')

        tk.Button(btn_frame, text="Open PDF", command=self.open_pdf,
                  bg='#4CAF50', fg='white').pack(side='left', padx=5)
        self.sidebar_visible = True
        tk.Button(btn_frame, text="Toggle Sidebar", command=self.toggle_sidebar,
                bg='#9C27B0', fg='white').pack(side='left', padx=5)

        tk.Button(btn_frame, text="Previous", command=self.prev_page,
                  bg='#2196F3', fg='white').pack(side='left', padx=5)
        tk.Button(btn_frame, text="Next", command=self.next_page,
                  bg='#2196F3', fg='white').pack(side='left', padx=5)
        tk.Button(btn_frame, text="Zoom In", command=self.zoom_in,
                  bg='#FF9800', fg='white').pack(side='left', padx=5)
        tk.Button(btn_frame, text="Zoom Out", command=self.zoom_out,
                  bg='#FF9800', fg='white').pack(side='left', padx=5)

        self.page_label = tk.Label(btn_frame, text="Page: 0/0", bg='#f0f0f0')
        self.page_label.pack(side='right', padx=10)

        # Sidebar frame for file list
        self.sidebar_frame = tk.Frame(root, width=200, bg='#e0e0e0')
        self.sidebar_frame.pack(side='left', fill='y')

        # Sidebar Treeview for file browsing
        self.sidebar_frame = tk.Frame(root, width=250, bg='#f8f8f8')
        self.sidebar_frame.pack(side='left', fill='y')

        self.tree = ttk.Treeview(self.sidebar_frame)
        self.tree.pack(fill='both', expand=True)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_expand)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Add root directory (you can start with a specific one or the user directory)
        start_dir = os.path.expanduser("~")  # Starts in user's home directory
        self.insert_node('', start_dir)

        # Add Menu Bar
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open", command=self.open_pdf)
        
        # Recent files submenu
        recent_menu = tk.Menu(filemenu, tearoff=0)
        self.recent_menu = recent_menu
        filemenu.add_cascade(label="Recent Files", menu=recent_menu)
        self.update_recent_menu()
        
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=filemenu)
        root.config(menu=menubar)
        # Hide sidebar button
        # tk.Button(btn_frame, text="Toggle Sidebar", command=self.toggle_sidebar,
        #         bg='#FF5722', fg='white').pack(side='left', padx=5)

        # self.update_sidebar()

        # Jump to page input
        self.jump_entry = tk.Entry(btn_frame, width=5)
        self.jump_entry.pack(side='right')
        tk.Button(btn_frame, text="Go", command=self.jump_to_page,
                bg='#9C27B0', fg='white').pack(side='right', padx=5)


        # Canvas for PDF rendering
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill='both', expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg='gray')
        self.canvas.pack(side='left', fill='both', expand=True)

        # Bind scrolling
        self.canvas.bind("<MouseWheel>", self.on_mouse_scroll)
        self.canvas.bind("<Button-4>", self.on_mouse_scroll)  # Linux
        self.canvas.bind("<Button-5>", self.on_mouse_scroll)  # Linux
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.show_context_menu)  # Right-click
        self.canvas.bind("<ButtonRelease-1>", self.capture_selection)  # Left-click release
        self.selected_word = None

        self.tk_image = None
        self.settings_file = "pdf_reader_settings.json"


    def on_mouse_scroll(self, event):
        if event.num == 5 or event.delta < 0:
            self.next_page()
        elif event.num == 4 or event.delta > 0:
            self.prev_page()

    def open_pdf(self, file_path=None):
        if not file_path:
            file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:  # After successful open
            self.update_recent_menu()
        if file_path:
            # Check if we have saved state for this file
            file_state = self.settings["recent_files"].get(file_path, {})
            
            try:
                self.doc = fitz.open(file_path)
                self.page_number = file_state.get("page", 0)
                self.zoom = file_state.get("zoom", 1.0)
                self.update_page_label()
                self.display_page()
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")

    def display_page(self):
        if self.doc:
            page = self.doc.load_page(self.page_number)
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            image = Image.open(io.BytesIO(img_data))
            self.tk_image = ImageTk.PhotoImage(image)

            self.canvas.delete("all")
            self.canvas.config(scrollregion=(0, 0, image.width, image.height))

            # Get canvas dimensions and center the image
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            center_x = max((canvas_width - image.width) // 2, 0)
            center_y = max((canvas_height - image.height) // 2, 0)

            self.canvas.create_image(center_x, center_y, anchor='nw', image=self.tk_image)
            self.update_page_label()

    def next_page(self):
        if self.doc and self.page_number < len(self.doc) - 1:
            self.page_number += 1
            self.display_page()

    def prev_page(self):
        if self.doc and self.page_number > 0:
            self.page_number -= 1
            self.display_page()

    def zoom_in(self):
        self.zoom += 0.1
        self.display_page()

    def zoom_out(self):
        if self.zoom > 0.2:
            self.zoom -= 0.1
            self.display_page()

    def update_page_label(self):
        if self.doc:
            self.page_label.config(text=f"Page: {self.page_number + 1}/{len(self.doc)}")
        else:
            self.page_label.config(text="Page: 0/0")
    def jump_to_page(self):
        try:
            target = int(self.jump_entry.get()) - 1
            if 0 <= target < len(self.doc):
                self.page_number = target
                self.display_page()
        except ValueError:
            pass  # Ignore invalid input
    def on_close(self):
        if self.doc:
            with open(self.settings_file, "w") as f:
                f.write(f"{self.page_number},{self.zoom}")
        self.root.destroy()

    def load_settings(self):
        try:
            with open(self.settings_file, "r") as f:
                data = f.read().strip()
                if data:
                    page, zoom = map(float, data.split(","))
                    self.page_number = int(page)
                    self.zoom = zoom
        except Exception:
            pass  # Ignore missing or malformed file

    def insert_node(self, parent, path):
        node = self.tree.insert(parent, 'end', text=os.path.basename(path) or path,
                                values=[path], open=False)
        if os.path.isdir(path):
            self.tree.insert(node, 'end')  # Dummy child for expansion

    def on_tree_expand(self, event):
        node = self.tree.focus()
        path = self.tree.item(node, 'values')[0]
        # Clear dummy children
        self.tree.delete(*self.tree.get_children(node))
        # Insert actual children
        for child in os.listdir(path):
            full_path = os.path.join(path, child)
            if os.path.isdir(full_path) or child.lower().endswith(".pdf"):
                self.insert_node(node, full_path)

    def on_tree_select(self, event):
        node = self.tree.focus()
        path = self.tree.item(node, 'values')[0]
        if os.path.isfile(path) and path.lower().endswith(".pdf"):
            self.open_pdf(path)
    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.pack_forget()
        else:
            # Repack the sidebar BEFORE the canvas_frame to keep layout correct
            self.sidebar_frame.pack(side='left', fill='y')
            self.canvas_frame.pack_forget()
            self.canvas_frame.pack(side='right', fill='both', expand=True)
        self.sidebar_visible = not self.sidebar_visible

    def on_canvas_click(self, event):
        if not self.doc:
            return

        # Get the PDF page
        page = self.doc.load_page(self.page_number)
        
        # Get the displayed image dimensions
        img_width = self.tk_image.width()
        img_height = self.tk_image.height()
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Calculate image position (centered)
        img_x = max((canvas_width - img_width) // 2, 0)
        img_y = max((canvas_height - img_height) // 2, 0)
        
        # Convert click to image coordinates
        click_x = event.x - img_x
        click_y = event.y - img_y
        
        # Only process clicks that are actually on the image
        if 0 <= click_x < img_width and 0 <= click_y < img_height:
            # Convert to PDF coordinates (accounting for zoom)
            pdf_x = click_x / self.zoom
            pdf_y = click_y / self.zoom
            
            # Get all words on the page
            words = page.get_text("words")  # List of (x0, y0, x1, y1, "word", ...)
            
            # Find the word at the clicked position
            for word_info in words:
                x0, y0, x1, y1, word = word_info[:5]
                if x0 <= pdf_x <= x1 and y0 <= pdf_y <= y1:
                    self.lookup_word(word)
                    return
            
            # If no word found at exact position, show message
            messagebox.showinfo("Dictionary", "No word found at this position.")

    def lookup_word(self, word):
        if not word:
            messagebox.showinfo("Dictionary", "No word found at this position.")
            return

        meanings = wn.synsets(word)
        if not meanings:
            messagebox.showinfo("Dictionary", f"No definition found for '{word}'")
            return

        definition = meanings[0].definition()
        messagebox.showinfo(f"Definition of '{word}'", definition)
        
    def capture_selection(self, event):
        try:
            selection = self.root.clipboard_get()
            self.selected_word = selection.strip()
        except tk.TclError:
            self.selected_word = None
    def show_context_menu(self, event):
        if self.selected_word:
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label=f"Define '{self.selected_word}'", command=self.lookup_selected_word)
            menu.post(event.x_root, event.y_root)

    #Session Keeping
    def load_settings(self):
        try:
            with open(self.settings_file, "r") as f:
                import json
                self.settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = {"recent_files": {}, "last_file": None}

    def save_settings(self):
        with open(self.settings_file, "w") as f:
            import json
            json.dump(self.settings, f, indent=4)

    def on_close(self):
        # Save current state before closing
        if self.doc:
            file_path = self.doc.name
            self.settings["recent_files"][file_path] = {
                "page": self.page_number,
                "zoom": self.zoom
            }
            self.settings["last_file"] = file_path
        self.save_settings()
        self.root.destroy()
    def update_recent_menu(self):
        self.recent_menu.delete(0, 'end')
        for file_path in list(self.settings["recent_files"].keys())[:5]:  # Show last 5
            # Display just the filename, but store full path
            filename = os.path.basename(file_path)
            self.recent_menu.add_command(
                label=filename,
                command=lambda p=file_path: self.open_pdf(p)
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFReader(root)
    root.geometry("800x1000")
    root.mainloop()
