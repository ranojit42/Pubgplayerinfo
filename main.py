import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
PUBG_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI1ODVmN2M1MC1lMWEzLTAxM2UtMWUxYy01YTE3YTU3M2I3NjkiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzY5OTU0MDIzLCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Ii02YjgyZDg2Zi00YTdkLTQxMDgtYmRhMy1jNGY3NTViMDhiOGYifQ.cTg4YzqRz8_c-ETKx0RHZMIa9pO4UCG-zL_5ZKCOw3A" # আপনার API KEY এখানে দিন
SHARD = "steam" # pc: steam, kakao | console: xbox, psn

HEADERS = {
    "Authorization": f"Bearer {PUBG_API_KEY}",
    "Accept": "application/vnd.api+json"
}

def get_current_season():
    url = f"https://api.pubg.com/shards/{SHARD}/seasons"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        for s in res.json()['data']:
            if s['attributes']['isCurrentSeason']:
                return s['id']
    return None

@app.route('/pubg', methods=['GET'])
def get_full_stats():
    player_name = request.args.get('name')
    if not player_name:
        return jsonify({"error": "Please provide a player name"}), 400

    try:
        # 1. Get Player ID
        p_res = requests.get(f"https://api.pubg.com/shards/{SHARD}/players?filter[playerNames]={player_name}", headers=HEADERS)
        if p_res.status_code != 200:
            return jsonify({"error": "Player not found"}), 404
        
        p_data = p_res.json()['data'][0]
        p_id = p_data['id']
        season_id = get_current_season()

        # 2. Get Season Stats
        s_res = requests.get(f"https://api.pubg.com/shards/{SHARD}/players/{p_id}/seasons/{season_id}", headers=HEADERS)
        stats = s_res.json()['data']['attributes']['gameModeStats'].get('squad-fpp', {})

        if not stats:
            return jsonify({"error": "No stats found for current season"}), 404

        kills = stats.get('kills', 0)
        losses = stats.get('losses', 0)
        kd = round(kills / max(1, losses), 2)

        full_info = {
            "status": "success",
            "developer": "SEXTY MODS",
            "player_name": player_name,
            "data": {
                "1_Total_Kills": kills,
                "2_Total_Wins": stats.get('wins', 0),
                "3_KD_Ratio": kd,
                "4_Headshot_Kills": stats.get('headshotKills', 0),
                "5_Total_Damage": round(stats.get('damageDealt', 0), 2),
                "6_Assists": stats.get('assists', 0),
                "7_Longest_Kill": f"{round(stats.get('longestKill', 0), 2)}m",
                "8_Max_Kill_Streak": stats.get('maxKillStreaks', 0),
                "9_Top_10s": stats.get('top10s', 0),
                "10_Matches_Played": stats.get('roundsPlayed', 0),
                "11_Suicides": stats.get('suicides', 0),
                "12_Team_Kills": stats.get('teamKills', 0),
                "13_Road_Kills": stats.get('roadKills', 0),
                "14_Vehicle_Destroys": stats.get('vehicleDestroys', 0),
                "15_Survival_Time_Avg": f"{round(stats.get('timeSurvived', 0) / max(1, stats.get('roundsPlayed', 1)) / 60, 2)} mins",
                "16_Heals_Used": stats.get('heals', 0),
                "17_Boosts_Used": stats.get('boosts', 0),
                "18_Revives": stats.get('revives', 0)
            }
        }
        return jsonify(full_info)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Vercel এর জন্য এটি প্রয়োজনীয়
@app.route('/')
def home():
    return "PUBG API is Live! Use /pubg?name=PlayerName"

if __name__ == '__main__':
    app.run(debug=True)
