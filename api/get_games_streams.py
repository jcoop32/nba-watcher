import requests
import json
from utils.get_team_abbreves import extract_teams_from_game_title
from utils.game_time_conversion import convert_time_and_check_day_12hr as convert_time

API_URL = "https://lotusgamehd.xyz/api-event.php?league=nba"


def get_basketball_games():
    try:
        print(f"Fetching data from: {API_URL}")
        response = requests.get(API_URL, timeout=10)

        response.raise_for_status()

        data = response.json()

        all_games = data
        basketball_games = []
        for day in all_games["days"]:
            for game in day["items"]:
                title, teams = extract_teams_from_game_title(game["title"])
                game_data = {
                    "title": title,
                    "start_time": convert_time(game["when_et"]),
                    "status": f"🔴 {game['status']}" if game["status"] == "LIVE" else game["status"],
                    "teams": teams,
                    "id": int(game["hds"][0]),
                    "link": game["streams"][0]["link"]
                }
                basketball_games.append(game_data)

        return basketball_games

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching data: {e}")
        return []
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

# print(get_basketball_games())
