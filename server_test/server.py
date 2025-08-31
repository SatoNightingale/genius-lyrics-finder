import asyncio
import json
import os
import sys
from dotenv import load_dotenv
import httpx
from pydantic import BaseModel
import requests
import lyricsgenius
import fastapi

app = fastapi.FastAPI()

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


# headers = {
#     "Authorization": f"Bearer {GENIUS_TOKEN}",
#     # "User-Agent": "Mozilla/5.0"
# }

# params = {
#     "q": "Elvenpath Nightwish"
# }

# response = requests.get("https://api.genius.com/search", headers=headers, params=params)

# data = response.json()
# hits = data["response"]["hits"]

# for hit in hits:
#     title = hit["result"]["title"]
#     artist = hit["result"]["primary_artist"]["name"]
#     url = hit["result"]["url"]
#     print(f"{title} by {artist} → {url}")





# async def buscar(search_url, params, headers):
#     async with httpx.AsyncClient() as cliente:
#         response = await cliente.get(search_url, params=params, headers=headers, follow_redirects=True)
#         data = response.json()
#         return data




# base_url = "http://api.genius.com"
# headers = {'Authorization': 'Bearer ' + GENIUS_TOKEN}
# search_url = base_url + "/search"
# song_title = "A rose for Epona" # the arg is given by the user
# params = {'q': song_title}
# # response = requests.get(search_url, params=params, headers=headers)

# json = asyncio.run(buscar(search_url, params, headers))
# # json = data.json()

# # print(json)

# # send the full title of the song
# full_title = json['response']['hits'][0]['result']['full_title']
# artist = json['response']['hits'][0]['result']['primary_artist']['name']
# FullSearchTerm = f"{artist} {song_title}"
# print(full_title)
# print(FullSearchTerm)

# # get the song ID
# song_id = json['response']['hits'][0]['result']['id']
# print(f"song_id is {song_id}")

# song = genius.search_song(title=full_title, artist=artist, song_id=song_id)
# print(song.lyrics)



@app.post("/buscar")
async def buscar():
    titulo = "A rose for Epona"
    autor = "Eluveitie"
    search_term = f"{autor} {titulo}"
    print(search_term)
    songs = genius.search_songs(search_term)["hits"]

    for song in songs:
        song = song["result"]
        
        # if song['title'] == "Rap God":
        song_id = song['id']
        print(song_id)
        print(song['title'])
        song = genius.song(song_id)['song']
        lyrics = genius.lyrics(song_id)
        print(lyrics)
        return lyrics