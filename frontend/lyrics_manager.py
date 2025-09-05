import os.path
import threading
from enum import Enum
from dotenv import load_dotenv
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, ProxyError
import lyricsgenius

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

# API_URL = "http://127.0.0.1:8000/getkey"
API_URL = "http://genius-lyrics-finder.vercel.app/getkey"
# API_URL = "https://genius-lyrics-finder-satonightingale8475-yooxz7gs.leapcell.dev/api/procesar"
# API_URL = "https://genius-lyrics-finder.onrender.com/api/procesar"



password = "rgusdjzo;v;laoeq3t8w9 e0g7054w8h tn78w09tp82u0 n3"

canciones = []


class EstadoCancionLetras(Enum):
    SIN_LETRAS              = 0
    BUSCANDO                = 1
    ERROR_CONEXION          = 2
    LETRAS_NO_ENCONTRADAS   = 3
    YA_TENIA_LETRAS         = 4
    LETRAS_ANADIDAS         = 5


load_dotenv(".env")

def get_token():
    try:
        response = requests.post(API_URL, json={"key": password}, timeout=10.0)
        data = response.json()
        key = data['password']
        
        if key != "":
            from encriptacion import descifrar
            token = descifrar(key, password)
        else:
            token = None
    except Exception as e:
        token = 'general_exception'
        print(e)
    except ProxyError as e:
        token = 'proxy_error'
    
    return token


def crear_genius(token: str):
    try:
        genius = lyricsgenius.Genius(
            token,
            remove_section_headers=True,
            skip_non_songs=False
        )
    except Exception as e:
        genius = None
    
    return genius


def recorrer_dir_recursivamente(dir: str, callback: callable):
    archivos = os.listdir(dir)

    for i, archivo in enumerate(archivos):
        ruta = os.path.join(dir, archivo)

        if os.path.isdir(ruta):
            recorrer_dir_recursivamente(ruta, callback)
        else:
            callback(ruta, i)


def procesar_mp3(ruta: str, id: int):
    if ruta.endswith("mp3"):
        global canciones
        audiofile = eyed3.load(ruta)

        if audiofile.tag is None:
            audiofile.initTag()

        titulo = audiofile.tag.title
        artista = audiofile.tag.artist

        letras = audiofile.tag.lyrics
        if letras and letras[0].text != '':
            letras = letras[0].text
            estado = EstadoCancionLetras.YA_TENIA_LETRAS
        else:
            letras = ''
            estado = EstadoCancionLetras.SIN_LETRAS

        canciones.append({"id": id, "titulo": titulo, "artista": artista, "letras": letras, "ruta": ruta, "estado": estado})

def obtener_mp3(dir):
    global canciones
    recorrer_dir_recursivamente(dir, procesar_mp3)
    return canciones


def run_threading(func, *args, **kwargs):
    hilo = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    hilo.start()


def procesar_canciones(canciones: list):
    token = get_token()
    genius = crear_genius(token)
    
    from interfaz import mensaje_fallo
    ok = False

    if token == 'general_exception':
        mensaje_fallo("Error: No se pudo logear en genius. Probablemente sea un problema de conexión")
    elif token == 'proxy_error':
        mensaje_fallo("Error al establecer conexión con el proxy. Intente desactivar el proxy")
    elif genius:
        ok = True
        for cancion in canciones:
            if cancion['estado'] == EstadoCancionLetras.BUSCANDO:
                lyrics, error = buscar_genius(cancion, genius)
                actualizar_cancion(cancion, lyrics, error)
        
    if not ok:
        for cancion in canciones:
            if cancion['estado'] == EstadoCancionLetras.BUSCANDO:
                actualizar_cancion(cancion, '', EstadoCancionLetras.ERROR_CONEXION)


def actualizar_cancion(cancion: dict, letra: str, error: EstadoCancionLetras):
    from interfaz import actualizar_cancion_en_hilo
    
    if error == None:
        cancion["letras"] = letra
        escribir_letras_archivo(cancion)
        cancion['estado'] = EstadoCancionLetras.LETRAS_ANADIDAS
    else:
        cancion['estado'] = error

        match error:
            case EstadoCancionLetras.YA_TENIA_LETRAS:
                print("La cancion", cancion["artista"], "-", cancion["titulo"], "ya tenia letras", "\n")
            case EstadoCancionLetras.ERROR_CONEXION:
                print("Error de conexión. No se pudo buscar las letras de la canción", cancion['artista'], "-", cancion['titulo'], "\n")
            case EstadoCancionLetras.LETRAS_NO_ENCONTRADAS:
                print("No se obtuvo resultados para", cancion["artista"], "-", cancion["titulo"], "\n")
            case _:
                print("Ha ocurrido un error inesperado y no se pudo buscar las letras de la canción", cancion["artista"], "-", cancion["titulo"], "\n")
    
    # actualizar GUI
    actualizar_cancion_en_hilo(cancion)


def buscar_genius(cancion: dict, genius: lyricsgenius.Genius) -> tuple[str, EstadoCancionLetras]:
    lyrics = ''
    error = EstadoCancionLetras.ERROR_CONEXION

    try:
        song_genius = genius.search_song(title=cancion['titulo'], artist=cancion['artista'])
        lyrics = song_genius.lyrics
        
        if lyrics != None and lyrics != "":
            error = None
        else:
            error = EstadoCancionLetras.LETRAS_NO_ENCONTRADAS
    except (HTTPError, ConnectionError, Timeout):
        error = EstadoCancionLetras.ERROR_CONEXION
    
    return lyrics, error


def escribir_letras_archivo(cancion):
    file = eyed3.load(cancion["ruta"])
    if file.tag is None:
        file.initTag()
    file.tag.lyrics.set(cancion["letras"])
    file.tag.save()
    print("Letras añadidas al archivo:", cancion["ruta"])


def get_cancion(index: int):
    if index >= 0 and index < len(canciones):
        return canciones[index]
    else:
        return None


def iniciar_busqueda(canciones):
    from interfaz import actualizar_cancion_en_hilo

    for cancion in canciones:
        if cancion['estado'] == EstadoCancionLetras.SIN_LETRAS:
            cancion['estado'] = EstadoCancionLetras.BUSCANDO
            actualizar_cancion_en_hilo(cancion)
    
    procesar_canciones(canciones)


def recargar_canciones(ids: list[int]):
    canciones = []
    for id in ids:
        cancion = get_cancion(id)
        if cancion:
            cancion['estado'] = EstadoCancionLetras.SIN_LETRAS
            canciones.append(cancion)
    
    iniciar_busqueda(canciones)


def modificar_datos_cancion(index, titulo: str, artista: str):
    cancion = get_cancion(index)
    if cancion:
        cancion['titulo'] = titulo
        cancion['artista'] = artista
        
        file = eyed3.load(cancion['ruta'])
        file.tag.artist = artista
        file.tag.title = titulo
        file.tag.save()
        print("Se ha modificado la información del archivo:", cancion['ruta'])


def clear_canciones():
    canciones.clear()


def run_as_script():
    cancion = "D:\\Música\\Eluveitie\\01 Eluveitie - Prologue.mp3"
    carpeta = "D:\\Música\\Eluveitie\\example\\2025 - Ànv"

    global canciones
    canciones = obtener_mp3(carpeta)
    procesar_canciones(canciones)


def test():
    print(get_token())

# if __name__ == '__main__':
#     test()

