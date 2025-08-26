import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import lyricsgenius


app = FastAPI()

GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_TOKEN", 'SPqGfxsIk4OkUD2mKptJfGWxz-2bhjlcAIT0zAWfVACV5df3Hu5uz4ndVBfA7tws')

genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN, remove_section_headers=True, skip_non_songs=True)


class Cancion(BaseModel):
    id: int
    titulo: str
    artista: str

class Payload(BaseModel):
    items: list[Cancion]


async def buscar_cancion(cancion: Cancion):
    song_genius = genius.search_song(cancion.titulo, cancion.artista)
    
    letra = ''
    error = ''

    if song_genius:
        if song_genius.lyrics:
            letra = song_genius.lyrics
        else:
            error = "no_tiene_letras"
    else:
        error = "error_del_servidor"
    
    return {"id": cancion.id, "letra": letra, "error": error}

    # ya luego puedo poner excepciones y eso

async def procesar_lista_canciones(canciones: list[Cancion]):
    for cancion in canciones:
        resultado = await buscar_cancion(cancion)
        yield json.dumps(resultado) + '\n'


@app.post("/api/procesar")
async def procesar(canciones: Payload):
    return StreamingResponse(procesar_lista_canciones(canciones.items), media_type="application/json")
