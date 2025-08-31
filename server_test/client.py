import httpx

url = "https://genius-lyrics-finder-satonightingale8475-yooxz7gs.leapcell.dev/buscar"

with httpx.Client() as client:
    response = client.post(url)
    data = response.json()
    print(data)