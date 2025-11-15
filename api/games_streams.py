import requests
import json
from datetime import datetime
from utils.get_team_abbreves import get_normalized_team_key, abv
from utils.time_conversions import format_et_to_cst_status, convert_ms_to_yyyymmdd

def get_basketball_games_source_1():
    """Fetches from Lotus.xyz and returns a dict keyed by 'YYYY-MM-DD_TEAMKEY'"""
    API_URL = "https://lotusgamehd.xyz/api-event.php?league=nba"
    games_dict = {}

    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        for day in data.get("days", []):
            for game in day.get("items", []):

                # 1. Get normalized team key
                team_key, title, away, home = get_normalized_team_key(game["title"])
                if not team_key:
                    continue

                # 2. Get normalized date key
                try:
                    date_str = datetime.strptime(game["when_et"], "%Y-%m-%d %H:%M").strftime("%Y-%m-%d")
                except ValueError:
                    continue

                game_key = f"{date_str}_{team_key}"

                game_id = int(game["hds"][0])
                stream_url = f"https://lotusgamehd.xyz/lotushd.php?hd={game_id}"

                teams = game["title"].split(" - ")
                away_team = teams[1]
                home_team = teams[0]
                new_title = f'{away_team} vs. {home_team}'

                game_data = {
                    "id": game_key,
                    "title": new_title,
                    "game_start": format_et_to_cst_status(game["when_et"]),
                    "status": f"🔴 {game['status']}" if game["status"] == "LIVE" else game["status"],
                    "teams": away + home,
                    "away_tricode": abv[away_team],
                    "home_tricode": abv[home_team],
                    "streams": [stream_url]
                }
                games_dict[game_key] = game_data

    except Exception as e:
        print(f"An unexpected error occurred in source 1: {e}")

    return games_dict

def get_basketball_games_source_2():
    API_URL = "https://streamed.pk/api/matches/basketball"
    games_dict = {}

    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        for game in data:
            team_key, title, away, home = get_normalized_team_key(game["title"])
            if not team_key:
                continue

            # 2. Get normalized date key
            date_str = convert_ms_to_yyyymmdd(game["date"])
            if not date_str:
                continue

            # Use the SORTED key for merging
            game_key = f"{date_str}_{team_key}"

            streams_list = []
            for source in game.get("sources", []):
                if source.get("id"):
                    stream_url = f"https://embedsports.top/embed/{source['source']}/{source['id']}/1"
                    streams_list.append(stream_url)

            if not streams_list:
                continue

            game_data = {
                "id": game_key,
                "title": title,
                "game_start": convert_ms_to_yyyymmdd(game["date"]) if "date" in game else "TBD", # S2 API doesn't have this, use S1's if merged
                "status": game.get("status", "Scheduled"),
                "teams": away + home,
                "away_tricode": away,
                "home_tricode": home,
                "streams": streams_list
            }
            games_dict[game_key] = game_data

    except Exception as e:
        print(f"An unexpected error occurred in source 2: {e}")

    return games_dict

def get_basketball_games():
    # print("Fetching games from Source 1 (Lotus)...")
    games_s1_dict = get_basketball_games_source_1()
    # print("Fetching games from Source 2 (Streamed.pk)...")
    games_s2_dict = get_basketball_games_source_2()

    merged_games = {}

    merged_games.update(games_s1_dict)

    for game_key, game_s2 in games_s2_dict.items():
        if game_key in merged_games:
            # GAME ALREADY EXISTS! Append streams.
            merged_games[game_key]["streams"].extend(game_s2["streams"])
        # else:
        #     # This is a new game, just add it
        #     merged_games[game_key] = game_s2

    # Return the merged games as a list
    return list(merged_games.values())

# print(get_basketball_games())
