# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from typing import List

# PUBG API Config
PUBG_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI1ODVmN2M1MC1lMWEzLTAxM2UtMWUxYy01YTE3YTU3M2I3NjkiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzY5OTU0MDIzLCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Ii02YjgyZDg2Zi00YTdkLTQxMDgtYmRhMy1jNGY3NTViMDhiOGYifQ.cTg4YzqRz8_c-ETKx0RHZMIa9pO4UCG-zL_5ZKCOw3A"
PUBG_REGION = "steam"  # steam / psn / xbox / kakao

app = FastAPI(
    title="PUBG Player Info API",
    version="1.0",
    description="Fetch PUBG player stats with suggestions and colored output"
)

class PlayerRequest(BaseModel):
    player_name: str

# ANSI color codes for Termux
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

@app.post("/pubg/player-info")
async def get_player_info(data: PlayerRequest):
    headers = {
        "Authorization": f"Bearer {PUBG_API_KEY}",
        "Accept": "application/vnd.api+json"
    }

    # Step 1: Search player
    search_url = f"https://api.pubg.com/shards/{PUBG_REGION}/players?filter[playerNames]={data.player_name}"
    res = requests.get(search_url, headers=headers)
    
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    
    player_data_list = res.json().get("data", [])
    
    if not player_data_list:
        return {
            "status": "error",
            "message": f"{RED}No exact player found matching '{data.player_name}'{RESET}",
            "suggestions": []  # API নিজে partial suggestions দেয় না, তাই আমরা empty রাখছি
        }
    
    results = []
    
    # Step 2: Fetch lifetime stats for each matched player
    for player in player_data_list:
        player_id = player["id"]
        player_name = player["attributes"]["name"]

        season_url = f"https://api.pubg.com/shards/{PUBG_REGION}/players/{player_id}/seasons/lifetime"
        season_res = requests.get(season_url, headers=headers)
        
        if season_res.status_code != 200:
            stats = {"error": season_res.text}
        else:
            stats = season_res.json()["data"]["attributes"]["gameModeStats"]
        
        results.append({
            "player_name": f"{GREEN}{player_name}{RESET}",
            "player_id": f"{BLUE}{player_id}{RESET}",
            "stats": stats
        })
    
    return {
        "status": "success",
        "results": results
    }
