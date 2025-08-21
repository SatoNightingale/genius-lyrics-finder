import lyricsgenius # librería para acceder a la API de genius.com - sitio web de letras
import os.path
import threading
from enum import Enum
from requests.exceptions import HTTPError, ConnectionError

# Librerías para procesar etiquetas
# from mutagen.mp3 import MP3 # ---muy raro ._.
import eyed3

# Cosas de mutagen.mp3
# cancion = MP3(os.path.join(carpeta, "Eluveitie - Celtos.mp3"))
# print(cancion.tags.get("TIT2"))

import logging 
# Para silenciar el logging de genius
logging.getLogger("lyricsgenius").setLevel(logging.CRITICAL)

# import interfaz
# from interfaz import actualizar_cancion_lista

# ---------------------------------------------------------
#            Pequeño mínimo técnico de eyed3D             #
# ---------------------------------------------------------

# Esto es para que no dé warning al escribir en un archivo
eyed3.log.setLevel("ERROR")

# Inicialización (por si el archivo no tiene etiquetas)
# if audiofile.tag is None:
#     audiofile.initTag()

# Cargar el archivo
# audiofile = eyed3.load(cancion)

# Leer datos
# print(audiofile.tag.artist, "-", audiofile.tag.title)
# print(audiofile.tag.lyrics[0].text) # leer lyrics

# Setear lyrics
# audiofile.tag.lyrics.set("La pele montaña, heyo heyo~~")
# audiofile.tag.save() # salvar

genius: lyricsgenius.Genius

cancion = "D:\\Música\\Eluveitie\\01 Eluveitie - Prologue.mp3"
carpeta = "D:\\Música\\Eluveitie\\albums"

canciones = []

class EstadoCancionLetras(Enum):
    SIN_LETRAS              = 0
    BUSCANDO                = 1
    ERROR_CONEXION          = 2
    LETRAS_NO_ENCONTRADAS   = 3
    NO_TIENE_LETRAS         = 4
    YA_TENIA_LETRAS         = 5
    LETRAS_ANADIDAS         = 6




def init_genius():
    global genius

    client_access_token = 'SPqGfxsIk4OkUD2mKptJfGWxz-2bhjlcAIT0zAWfVACV5df3Hu5uz4ndVBfA7tws'
    genius = lyricsgenius.Genius(client_access_token, remove_section_headers=True, skip_non_songs=True)

def recorrer_dir_recursivamente(dir: str, callback: callable):
    archivos = os.listdir(dir)

    for f in archivos:
        ruta = os.path.join(dir, f)

        if os.path.isdir(ruta):
            recorrer_dir_recursivamente(ruta, callback)
        else:
            callback(ruta)

def procesar_mp3(ruta: str):
    if ruta.endswith("mp3"):
        global canciones
        audiofile = eyed3.load(ruta)

        if audiofile.tag is None:
            audiofile.initTag()

        titulo = audiofile.tag.title
        artista = audiofile.tag.artist

        letras = audiofile.tag.lyrics
        if letras:
            letras = letras[0].text
            estado = EstadoCancionLetras.YA_TENIA_LETRAS
        else:
            letras = ''
            estado = EstadoCancionLetras.BUSCANDO

        canciones.append({"titulo": titulo, "artista": artista, "letras": letras, "ruta": ruta, 'estado': estado})

def obtener_mp3(dir):
    global canciones
    recorrer_dir_recursivamente(dir, procesar_mp3)
    return canciones

# esto va a ser cómico
# me dice que lo haga en un HILO BRÓDER
def procesar_canciones_threading():
    hilo = threading.Thread(target=procesar_canciones)
    hilo.start()

def procesar_canciones():
    global canciones, genius
    from interfaz import actualizar_cancion_en_hilo

    for i, cancion in enumerate(canciones):
        buscar_lyrics_cancion(cancion)
        actualizar_cancion_en_hilo(cancion, i)


# Toma todos los archivos mp3 de una carpeta y si no tienen letra, las busca en genius.com y se las asigna
def buscar_lyrics_cancion(cancion):
    global genius

    # file = eyed3.load(cancion["ruta"])
    
    # lyrics = file.tag.lyrics

    if cancion['letras'] == '':
        try:
            song_genius = genius.search_song(cancion["titulo"], cancion["artista"])
            
            if song_genius != None:
                file = eyed3.load(cancion["ruta"])
                lyrics = song_genius.lyrics

                print("Salvando letras para", cancion["ruta"], "\n")

                file.tag.lyrics.set(lyrics)
                file.tag.save()

                cancion['letras'] = lyrics
                cancion['estado'] = EstadoCancionLetras.LETRAS_ANADIDAS
            else:
                print("No se obtuvo resultados para", cancion["artista"], "-", cancion["titulo"], "\n")
                cancion['estado'] = EstadoCancionLetras.LETRAS_NO_ENCONTRADAS
        except (HTTPError, ConnectionError) as error:
            print("Error de conexión:", error.strerror)
            cancion['estado'] = EstadoCancionLetras.ERROR_CONEXION
    else:
        print("La cancion", cancion["artista"], "-", cancion["titulo"], "ya tenia letras", "\n")
        
        


def run_as_script():
    init_genius()
    recorrer_dir_recursivamente(carpeta, procesar_mp3)
    # buscar_lyrics()

# def main():
#     init_genius()
#     interfaz.crear_ventana()

# if __name__ == '__main__':
#     # run_as_script()
#     main()

