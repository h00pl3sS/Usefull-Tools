import os
import sys
import re
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import pdf2image
import pdfplumber
from pypdf import PdfReader, PdfWriter
import threading

def get_resource_path(relative_path):
    """ Gestiona las rutas para que funcionen en el .exe compilado """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class AppInteractivaV2:
    def __init__(self, root):
        self.root = root
        self.root.title("Divisor PDF Pro V2.1 - Food Delivery Brands")
        self.root.geometry("1100x950")
        
        self.pdf_path = ""
        self.output_folder = tk.StringVar()
        self.selection_coords = None 
        self.pdf_dim = (0, 0)
        self.scale_factor = 1.0
        
        self.setup_ui()

    def setup_ui(self):
        # --- PANEL SUPERIOR DE CONTROLES ---
        top_bar = tk.Frame(self.root, pady=10, bg="#f0f0f0")
        top_bar.pack(side=tk.TOP, fill=tk.X)
        
        # Fila 1: Selección de PDF
        f1 = tk.Frame(top_bar, bg="#f0f0f0")
        f1.pack(fill=tk.X, padx=10)
        tk.Button(f1, text="📂 1. Cargar PDF", command=self.load_pdf, width=15).pack(side=tk.LEFT, padx=5)
        self.lbl_pdf = tk.Label(f1, text="Ningún archivo seleccionado", bg="#f0f0f0", fg="blue", font=("Arial", 9, "bold"))
        self.lbl_pdf.pack(side=tk.LEFT, padx=5)

        # Fila 2: Carpeta de Destino (MODIFICADO)
        f2 = tk.Frame(top_bar, bg="#f0f0f0")
        f2.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(f2, text="📁 2. Elegir Destino", command=self.browse_output, width=15).pack(side=tk.LEFT, padx=5)
        # El campo Entry ahora permite ver y editar la ruta completa
        self.ent_dest = tk.Entry(f2, textvariable=self.output_folder, font=("Arial", 9))
        self.ent_dest.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Fila 3: Acciones y Progreso
        f3 = tk.Frame(top_bar, bg="#f0f0f0")
        f3.pack(fill=tk.X, padx=10, pady=5)
        self.btn_run = tk.Button(f3, text="🚀 3. Procesar Selección", state=tk.DISABLED, 
                                 command=self.start_thread, bg="#4CAF50", fg="white", width=25, font=("Arial", 10, "bold"))
        self.btn_run.pack(side=tk.LEFT, padx=5)
        self.progress = ttk.Progressbar(f3, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.pack(side=tk.LEFT, padx=20)

        # --- VISUALIZADOR ---
        self.frame_canvas = tk.Frame(self.root, bd=2, relief=tk.SUNKEN)
        self.frame_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(self.frame_canvas, cursor="cross", bg="gray", highlightthickness=0)
        self.v_scroll = tk.Scrollbar(self.frame_canvas, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scroll = tk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.draw_crop)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop)
        
        # --- CONSOLA DE LOG ---
        self.log_area = scrolledtext.ScrolledText(self.root, height=8, font=("Consolas", 9), bg="#1e1e1e", fg="#dcdcdc")
        self.log_area.pack(fill=tk.X, padx=10, pady=5)
        
        self.rect = None
        tk.Label(self.root, text="Desarrollado por Miguel de Marcos para Food Delivery Brands", 
                          fg="red", font=("Arial", 8, "italic")).pack(side=tk.BOTTOM, pady=2)

    def log(self, msg):
        self.log_area.insert(tk.END, f"> {msg}\n")
        self.log_area.see(tk.END)

    def browse_output(self):
        # Abre el diálogo estándar que permite crear carpetas nuevas
        folder = filedialog.askdirectory(title="Selecciona o Crea la carpeta de destino")
        if folder:
            # Normalizamos la ruta para evitar problemas de barras inclinadas
            folder = os.path.normpath(folder)
            self.output_folder.set(folder)
            self.log(f"Destino establecido: {folder}")

    def load_pdf(self):
        self.pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not self.pdf_path: return
        
        # Por defecto sugerimos la carpeta del PDF, pero el usuario puede cambiarla
        self.output_folder.set(os.path.normpath(os.path.dirname(self.pdf_path)))
        self.lbl_pdf.config(text=os.path.basename(self.pdf_path))
        
        poppler_path = get_resource_path("poppler_bin")
        if os.path.exists(os.path.join(poppler_path, "bin")):
            poppler_path = os.path.join(poppler_path, "bin")
        
        try:
            self.log("Generando vista previa...")
            images = pdf2image.convert_from_path(self.pdf_path, first_page=1, last_page=1, poppler_path=poppler_path)
            full_img = images[0]
            
            screen_h = self.root.winfo_screenheight() * 0.65
            self.scale_factor = screen_h / full_img.height
            new_w, new_h = int(full_img.width * self.scale_factor), int(full_img.height * self.scale_factor)
            self.preview_img = full_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            with pdfplumber.open(self.pdf_path) as pdf:
                self.pdf_dim = (pdf.pages[0].width, pdf.pages[0].height)

            self.tk_img = ImageTk.PhotoImage(self.preview_img)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
            self.canvas.config(scrollregion=(0, 0, new_w, new_h))
            self.log("PDF cargado. 1) Elige destino (puedes crear una carpeta nueva). 2) Selecciona el área.")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al cargar: {e}")

    def start_crop(self, event):
        self.start_x, self.start_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if self.rect: self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='red', width=3)

    def draw_crop(self, event):
        cur_x, cur_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def end_crop(self, event):
        ex, ey = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.selection_coords = (min(self.start_x, ex), min(self.start_y, ey), max(self.start_x, ex), max(self.start_y, ey))
        self.btn_run.config(state=tk.NORMAL)

    def start_thread(self):
        if not self.output_folder.get():
            messagebox.showwarning("Atención", "Por favor, elige una carpeta de destino primero.")
            return
        self.btn_run.config(state=tk.DISABLED)
        threading.Thread(target=self.process, daemon=True).start()

    def process(self):
        try:
            out_dir = self.output_folder.get()
            # Si el usuario escribió una ruta que no existe, la creamos
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            
            sx, sy = self.pdf_dim[0] / self.preview_img.width, self.pdf_dim[1] / self.preview_img.height
            bbox = (self.selection_coords[0]*sx, self.selection_coords[1]*sy, 
                    self.selection_coords[2]*sx, self.selection_coords[3]*sy)

            reader = PdfReader(self.pdf_path)
            total = len(reader.pages)
            self.progress["maximum"] = total

            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    crop = page.within_bbox(bbox)
                    raw_name = crop.extract_text()
                    
                    raw_val = raw_name.split('\n')[0] if raw_name else f"Pagina_{i+1}"
                    clean_name = re.sub(r'[<>:"/\\|?*]', '', raw_val).strip()[:60]
                    if not clean_name: clean_name = f"Pagina_{i+1}"
                    
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])
                    
                    dest = os.path.join(out_dir, f"{clean_name}.pdf")
                    c = 1
                    while os.path.exists(dest):
                        dest = os.path.join(out_dir, f"{clean_name}_{c}.pdf"); c += 1
                    
                    with open(dest, "wb") as f: writer.write(f)
                    
                    self.progress["value"] = i + 1
                    self.log(f"[{i+1}/{total}] Guardado: {os.path.basename(dest)}")
            
            self.log(f"--- PROCESO FINALIZADO CON ÉXITO ---")
            messagebox.showinfo("Completado", f"Se han generado {total} archivos en la carpeta seleccionada.")
        except Exception as e:
            self.log(f"ERROR: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.btn_run.config(state=tk.NORMAL)
            self.progress["value"] = 0

if __name__ == "__main__":
    root = tk.Tk()
    AppInteractivaV2(root)
    root.mainloop()