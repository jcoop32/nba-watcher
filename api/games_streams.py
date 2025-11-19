import requests
import concurrent.futures
from datetime import datetime
import pytz
from utils.get_team_abbreves import get_normalized_team_key, abv
from utils.time_conversions import format_et_to_cst_status, convert_ms_to_yyyymmdd

session = requests.Session()

# 2. Define headers to mimic a real browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}
session.headers.update(HEADERS)

def get_basketball_games_source_1():
    """Fetches from Lotus.xyz and returns a dict keyed by 'YYYY-MM-DD_TEAMKEY'"""
    API_URL = "https://lotusgamehd.xyz/api-event.php?league=nba"
    games_dict = {}

    try:
        response = session.get(API_URL, timeout=10)
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

                # 3. Calculate Timestamp for Polling Gatekeeper (ET -> UTC Timestamp)
                try:
                    et_tz = pytz.timezone('US/Eastern')
                    dt_object = datetime.strptime(game["when_et"], "%Y-%m-%d %H:%M")
                    dt_aware = et_tz.localize(dt_object)
                    game_timestamp = dt_aware.timestamp()
                except Exception:
                    game_timestamp = 0

                # 4. Create stream object
                game_id = int(game["hds"][0])
                stream_url = f"https://lotusgamehd.xyz/lotushd.php?hd={game_id}"

                teams = game["title"].split(" - ")
                if len(teams) == 2:
                    away_team = teams[1]
                    home_team = teams[0]
                    new_title = f'{away_team} vs. {home_team}'
                else:
                    new_title = title

                game_data = {
                    "id": game_key,
                    "title": new_title,
                    "start_timestamp": game_timestamp, # Used by frontend to delay polling
                    "game_start": format_et_to_cst_status(game["when_et"]),
                    "status": f"🔴 {game['status']}" if game["status"] == "LIVE" else game["status"],
                    "teams": away + home,
                    "away_tricode": abv.get(away_team, away), # Safety get
                    "home_tricode": abv.get(home_team, home), # Safety get
                    "streams": [stream_url]
                }
                games_dict[game_key] = game_data

    except Exception as e:
        print(f"An unexpected error occurred in source 1: {e}")

    return games_dict

def get_basketball_games_source_2():
    """Fetches from Streamed.pk and returns a dict keyed by 'YYYY-MM-DD_TEAMKEY'"""
    API_URL = "https://streamed.pk/api/matches/basketball"
    games_dict = {}

    try:
        response = session.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        for game in data:
            team_key, title, away, home = get_normalized_team_key(game["title"])
            if not team_key:
                continue

            date_str = convert_ms_to_yyyymmdd(game["date"])
            if not date_str:
                continue

            game_key = f"{date_str}_{team_key}"

            game_timestamp = game.get("date", 0) / 1000

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
                "start_timestamp": game_timestamp,
                "game_start": convert_ms_to_yyyymmdd(game["date"]) if "date" in game else "TBD",
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
    """
    Fetches games from both sources in PARALLEL to reduce wait time.
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_1 = executor.submit(get_basketball_games_source_1)
        future_2 = executor.submit(get_basketball_games_source_2)

        games_s1_dict = future_1.result()
        games_s2_dict = future_2.result()

    merged_games = {}
    merged_games.update(games_s1_dict)

    for game_key, game_s2 in games_s2_dict.items():
        if game_key in merged_games:
            existing_streams = merged_games[game_key]["streams"]
            for s in game_s2["streams"]:
                if s not in existing_streams:
                    existing_streams.append(s)
        # else:
        #     # This is a new game, just add it
        #     merged_games[game_key] = game_s2

    return list(merged_games.values())
