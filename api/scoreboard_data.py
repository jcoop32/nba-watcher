from nba_api.live.nba.endpoints import scoreboard
from utils.time_conversions import convert_et_to_cst_conditional, get_game_day_status, has_game_started
from utils.redis_service import get_cache, set_cache

CACHE_TIMEOUT = 15

def get_scoreboard_data(upcoming_games: list):
    """
    Fetches scoreboard data for the requested list of teams (tricodes).
    Uses Redis to cache the full NBA scoreboard to minimize API calls.
    """

    # 1. Try to get the full scoreboard from Redis
    full_scoreboard_data = get_cache("nba_scoreboard_live")

    if not full_scoreboard_data:
        # 2. If cache miss, fetch fresh data from NBA API
        try:
            games = scoreboard.ScoreBoard().get_dict()
            all_game_scoreboard = games["scoreboard"]["games"]
            full_scoreboard_data = {}

            # Process ALL games currently on the board
            for game in all_game_scoreboard:
                # Extract keys cleanly
                game_code = game["gameCode"].split('/')[1] # e.g., 'BOSLAL'

                home_leader = game["gameLeaders"].get("homeLeaders", {})
                away_leader = game["gameLeaders"].get("awayLeaders", {})

                # Build the game data object
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

                # Store using the standard tricode (e.g. BOSLAL)
                full_scoreboard_data[game_code] = data

                # Also store reversed key just in case (LALBOS) to handle different source formats
                if len(game_code) == 6:
                    reversed_key = game_code[3:] + game_code[:3]
                    full_scoreboard_data[reversed_key] = data

            # 3. Save the COMPLETE processed data to Redis
            set_cache("nba_scoreboard_live", full_scoreboard_data, CACHE_TIMEOUT)

        except Exception as e:
            print(f"Scoreboard API Error: {e}")
            full_scoreboard_data = {}

    # 4. Filter the full data for the specific games requested by the frontend
    result_scoreboards = {}

    for teams in upcoming_games:
        if teams in full_scoreboard_data:
            result_scoreboards[teams] = full_scoreboard_data[teams]
        else:
            # Fallback for games not found (e.g. games tomorrow that aren't on today's scoreboard yet)
            result_scoreboards[teams] = {
                "game_status": "Tomorrow", # Or "Scheduled"
                "game_started_yet": False,
                "best_stats_home": "N/A",
                "best_stats_away": "N/A",
                "home_score": 0,
                "away_score": 0,
                "game_id": None
            }

    return result_scoreboards
