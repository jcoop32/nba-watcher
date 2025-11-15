from nba_api.live.nba.endpoints import scoreboard
from utils.time_conversions import convert_et_to_cst_conditional, get_game_day_status, has_game_started
import time

_SCOREBOARD_CACHE = {}
_LAST_FETCH_TIME = 0
CACHE_TIMEOUT = 15
def get_scoreboard_data(upcoming_games: list):
    global _SCOREBOARD_CACHE, _LAST_FETCH_TIME

    #CHECK CACHE: If data is fresh, return it immediately.
    if time.time() - _LAST_FETCH_TIME < CACHE_TIMEOUT:
        return {teams: _SCOREBOARD_CACHE.get(teams) for teams in upcoming_games if teams in _SCOREBOARD_CACHE}


    games = scoreboard.ScoreBoard().get_dict()
    all_game_scoreboard = games["scoreboard"]["games"]
    game_scoreboards = {}

    # This is the list of "correct" AWAYHOME tricodes from the NBA API
    today_game_codes = [g["gameCode"].split('/')[1] for g in all_game_scoreboard]

    for teams in upcoming_games:
        # --- START: New Logic ---

        game = None
        found_key = None

        if teams in today_game_codes:
            # The tricode (e.g., 'CHIDEN') was correct as-is
            found_key = teams
        else:
            # The tricode was not found. Let's try reversing it.
            if len(teams) == 6: # Safety check
                # e.g., 'DENCHI' -> 'CHI' + 'DEN' = 'CHIDEN'
                reversed_teams = teams[3:] + teams[:3]

                if reversed_teams in today_game_codes:
                    # The reversed key was correct!
                    found_key = reversed_teams

        if found_key:
            # We found the game, using either the original or reversed key
            game = next(g for g in all_game_scoreboard if found_key in g["gameCode"])

            # --- END: New Logic ---

            try:
                home_leader = game["gameLeaders"]["homeLeaders"]
                away_leader = game["gameLeaders"]["awayLeaders"]
                home_score = game["homeTeam"]["score"]
                away_score = game["awayTeam"]["score"]

                data = {
                    "game_status": f"{convert_et_to_cst_conditional(game['gameStatusText'])}",
                    "quarter": game['gameStatusText'],
                    "game_started_yet": has_game_started(game["gameTimeUTC"]),
                    "today_or_tomorrow": get_game_day_status(game["gameTimeUTC"]),
                    "best_stats_home": f'{home_leader["name"]} - {home_leader["points"]}pts - {home_leader["rebounds"]}rebs - {home_leader["assists"]}asts',
                    "best_stats_away": f'{away_leader["name"]} - {away_leader["points"]}pts - {away_leader["rebounds"]}rebs - {away_leader["assists"]}asts',
                    "home_score": home_score,
                    "away_score": away_score,
                    "game_id": game["gameId"]
                }
            except KeyError:
                # If game leaders are missing
                data = {
                    "game_status": f"{convert_et_to_cst_conditional(game['gameStatusText'])}",
                    "quarter": game['gameStatusText'],
                    "game_started_yet": has_game_started(game["gameTimeUTC"]),
                    "today_or_tomorrow": get_game_day_status(game["gameTimeUTC"]),
                    "best_stats_home": "N/A",
                    "best_stats_away": "N/A",
                    "home_score": game["homeTeam"]["score"],
                    "away_score": game["awayTeam"]["score"],
                    "game_id": game["gameId"]
                }
        else:
            # Not found (even after reversing) → game is likely tomorrow or later
            data = {
                "game_status": "Tommorrow",
                "game_started_yet": False,
                "best_stats_home": "N/A",
                "best_stats_away": "N/A",
                "home_score": 0,
                "away_score": 0,
                "game_id": None
            }

        # We use the *original* `teams` key here so the frontend gets
        # the data it asked for, regardless of which key we used to find it.
        game_scoreboards[teams] = data

    # 3. UPDATE CACHE: Store new data and timestamp
    _SCOREBOARD_CACHE = game_scoreboards
    _LAST_FETCH_TIME = time.time()

    return game_scoreboards
