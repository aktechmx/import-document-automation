import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os, sys
from create_document import generar_word
from pdf_extractor import extraer_informacion_pdfs

def ruta_ico(ruta_relativa):
    '''Obtendremos la ruta absoluta del ícono'''
    if hasattr(sys,'_MEIPASS'):
        ruta_base = sys._MEIPASS
    else:
        ruta_base = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(ruta_base, ruta_relativa)

class AplicacionPlantillas:
    def __init__(self, root):
        self.root = root
        # Título
        self.root.title("Generador de Plantilla para Importaciones")
        self.root.geometry("550x550")
        self.root.configure(padx=20, pady=20)
        self.root.resizable(False, False)

        try:
            # BUSCAMOS PNG ORIGINAL
            ruta_icono = ruta_ico("logo.png")
            # Usamos PhotoImage e iconphoto
            imagen_icono = tk.PhotoImage(file=ruta_icono)
            self.root.iconphoto(False, imagen_icono)
        except Exception as e:
            messagebox.showwarning("Debug de Ícono", f"No se pudo cargar el ícono.\n\nError: {e}\n\nRuta intentada: {ruta_icono}")

        # Variables de las rutas
        self.ruta_pdf1 = ""
        self.ruta_pdf2 = ""
        self.ruta_guardado = ""

        self.crear_interfaz()

    def crear_interfaz(self):
        # --- ESTILOS ---
        estilo = ttk.Style()
        estilo.configure("TButton", font=("Calibri", 10), padding=5)
        estilo.configure("TLabel", font=("Calibri", 10))
        estilo.configure("Titulo.TLabel", font=("Calibri", 14, "bold"))

        # --- ENCABEZADO ---
        ttk.Label(self.root, text="Automatización de Importaciones Temporales", style="Titulo.TLabel").pack(pady=(0, 15))

        # --- SELECCIÓN DE ARCHIVOS ---
        frame_archivos = ttk.LabelFrame(self.root, text=" 1. Selección de Documentos ", padding=10)
        frame_archivos.pack(fill="x", pady=5)

        self.btn_pdf1 = ttk.Button(frame_archivos, text="📄 Seleccionar Factura (PDF 1)", command=self.seleccionar_pdf1)
        self.btn_pdf1.pack(fill="x", pady=2)
        self.lbl_pdf1 = ttk.Label(frame_archivos, text="No seleccionado", foreground="gray")
        self.lbl_pdf1.pack(anchor="w", pady=(0, 5))

        self.btn_pdf2 = ttk.Button(frame_archivos, text="📄 Seleccionar Certificado (PDF 2)", command=self.seleccionar_pdf2)
        self.btn_pdf2.pack(fill="x", pady=2)
        self.lbl_pdf2 = ttk.Label(frame_archivos, text="No seleccionado", foreground="gray")
        self.lbl_pdf2.pack(anchor="w", pady=(0, 5))

        # --- SELECCIÓN DE DESTINO ---
        frame_destino = ttk.LabelFrame(self.root, text=" 2. Carpeta de Destino ", padding=10)
        frame_destino.pack(fill="x", pady=10)

        self.btn_destino = ttk.Button(frame_destino, text="📁 Seleccionar Carpeta para Guardar", command=self.seleccionar_destino)
        self.btn_destino.pack(fill="x", pady=2)
        self.lbl_destino = ttk.Label(frame_destino, text="No seleccionado", foreground="gray")
        self.lbl_destino.pack(anchor="w", pady=(0, 5))

        # --- BARRA DE PROGRESO Y ESTATUS ---
        self.frame_progreso = tk.Frame(self.root)
        self.frame_progreso.pack(fill="x", pady=10)

        self.lbl_estatus = ttk.Label(self.frame_progreso, text="Esperando documentos...", font=("Calibri", 10, "italic"))
        self.lbl_estatus.pack(pady=2)

        self.progress_bar = ttk.Progressbar(self.frame_progreso, mode='indeterminate')
        

        # --- BOTÓN DE PROCESAR ---
        self.btn_procesar = ttk.Button(self.root, text="🚀 PROCESAR PLANTILLA", command=self.iniciar_proceso)
        self.btn_procesar.pack(fill="x", pady=15, ipady=8)

    # --- FUNCIONES DE LOS BOTONES ---
    def seleccionar_pdf1(self):
        ruta = filedialog.askopenfilename(title="Selecciona la Factura", filetypes=[("Archivos PDF", "*.pdf")])
        if ruta:
            self.ruta_pdf1 = ruta
            self.lbl_pdf1.config(text=ruta.split("/")[-1], foreground="black")

    def seleccionar_pdf2(self):
        ruta = filedialog.askopenfilename(title="Selecciona el Certificado", filetypes=[("Archivos PDF", "*.pdf")])
        if ruta:
            self.ruta_pdf2 = ruta
            self.lbl_pdf2.config(text=ruta.split("/")[-1], foreground="black")

    def seleccionar_destino(self):
        ruta = filedialog.askdirectory(title="Selecciona la carpeta destino")
        if ruta:
            self.ruta_guardado = ruta
            self.lbl_destino.config(text=ruta, foreground="black")

    # --- LÓGICA DEL PROCESAMIENTO ---
    def iniciar_proceso(self):
        # Validación
        if not self.ruta_pdf1 or not self.ruta_pdf2 or not self.ruta_guardado:
            messagebox.showwarning("Han faltado datos", "Por favor, selecciona los dos PDFs y la carpeta de destino.")
            return

        # Bloqueo de botones en procesamiento de datos.
        self.btn_pdf1.state(['disabled'])
        self.btn_pdf2.state(['disabled'])
        self.btn_destino.state(['disabled'])
        self.btn_procesar.state(['disabled'])

        
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.start(15)
        self.lbl_estatus.config(text="Leyendo documentos PDF. Esto puede tomar unos segundos...", foreground="blue")
        
        self.root.update() 
        self.ejecutar_extraccion()

    def ejecutar_extraccion(self):
        try:
            lista_de_datos = extraer_informacion_pdfs(self.ruta_pdf1, self.ruta_pdf2)

            self.lbl_estatus.config(text="Generando Plantilla en Word...")
            self.root.update()

            # Creamos una lista para guardar los nombres de los archivos generados
            nombres_archivos = []
            
            for datos_heat in lista_de_datos:
                # Atrapamos el nombre que nos devuelve create_document.py
                nombre = generar_word(datos_heat, self.ruta_guardado)
                nombres_archivos.append(nombre)

            # Unimos los nombres por si en un futuro genera más de uno al mismo tiempo
            archivos_texto = ", ".join(nombres_archivos)

            self.progress_bar.stop()
            self.progress_bar.pack_forget() 
            
            # 1. Lo mostramos en la pantalla principal del programa
            self.lbl_estatus.config(text=f"¡Éxito! Archivo: {archivos_texto}", foreground="green")
            
            # Unimos los nombres por si en un futuro genera más de uno al mismo tiempo
            archivos_texto = ", ".join(nombres_archivos)

            self.progress_bar.stop()
            self.progress_bar.pack_forget() 
            
            # --- NUEVO MENSAJE PERSONALIZADO ---
            # Cortamos la ruta completa para obtener solo el nombre de la última carpeta
            nombre_folder = self.ruta_guardado.split("/")[-1]
            
            mensaje_exito = f"El archivo se guardó con el nombre {archivos_texto}, en el folder {nombre_folder}."
            
            # 1. Lo mostramos en la pantalla principal del programa
            self.lbl_estatus.config(text=mensaje_exito, foreground="green")
            
            # 2. Lo mostramos en la ventanita emergente
            messagebox.showinfo("Completado", f"{mensaje_exito}\n\nPuedes realizar el proceso de nuevo.")
            
            # Le avisamos al reseteo que fue un éxito para que no borre el mensaje de la pantalla
            self.resetear_interfaz(exito=True)

        except Exception as e:
            self.progress_bar.stop()
            self.progress_bar.pack_forget() 
            self.lbl_estatus.config(text="Error durante el procesamiento", foreground="red")
            
            messagebox.showerror("Error", f"Ocurrió un error inesperado:\n{str(e)}")
            self.resetear_interfaz(solo_botones=True)

    # Agregamos el parámetro 'exito=False' a la función
    def resetear_interfaz(self, solo_botones=False, exito=False):
        self.btn_pdf1.state(['!disabled'])
        self.btn_pdf2.state(['!disabled'])
        self.btn_destino.state(['!disabled'])
        self.btn_procesar.state(['!disabled'])

        if not solo_botones:
            self.ruta_pdf1 = ""
            self.ruta_pdf2 = ""
            self.lbl_pdf1.config(text="No seleccionado", foreground="gray")
            self.lbl_pdf2.config(text="No seleccionado", foreground="gray")
            
            # Si NO venimos de un éxito, regresamos el mensaje a "Esperando documentos"
            if not exito:
                self.lbl_estatus.config(text="Esperando nuevos documentos...", foreground="black")

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionPlantillas(root)
    root.mainloop()