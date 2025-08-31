import asyncio
import os
import json
import sys
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import httpx
from pydantic import BaseModel
import lyricsgenius
import requests
from dotenv import load_dotenv


app = FastAPI()

load_dotenv(".env")
GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_TOKEN")

if GENIUS_ACCESS_TOKEN:
    genius = lyricsgenius.Genius(
        GENIUS_ACCESS_TOKEN,
        remove_section_headers=True,
        skip_non_songs=False,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
    )
else:
    print("Error fatal: no se pudo iniciar genius")
    sys.exit(1)

class Cancion(BaseModel):
    id: int
    titulo: str
    artista: str

class Payload(BaseModel):
    items: list[Cancion]

def search_song_sync(titulo, artista, song_id):
    return genius.search_song(title=titulo, artist=artista, song_id=song_id)

async def search_song_async(titulo, artista, song_id):
    song = await asyncio.to_thread(search_song_sync, titulo, artista, song_id)
    return song

async def request_song(titulo: str, artista: str):
    base_url = "http://api.genius.com"
    headers = {'Authorization': 'Bearer ' + GENIUS_ACCESS_TOKEN}
    search_url = base_url + "/search"
    params = {'q': titulo}
    # response = requests.get(search_url, params=params, headers=headers)
    async with httpx.AsyncClient() as cliente:
        response = await cliente.get(search_url, params=params, headers=headers, follow_redirects=True)
        data = response.json()
    
    # json = response.json()

    # print(json)

    # send the full title of the song
    full_title = data['response']['hits'][0]['result']['full_title']
    artist = data['response']['hits'][0]['result']['primary_artist']['name']
    FullSearchTerm = f"{artist} {titulo}"
    # print(full_title)
    print(FullSearchTerm)

    # get the song ID
    song_id = data['response']['hits'][0]['result']['id']
    print(f"song_id is {song_id}")

    song = await search_song_async(titulo=titulo, artista=artist, song_id=song_id)
    print("lyrics:", song.lyrics)
    return song

async def buscar_cancion(cancion: Cancion):
    letra = ''
    error = ''

    try:
        # song_genius = genius.search_song(cancion.titulo, cancion.artista)
        song_genius = await request_song(cancion.titulo, cancion.artista)

        if song_genius and song_genius.lyrics:
            letra = song_genius.lyrics
        elif song_genius:
            error = "no_tiene_letras"
        else:
            error = "cancion_no_existe"
    except Exception as e:
        error = "error_del_servidor"
        print(e)
    print("returning")
    return {"id": cancion.id, "letra": letra, "error": error}

async def procesar_lista_canciones(canciones: list[Cancion]):
    for cancion in canciones:
        resultado = await buscar_cancion(cancion)
        yield json.dumps(resultado) + '\n'


@app.post("/api/procesar")
async def procesar(canciones: Payload):
    return StreamingResponse(procesar_lista_canciones(canciones.items), media_type="application/json")


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
