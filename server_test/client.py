import httpx

url = "http://127.0.0.1:8000/"

with httpx.Client() as client:
    response = client.post(url)
    data = response.json()
    print(data)