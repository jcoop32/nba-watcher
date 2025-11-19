import requests
from utils.time_conversions import convert_et_to_cst_conditional, get_game_day_status, has_game_started
from services.redis_service import get_cache, set_cache

CACHE_TIMEOUT = 15
SCOREBOARD_URL = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"

session = requests.Session()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com'
}
session.headers.update(HEADERS)

def get_scoreboard_data(upcoming_games: list):
    """
    Fetches scoreboard data using a persistent HTTP session for speed.
    """

    full_scoreboard_data = get_cache("nba_scoreboard_live")

    if not full_scoreboard_data:
        try:
            response = session.get(SCOREBOARD_URL, timeout=5)
            response.raise_for_status()
            games = response.json()

            all_game_scoreboard = games["scoreboard"]["games"]
            full_scoreboard_data = {}

            for game in all_game_scoreboard:
                game_code = game["gameCode"].split('/')[1]

                home_leader = game["gameLeaders"].get("homeLeaders", {})
                away_leader = game["gameLeaders"].get("awayLeaders", {})

                data = {
                    "game_status": f"{convert_et_to_cst_conditional(game['gameStatusText'])}",
                    "quarter": game['gameStatusText'],
                    "game_started_yet": has_game_started(game["gameTimeUTC"]),
                    "today_or_tomorrow": get_game_day_status(game["gameTimeUTC"]),
                    "best_stats_home": f'{home_leader.get("name", "N/A")} - {home_leader.get("points", 0)}pts - {home_leader.get("rebounds", 0)}rebs - {home_leader.get("assists", 0)}asts',
                    "best_stats_away": f'{away_leader.get("name", "N/A")} - {away_leader.get("points", 0)}pts - {away_leader.get("rebounds", 0)}rebs - {away_leader.get("assists", 0)}asts',
                    "home_score": game["homeTeam"]["score"],
                    "away_score": game["awayTeam"]["score"],
                    "game_id": game["gameId"]
                }

                full_scoreboard_data[game_code] = data

                if len(game_code) == 6:
                    reversed_key = game_code[3:] + game_code[:3]
                    full_scoreboard_data[reversed_key] = data

            set_cache("nba_scoreboard_live", full_scoreboard_data, CACHE_TIMEOUT)

        except Exception as e:
            print(f"Scoreboard Fetch Error: {e}")
            full_scoreboard_data = {}

    result_scoreboards = {}

    for teams in upcoming_games:
        if teams in full_scoreboard_data:
            result_scoreboards[teams] = full_scoreboard_data[teams]
        else:
            result_scoreboards[teams] = {
                "game_status": "Scheduled",
                "game_started_yet": False,
                "best_stats_home": "N/A",
                "best_stats_away": "N/A",
                "home_score": 0,
                "away_score": 0,
                "game_id": None
            }

    return result_scoreboards
