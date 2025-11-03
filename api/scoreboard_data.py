from nba_api.live.nba.endpoints import scoreboard, PlayByPlay
from utils.time_conversions import convert_et_to_cst_conditional, get_game_day_status, has_game_started
import time # <--- NEW IMPORT

# Global cache variables for NBA Scoreboard data
_SCOREBOARD_CACHE = {}
_LAST_FETCH_TIME = 0
CACHE_TIMEOUT = 10  # Seconds to wait before hitting the NBA API again (recommended 5-15s)

def get_scoreboard_data(upcoming_games: list):
    global _SCOREBOARD_CACHE, _LAST_FETCH_TIME

    # 1. CHECK CACHE: If data is fresh, return it immediately.
    if time.time() - _LAST_FETCH_TIME < CACHE_TIMEOUT:
        # Filter and return only the requested games from the global cache
        return {teams: _SCOREBOARD_CACHE.get(teams) for teams in upcoming_games if teams in _SCOREBOARD_CACHE}


    # 2. FETCH FRESH DATA: If cache is stale, perform the expensive API calls.
    games = scoreboard.ScoreBoard().get_dict()
    all_game_scoreboard = games["scoreboard"]["games"]
    game_scoreboards = {}

    # Create a set of all today's game codes for quick lookup
    today_game_codes = [g["gameCode"].split('/')[1] for g in all_game_scoreboard]

    for teams in upcoming_games:
        if teams in today_game_codes:
            game = next(g for g in all_game_scoreboard if teams in g["gameCode"])

            # --- Last Play Retrieval Logic ---
            last_game_event = "Game has not started or data is unavailable."
            game_started = game["gameStatus"] > 1 # Game Status 1 is Scheduled

            if game_started:
                try:
                    game_id = game["gameId"]
                    # Call the PlayByPlay endpoint for a single, active game
                    pbp = PlayByPlay(game_id=game_id).get_dict()
                    # Get the list of actions/plays, or an empty list if missing
                    plays = pbp.get("playByPlay", {}).get("actions", [])

                    if plays:
                        # The last play description is the 'description' field of the last action
                        last_game_event = plays[-1].get("description", "Last play description unavailable.")
                    else:
                        last_game_event = "Game in progress, no plays recorded yet."
                except Exception:
                    last_game_event = "Could not fetch last event due to an API error."
            # --- End Last Play Retrieval Logic ---

            try:
                home_leader = game["gameLeaders"]["homeLeaders"]
                away_leader = game["gameLeaders"]["awayLeaders"]

                # DATA EXTRACTION
                home_score = game["homeTeam"]["score"]
                away_score = game["awayTeam"]["score"]
                period = game["period"]
                game_clock = game["gameClock"]

                data = {
                    "game_status": convert_et_to_cst_conditional(game["gameStatusText"]),
                    "game_started_yet": has_game_started(game["gameTimeUTC"]),
                    "today_or_tomorrow": get_game_day_status(game["gameTimeUTC"]),
                    "best_stats_home": f'{home_leader["name"]} - {home_leader["points"]}pts - {home_leader["rebounds"]}rebs - {home_leader["assists"]}asts',
                    "best_stats_away": f'{away_leader["name"]} - {away_leader["points"]}pts - {away_leader["rebounds"]}rebs - {away_leader["assists"]}asts',
                    "home_score": home_score,
                    "away_score": away_score,
                    "period": period,
                    "game_clock": game_clock,
                    "last_game_event": last_game_event,
                }
            except KeyError:
                # If game leaders are missing
                data = {
                    "game_status": convert_et_to_cst_conditional(game["gameStatusText"]),
                    "game_started_yet": has_game_started(game["gameTimeUTC"]),
                    "today_or_tomorrow": get_game_day_status(game["gameTimeUTC"]),
                    "best_stats_home": "N/A",
                    "best_stats_away": "N/A",
                    "home_score": game["homeTeam"]["score"],
                    "away_score": game["awayTeam"]["score"],
                    "period": game["period"],
                    "game_clock": game["gameClock"],
                    "last_game_event": last_game_event,
                }
        else:
            # Not found → game is likely tomorrow or later
            data = {
                "game_status": "Scheduled (no data yet)",
                "game_started_yet": False,
                "best_stats_home": "N/A",
                "best_stats_away": "N/A",
                "home_score": 0,
                "away_score": 0,
                "period": 0,
                "game_clock": "",
                "last_game_event": "Game has not started or data is unavailable.",
            }

        game_scoreboards[teams] = data

    # 3. UPDATE CACHE: Store new data and timestamp
    _SCOREBOARD_CACHE = game_scoreboards
    _LAST_FETCH_TIME = time.time()

    return game_scoreboards
