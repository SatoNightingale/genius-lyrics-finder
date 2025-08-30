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

root: tk.Tk = None
ruta: tk.StringVar
modo_edicion = False
lstCanciones: ttk.Treeview
lblTitulo: tk.Label
lblArtista: tk.Label
lblEstado: tk.Label
tfdTitulo: tk.Entry
tfdArtista: tk.Entry
panelInfo: tk.Frame
panelEdicion: tk.Frame
btnEditar: tk.Button
btnRecargar: tk.Button
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
        lstCanciones.delete(*lstCanciones.get_children())
        lyrics_manager.clear_canciones()

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

    iid = lstCanciones.get_children()[index]

    lstCanciones.delete(iid)
    # print(cancion)
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
    global lblTitulo, lblArtista, lblEstado, txtLetra

    lblTitulo['text'] = 'Titulo: ' + cancion['titulo']
    lblArtista['text'] = 'Autor: ' + cancion['artista']

    lblEstado['text'] = 'Estado: ' + strStates[cancion['estado']]
    
    txtLetra.config(state='normal')
    txtLetra.delete('1.0', tk.END)
    txtLetra.insert('1.0', cancion['letras'])
    txtLetra.config(state='disabled')


def get_listbox_index() -> int | None:
    global lstCanciones
    seleccion = lstCanciones.selection()
    if seleccion:
        item_id = seleccion[0]
        index = lstCanciones.get_children().index(item_id)
        return index
    else:
        return None


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
    index = get_listbox_index()
    if index:
        cancion = lyrics_manager.get_cancion(index)
        if cancion:
            mostrar_info_cancion(cancion)


def alternar_consola(event):
    if txtConsola.winfo_ismapped():
        txtConsola.grid_remove()
    else:
        txtConsola.grid()


def cambiar_modo_edicion():
    global modo_edicion, btnEditar, lblTitulo, lblArtista, tfdTitulo, tfdArtista, panelInfo, panelEdicion
    
    indice = get_listbox_index()

    cancion = lyrics_manager.get_cancion(indice) if indice else None

    if cancion:
        modo_edicion = not modo_edicion
        
        btnEditar.config(text="Guardar" if modo_edicion else "Editar")

        if modo_edicion:
            panelEdicion.grid()
            panelInfo.grid_remove()

            tfdTitulo.delete(0, 'end')
            tfdTitulo.insert(0, cancion['titulo'])
            tfdArtista.delete(0, 'end')
            tfdArtista.insert(0, cancion['artista'])
        else:
            panelEdicion.grid_remove()
            panelInfo.grid()
            lyrics_manager.actualizar_info_cancion(indice, tfdTitulo.get(), tfdArtista.get())

            actualizar_cancion_lista(cancion, indice)
            lblTitulo.config(text="Titulo: " + cancion['titulo'])
            lblArtista.config(text="Artista: " + cancion['artista'])





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

    textfield = tk.Entry(frm, textvariable=ruta)
    textfield.grid(column=0, row=1, columnspan=1, sticky="ew")

    boton = tk.Button(frm, text="Buscar", command=buscar_carpeta)
    boton.grid(column=1, row=1, padx=10, sticky='ew')

    return frm


def crear_frame_listbox(root):
    global lstCanciones

    frame = ttk.Frame(root, padding=10)
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

    scrollbalear_widget(frame, lstCanciones, 1, 0)

    return frame

def crear_barra_lateral(root):
    global lblEstado, panelInfo, panelEdicion

    frame = ttk.Labelframe(root, padding=10, text="Información de la canción")
    
    frame.columnconfigure(0, minsize=200) # weight=1,
    frame.rowconfigure(3, weight=1)

    panelInfo = crear_panel_info(frame)
    panelEdicion = crear_panel_edicion(frame)
    botones = crear_panel_botones(frame)

    panelInfo.grid(column=0, row=0, sticky='w')

    panelEdicion.grid(column=0, row=0, sticky='w')
    panelEdicion.grid_remove() # se mostrará cuando se presione el botón Editar

    lblEstado = tk.Label(frame, text="Estado:")
    lblEstado.grid(column=0, row=1, sticky='w')

    botones.grid(column=0, row=2, sticky='ew')

    # incluso se podría poner la ruta

    letra = crear_panel_letra(frame)
    letra.grid(column=0, row=3, sticky='nsew')

    return frame


def crear_panel_info(parent):
    global lblArtista, lblTitulo

    frame = ttk.Frame(parent)
    frame.grid()

    lblTitulo = tk.Label(frame, text="Titulo:")
    lblTitulo.grid(column=0, row=0, sticky='w')

    lblArtista = tk.Label(frame, text="Artista:")
    lblArtista.grid(column=0, row=1, sticky='w')

    return frame


def crear_panel_edicion(parent):
    global tfdArtista, tfdTitulo

    frame = ttk.Frame(parent)

    tk.Label(frame, text="Titulo:").grid(column=0, row=0)

    tfdTitulo = tk.Entry(frame)
    tfdTitulo.grid(column=1, row=0, padx=5, sticky='ew')

    tk.Label(frame, text="Autor:").grid(column=0, row=1)

    tfdArtista = tk.Entry(frame)
    tfdArtista.grid(column=1, row=1, padx=5, sticky='ew')

    return frame


def crear_panel_botones(parent):
    global btnEditar, btnRecargar

    frame = ttk.Frame(parent)

    btnEditar = tk.Button(frame, text="Editar", command=cambiar_modo_edicion)
    btnEditar.grid(column=0, row=0, padx=5, sticky='ew')

    btnRecargar = tk.Button(frame, text="Recargar letra")
    btnRecargar.grid(column=1, row=0, padx=5, sticky='ew')

    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)

    return frame


def crear_panel_letra(parent):
    global txtLetra

    frame = ttk.Frame(parent)

    tk.Label(frame, text="Letra").grid(row=0, sticky='w')

    txtLetra = tk.Text(frame, wrap='word', width=32, height=8)
    txtLetra.grid(column=0, row=1, sticky='nsew')
    
    txtLetra.config(state='disabled')

    fuente = tkfont.Font(family="Arial", size=9)
    txtLetra.configure(font=fuente)

    scrollbalear_widget(frame, txtLetra, 1, 0)

    frame.rowconfigure(1, weight=1)

    return frame


def crear_consola_python(root):
    global txtConsola

    frame = ttk.Labelframe(root, padding=10, text="Consola", height=6)
    
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

    return frame


def crear_ventana():
    global root
    root = tk.Tk()
    root.title("Genius Lyrics Finder")
    
    global ruta
    ruta = tk.StringVar()

    root.rowconfigure(1, weight=1)
    root.columnconfigure(0, weight=1)

    seleccion = crear_frame_seleccion(root)
    seleccion.grid(column=0, row=0)

    listbox = crear_frame_listbox(root)
    listbox.grid(row=1, column=0)
    listbox.grid(sticky='nsew')

    barra = crear_barra_lateral(root)
    barra.grid(column=1, row=0, sticky='nsew', rowspan=3, padx=5, pady=5)

    consola = crear_consola_python(root)
    consola.grid(column=0, row=2, sticky='nsew', padx=5, pady=5)

    mensaje_bienvenida()
    
    root.mainloop()

def scrollbalear_widget(frame, widget: tk.Widget, row: int, column: int):
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