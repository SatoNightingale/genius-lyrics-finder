import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog
import os

import lyrics_manager
# from lyrics_manager import EstadoCancionLetras
# from lyrics_manager import canciones
# from lyrics_manager import obtener_mp3
# from lyrics_manager import buscar_lyrics

# ------------------------------------------------------------- #
#                     Declaración de globales                   #
# ------------------------------------------------------------- #
# deepseek API key: sk-bbb216ae32a64fc58c692a6ef0ae961c
root: tk.Tk = None
ruta: tk.StringVar
lstCanciones: ttk.Treeview
lblTitulo: tk.Label
lblAutor: tk.Label
lblEstado: tk.Label
txtLetra: tk.Text
txtConsola: tk.Text


strStates = {
    lyrics_manager.EstadoCancionLetras.SIN_LETRAS: 'No tiene letras',
    lyrics_manager.EstadoCancionLetras.BUSCANDO: 'Buscando letras en genius.com...',
    lyrics_manager.EstadoCancionLetras.ERROR_CONEXION: 'Error de conexión',
    lyrics_manager.EstadoCancionLetras.LETRAS_NO_ENCONTRADAS: 'No se encontraron letras',
    lyrics_manager.EstadoCancionLetras.YA_TENIA_LETRAS: 'Ya tenía letras',
    lyrics_manager.EstadoCancionLetras.LETRAS_ANADIDAS: 'Se añadieron letras'
}

# ------------------------------------------------------------- #
#                      Funciones de control                     #
# ------------------------------------------------------------- #

def registrar_canciones():
    global lstCanciones, ruta, root
    str_ruta = ruta.get()

    if os.path.exists(str_ruta):
        canciones = lyrics_manager.obtener_mp3(str_ruta)

        for cancion in canciones:
            estado = strStates[cancion['estado']]
            artista = cancion['artista']
            nombre = cancion['titulo']
            item = (estado, artista, nombre)
            lstCanciones.insert('', 'end', values=item)
    else:
        print('ruta invalida')
    
    root.update_idletasks()

    lyrics_manager.procesar_canciones_threading()

def actualizar_cancion_lista(cancion, index):
    global lstCanciones, root

    # song_name = ' - '.join([cancion['artista'], cancion['titulo']])

    # song_item = ' '.join([minorStrStates[cancion['estado']], song_name])

    iid = lstCanciones.get_children()[index]

    lstCanciones.delete(iid)

    estado = strStates[cancion['estado']]
    artista = cancion['artista']
    nombre = cancion['titulo']
    item = (estado, artista, nombre)

    lstCanciones.insert('', index, values=item)

    root.update_idletasks()

def actualizar_cancion_en_hilo(cancion, index):
    global root
    root.after(0, lambda i=index, c=cancion: actualizar_cancion_lista(c, i))

def mostrar_info_cancion(cancion):
    global lblTitulo, lblAutor, lblEstado, txtLetra

    lblTitulo['text'] = 'Titulo: ' + cancion['titulo']
    lblAutor['text'] = 'Autor: ' + cancion['artista']

    lblEstado['text'] = 'Estado: ' + strStates[cancion['estado']]

    txtLetra.config(state='normal')
    txtLetra.delete('1.0', tk.END)
    txtLetra.insert('1.0', cancion['letras'])
    txtLetra.config(state='disabled')




# ------------------------------------------------------------- #
#                      Funciones de evento                      #
# ------------------------------------------------------------- #

def buscar_carpeta():
    global ruta

    ruta.set(filedialog.askdirectory(
        title="Carpeta de música para buscar letras",
        initialdir="/"
    ))

    registrar_canciones()

def on_cancion_seleccionada(event):
    global lstCanciones
    # seleccion = lstCanciones.curselection()
    seleccion = lstCanciones.selection()
    if seleccion:
        item_id = seleccion[0]
        index = lstCanciones.get_children().index(item_id)
        cancion = lyrics_manager.canciones[index]
        mostrar_info_cancion(cancion)

def alternar_consola(event):
    if txtConsola.winfo_ismapped():
        txtConsola.grid_remove()
    else:
        txtConsola.grid()




# ------------------------------------------------------------- #
#                     Creación de la interfaz                   #
# ------------------------------------------------------------- #

def crear_frame_seleccion(root):
    global ruta

    frm = ttk.Frame(root, padding=10)
    frm.grid(sticky='ew')
    frm.columnconfigure(0, weight=1, minsize=320)
    frm.columnconfigure(1, weight=0)

    tk.Label(frm, text="Seleccione la carpeta donde está la música").grid(column=0, row=0, columnspan=2, sticky='w')

    boton = tk.Button(frm, text="Buscar", command=buscar_carpeta)
    boton.grid(column=1, row=1, sticky='ew')

    textfield = tk.Entry(frm, textvariable=ruta)
    textfield.grid(column=0, row=1, columnspan=1, sticky="ew", padx=10)

def crear_frame_listbox(root):
    global lstCanciones

    frame = ttk.Frame(root, padding=10)
    frame.grid(sticky='nsew')
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)

    tk.Label(frame, text="Canciones detectadas:").grid(column=0, row=0, sticky='w')

    lstCanciones = tk.Listbox(frame, selectmode=tk.SINGLE, width=30)
    lstCanciones = ttk.Treeview(frame, columns=("Estado", "Artista", "Nombre"), show='headings')
    lstCanciones.grid(column=0, row=1, sticky='nsew')

    lstCanciones.heading("Estado", text="Estado")
    lstCanciones.heading("Artista", text="Artista")
    lstCanciones.heading("Nombre", text="Nombre")

    lstCanciones.column("Estado", width=150, minwidth=100, stretch=False)
    lstCanciones.column("Artista", width=120, minwidth=80, stretch=False)
    lstCanciones.column("Nombre", minwidth=150, stretch=True)

    lstCanciones.bind('<<TreeviewSelect>>', on_cancion_seleccionada) # <<ListboxSelect>>

    scrollbalear_widget(frame, lstCanciones, 0, 1)

def crear_barra_lateral(root):
    global lblAutor, lblTitulo, lblEstado, txtLetra

    frame = ttk.Labelframe(root, padding=10, text="Información de la canción")
    frame.grid(column=1, row=0, sticky='nsew', rowspan=3)
    frame.columnconfigure(0, weight=1, minsize=200)
    frame.rowconfigure(4, weight=1)

    lblTitulo = tk.Label(frame, text="Titulo:")
    lblTitulo.grid(column=0, row=0, sticky='w')

    lblAutor = tk.Label(frame, text="Autor:")
    lblAutor.grid(column=0, row=1, sticky='w')

    lblEstado = tk.Label(frame, text="Estado:")
    lblEstado.grid(column=0, row=2, sticky='w')

    tk.Label(frame, text="Letra").grid(row=3, sticky='w')

    txtLetra = tk.Text(frame, wrap='word', width=32, height=8)
    txtLetra.grid(column=0, row=4, sticky='nsew')
    
    txtLetra.config(state='disabled')

    fuente = tkfont.Font(family="Arial", size=9)
    txtLetra.configure(font=fuente)

    scrollbalear_widget(frame, txtLetra, 0, 4)
    

def crear_consola_python(root):
    global txtConsola

    frame = ttk.Labelframe(root, padding=10, text="Consola", height=6)
    frame.grid(column=0, row=2, sticky='nsew', columnspan=1)
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    # frame.bind('<Button-1>', alternar_consola)

    txtConsola = tk.Text(frame, height=7)
    txtConsola.grid(column=0, row=0, sticky='nsew')
    txtConsola.config(state='disabled')

    fuente = tkfont.Font(family="Consolas", size=9)
    txtConsola.configure(font=fuente)

    scrollbalear_widget(frame, txtConsola, 0, 0)

    # redirigir
    sys.stdout = ConsoleRedirector(txtConsola)
    sys.stderr = ConsoleRedirector(txtConsola)

def crear_ventana():
    global root
    root = tk.Tk()
    root.title("Genius Lyrics Finder")
    
    global ruta
    ruta = tk.StringVar()

    root.rowconfigure(1, weight=1)
    root.columnconfigure(0, weight=1)

    crear_frame_seleccion(root)
    crear_frame_listbox(root)
    crear_barra_lateral(root)
    crear_consola_python(root)

    mensaje_bienvenida()
    
    root.mainloop()

def scrollbalear_widget(frame, widget: tk.Widget, column: int, row: int):
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=widget.yview)
    scrollbar.grid(column=column+1, row=row, sticky='ns')
    widget.config(yscrollcommand=scrollbar.set)

def mensaje_bienvenida():
    print("Bienvenido a Genius Lyrics Finder, creado por Satoshi!")
    print("Presione Buscar y seleccione una carpeta con archivos de música mp3. El programa recorrerá toda la carpeta y sus subcarpetas mostrando todas las canciones que haya, y para las que no tengan letras asignadas, descargará las letras del sitio genius.com y se las pondrá automáticamente, de ser posible\n")


# ---------------------------------------------------------- #
#       Para capturar y redirigir el output de la consola    #
# ---------------------------------------------------------- #

class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget # el widget por donde se va a pasar el output
        self.console = sys.__stdout__  # para mantener el output por consola
    
    def write(self, mensaje):
        self.text_widget.configure(state='normal')
        self.text_widget.insert('end', mensaje)
        self.text_widget.see('end') # para que auto-scrollee hasta el final
        self.text_widget.configure(state='disabled')
        if self.console != None:
            self.console.write(mensaje)  # también imprime en consola
    
    def flush(self):
        self.console.flush()