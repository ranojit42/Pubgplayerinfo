from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

PUBG_API_KEY = "YOUR_PUBG_KEY"
PUBG_REGION = "steam"

class PlayerRequest(BaseModel):
    player_name: str

@app.post("/api/player-info")
async def player_info(data: PlayerRequest):
    headers = {
        "Authorization": f"Bearer {PUBG_API_KEY}",
        "Accept": "application/vnd.api+json"
    }
    url = f"https://api.pubg.com/shards/{PUBG_REGION}/players?filter[playerNames]={data.player_name}"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    data = res.json().get("data", [])
    if not data:
        return {"status":"error","message":"No player found"}
    player_id = data[0]["id"]
    stats_url = f"https://api.pubg.com/shards/{PUBG_REGION}/players/{player_id}/seasons/lifetime"
    stats_res = requests.get(stats_url, headers=headers)
    if stats_res.status_code != 200:
        stats = {"error": stats_res.text}
    else:
        stats = stats_res.json()["data"]["attributes"]["gameModeStats"]
    return {"player_name": data[0]["attributes"]["name"], "player_id": player_id, "stats": stats}
