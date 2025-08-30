import asyncio
import json
import os.path
import threading
from enum import Enum
import requests
from requests.exceptions import HTTPError, ConnectionError
import httpx

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

API_URL = "http://127.0.0.1:8000/api/procesar"
# API_URL = "http://genius-lyrics-finder.vercel.app/api/procesar"
# API_URL = "https://genius-lyrics-finder-satonightingale8475-yooxz7gs.leapcell.dev/api/procesar"
# API_URL = "https://genius-lyrics-finder.onrender.com/api/procesar"


cancion = "D:\\Música\\Eluveitie\\01 Eluveitie - Prologue.mp3"
carpeta = "D:\\Música\\Eluveitie\\example\\2025 - Ànv"

canciones = []

class EstadoCancionLetras(Enum):
    SIN_LETRAS              = 0
    BUSCANDO                = 1
    ERROR_CONEXION          = 2
    LETRAS_NO_ENCONTRADAS   = 3
    YA_TENIA_LETRAS         = 4
    LETRAS_ANADIDAS         = 5






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
            print("letras", letras)
            estado = EstadoCancionLetras.YA_TENIA_LETRAS
        else:
            letras = ''
            estado = EstadoCancionLetras.SIN_LETRAS

        canciones.append({"id": id, "titulo": titulo, "artista": artista, "letras": letras, "ruta": ruta, "estado": estado})

def obtener_mp3(dir):
    global canciones
    recorrer_dir_recursivamente(dir, procesar_mp3)
    return canciones


def obtener_backend_list(canciones: list) -> list:
    from interfaz import actualizar_cancion_en_hilo

    backend_list = []
    
    for cancion in canciones:
        if cancion["estado"] == EstadoCancionLetras.SIN_LETRAS:
            backend_list.append({"id": cancion["id"], "titulo": cancion["titulo"], "artista": cancion["artista"]})
        elif cancion['estado'] == EstadoCancionLetras.YA_TENIA_LETRAS:
            print("La cancion", cancion["artista"], "-", cancion["titulo"], "ya tenia letras", "\n")
            actualizar_cancion_en_hilo(cancion, cancion['id'])
    
    return backend_list


# esto va a estar gracioso
# me dice que lo haga en un HILO BRÓDER
def procesar_canciones_threading():
    hilo = threading.Thread(target=procesar_canciones)
    hilo.start()

def procesar_canciones():
    global canciones
    asyncio.run(buscar_letras_backend(canciones))


async def buscar_letras_backend(canciones: list):
    from interfaz import actualizar_cancion_en_hilo

    formatted_canciones = obtener_backend_list(canciones)
    payload = {"items": formatted_canciones}

    for cancion in canciones:
        if cancion['estado'] == EstadoCancionLetras.SIN_LETRAS:
            cancion['estado'] = EstadoCancionLetras.BUSCANDO
            actualizar_cancion_en_hilo(cancion, cancion['id'])

    try:
        async with httpx.AsyncClient() as cliente:
            async with cliente.stream("POST", API_URL, json=payload) as respuesta:
                async for line in respuesta.aiter_lines():
                    if line:
                        # print("line:", line)
                        decodificado = json.loads(line)
                        actualizar_cancion(decodificado["id"], decodificado["letra"], decodificado["error"])
    except (json.JSONDecodeError | httpx.RequestError) as e:
        codigo_error = ''
        if e is httpx.RequestError:
            # print(f"Error de conexión: {e}")
            codigo_error = 'error_conexion'
        elif e is json.JSONDecodeError:
            # print(f"Error del servidor: {e}")
            codigo_error = 'error_del_servidor'

        for i, data_cancion in enumerate(formatted_canciones):
            if canciones[data_cancion['id']]['estado'] == EstadoCancionLetras.BUSCANDO:
                actualizar_cancion(data_cancion['id'], '', codigo_error)


def actualizar_cancion(id: int, letra: str, error: str):
    from interfaz import actualizar_cancion_en_hilo

    cancion = canciones[id]
    
    match error:
        case 'no_tiene_letras':
            cancion["estado"] = EstadoCancionLetras.LETRAS_NO_ENCONTRADAS
        case 'error_del_servidor':
            cancion['estado'] = EstadoCancionLetras.ERROR_CONEXION
        case 'error_conexion':
            cancion['estado'] = EstadoCancionLetras.ERROR_CONEXION
        case _:
            cancion["letra"] = letra
            escribir_letras_archivo(cancion)
            cancion['estado'] = EstadoCancionLetras.LETRAS_ANADIDAS
    
    # actualizar GUI
    actualizar_cancion_en_hilo(cancion, id)
    # print("Letra de", cancion["artista"], "-", cancion["titulo"], ":\n", cancion["letra"])


# Toma todos los archivos mp3 de una carpeta y si no tienen letra, las busca en genius.com y se las asigna
# (En desuso)
# def buscar_letras_cancion(cancion):
#     # global genius

#     # file = eyed3.load(cancion["ruta"])
    
#     # lyrics = file.tag.lyrics

#     if cancion['letras'] == '':
#         try:
#             # song_genius = genius.
#             lyrics = buscar_cancion_api({ "titulo": cancion["titulo"], "artista": cancion["artista"] })
            
#             if lyrics != None:
#                 cancion['letras'] = lyrics
#                 cancion['estado'] = EstadoCancionLetras.LETRAS_ANADIDAS

#                 escribir_letras_archivo(cancion)
#             else:
#                 print("No se obtuvo resultados para", cancion["artista"], "-", cancion["titulo"], "\n")
#                 cancion['estado'] = EstadoCancionLetras.LETRAS_NO_ENCONTRADAS
#         except (HTTPError, ConnectionError) as error:
#             print("Error de conexión:", error.strerror)
#             cancion['estado'] = EstadoCancionLetras.ERROR_CONEXION
#     else:
#         print("La cancion", cancion["artista"], "-", cancion["titulo"], "ya tenia letras", "\n")
        

def escribir_letras_archivo(cancion):
    file = eyed3.load(cancion["ruta"])
    file.tag.lyrics.set(cancion["letras"])
    file.tag.save()
    print("Letras añadidas al archivo:", cancion["ruta"])


def get_cancion(index):
    if index >= 0 and index < len(canciones):
        return canciones[index]
    else:
        return None


def actualizar_info_cancion(index, titulo: str, artista: str):
    cancion = get_cancion(index)
    if cancion:
        cancion['titulo'] = titulo
        cancion['artista'] = artista


def clear_canciones():
    canciones.clear()


def run_as_script():
    global carpeta, canciones
    obtener_mp3(carpeta)
    asyncio.run(buscar_letras_backend(canciones))


async def test():
    payload = {"items": [
        {"id": 0,  "titulo": "A rose for Epona", "artista": "Eluveitie"},
    ]}

    async with httpx.AsyncClient(timeout=20.0) as cliente:
        async with cliente.stream("POST", API_URL, json=payload) as respuesta:
            async for line in respuesta.aiter_lines():
                if line:
                    decodificado = json.loads(line)
                    print(decodificado)

if __name__ == '__main__':
    asyncio.run(test())

