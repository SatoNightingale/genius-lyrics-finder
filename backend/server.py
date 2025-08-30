import os
import json
import sys
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import lyricsgenius


app = FastAPI()

GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_TOKEN")

if GENIUS_ACCESS_TOKEN:
    genius = lyricsgenius.Genius(
        GENIUS_ACCESS_TOKEN,
        remove_section_headers=True,
        skip_non_songs=False,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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


async def buscar_cancion(cancion: Cancion):
    letra = ''
    error = ''

    try:
        song_genius = genius.search_song(cancion.titulo, cancion.artista)

        if song_genius and song_genius.lyrics:
            letra = song_genius.lyrics
        elif song_genius:
            error = "no_tiene_letras"
        else:
            error = "cancion_no_existe"
    except Exception as e:
        error = f"error_del_servidor: {e}"
    
    return {"id": cancion.id, "letra": letra, "error": error}

    # ya luego puedo poner excepciones y eso

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
