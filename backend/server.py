import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv


app = FastAPI()

load_dotenv(".env")
# GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_TOKEN")
KEY_PASSWORD = os.getenv("KEY_PASSWORD")
ENCRYPTED_TOKEN = os.getenv("ENCRYPTED_TOKEN")

class Password(BaseModel):
    key: str


@app.get("/getkey")
async def get_api_key(password: Password):
    if password.key == KEY_PASSWORD:
        return {"password": ENCRYPTED_TOKEN}
    else:
        return ""


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
