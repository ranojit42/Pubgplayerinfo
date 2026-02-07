import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
# আপনার দেওয়া এপিআই কী এখানে সেট করা হয়েছে
PUBG_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI1ODVmN2M1MC1lMWEzLTAxM2UtMWUxYy01YTE3YTU3M2I3NjkiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzY5OTU0MDIzLCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Ii02YjgyZDg2Zi00YTdkLTQxMDgtYmRhMy1jNGY3NTViMDhiOGYifQ.cTg4YzqRz8_c-ETKx0RHZMIa9pO4UCG-zL_5ZKCOw3A"
SHARD = "steam" # pc: steam, kakao | console: xbox, psn

HEADERS = {
    "Authorization": f"Bearer {PUBG_API_KEY}",
    "Accept": "application/vnd.api+json"
}

def get_current_season():
    try:
        url = f"https://api.pubg.com/shards/{SHARD}/seasons"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            seasons = res.json().get('data', [])
            for s in seasons:
                if s.get('attributes', {}).get('isCurrentSeason'):
                    return s.get('id')
    except Exception as e:
        print(f"Season Error: {e}")
    return None

@app.route('/pubg', methods=['GET'])
def get_full_stats():
    player_name = request.args.get('name')
    if not player_name:
        return jsonify({"error": "Please provide a player name"}), 400

    try:
        # 1. Get Player ID
        p_res = requests.get(f"https://api.pubg.com/shards/{SHARD}/players?filter[playerNames]={player_name}", headers=HEADERS, timeout=10)
        
        if p_res.status_code != 200:
            return jsonify({"error": f"Player '{player_name}' not found or API error"}), p_res.status_code
        
        p_json = p_res.json()
        if not p_json.get('data'):
            return jsonify({"error": "No data found for this player"}), 404
            
        p_id = p_json['data'][0]['id']
        season_id = get_current_season()

        if not season_id:
            return jsonify({"error": "Could not find current season ID"}), 500

        # 2. Get Season Stats
        s_res = requests.get(f"https://api.pubg.com/shards/{SHARD}/players/{p_id}/seasons/{season_id}", headers=HEADERS, timeout=10)
        
        if s_res.status_code != 200:
            return jsonify({"error": "Failed to fetch season stats"}), s_res.status_code

        all_game_stats = s_res.json().get('data', {}).get('attributes', {}).get('gameModeStats', {})
        
        # Squad-FPP ডাটা না থাকলে সাধারণ Squad ডাটা চেক করবে
        stats = all_game_stats.get('squad-fpp') or all_game_stats.get('squad') or {}

        if not stats:
            return jsonify({"error": "No match stats found for this player in current season"}), 404

        # Calculation for K/D
        kills = stats.get('kills', 0)
        losses = stats.get('losses', 0)
        kd = round(kills / max(1, losses), 2)
        rounds = max(1, stats.get('roundsPlayed', 1))

        # 3. Organizing 15+ Data Points
        full_info = {
            "status": "success",
            "developer": "SEXTY MODS",
            "player_name": player_name,
            "data": {
                "01_Total_Kills": kills,
                "02_Total_Wins": stats.get('wins', 0),
                "03_KD_Ratio": kd,
                "04_Headshot_Kills": stats.get('headshotKills', 0),
                "05_Total_Damage": round(stats.get('damageDealt', 0), 2),
                "06_Assists": stats.get('assists', 0),
                "07_Longest_Kill": f"{round(stats.get('longestKill', 0), 2)}m",
                "08_Max_Kill_Streak": stats.get('maxKillStreaks', 0),
                "09_Top_10s": stats.get('top10s', 0),
                "10_Matches_Played": stats.get('roundsPlayed', 0),
                "11_Suicides": stats.get('suicides', 0),
                "12_Team_Kills": stats.get('teamKills', 0),
                "13_Road_Kills": stats.get('roadKills', 0),
                "14_Vehicle_Destroys": stats.get('vehicleDestroys', 0),
                "15_Survival_Time_Avg": f"{round(stats.get('timeSurvived', 0) / rounds / 60, 2)} mins",
                "16_Heals_Used": stats.get('heals', 0),
                "17_Boosts_Used": stats.get('boosts', 0),
                "18_Revives": stats.get('revives', 0)
            }
        }
        return jsonify(full_info)

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

# Vercel এর জন্য হোম রুট
@app.route('/')
def home():
    return "🔥 PUBG API is Live! Use: /pubg?name=PlayerName"

if __name__ == '__main__':
    app.run(debug=True)
