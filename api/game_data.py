from nba_api.live.nba.endpoints import scoreboard
from utils.game_start import has_game_started

def get_scoreboard_data(upcoming_games: list):
    games = scoreboard.ScoreBoard().get_dict()
    all_game_scoreboard = games["scoreboard"]["games"]
    game_scoreboards = {}

    # Create a set of all today's game codes for quick lookup
    today_game_codes = [g["gameCode"].split('/')[1] for g in all_game_scoreboard]

    for teams in upcoming_games:
        if teams in today_game_codes:
            game = next(g for g in all_game_scoreboard if teams in g["gameCode"])
            try:
                home_leader = game["gameLeaders"]["homeLeaders"]
                away_leader = game["gameLeaders"]["awayLeaders"]
                data = {
                    "game_status": game["gameStatusText"],
                    "game_started_yet": has_game_started(game["gameTimeUTC"]),
                    "best_stats_home": f'{home_leader["name"]} - {home_leader["points"]}pts - {home_leader["rebounds"]}rebs - {home_leader["assists"]}asts',
                    "best_stats_away": f'{away_leader["name"]} - {away_leader["points"]}pts - {away_leader["rebounds"]}rebs - {away_leader["assists"]}asts',
                }
            except KeyError:
                # Game leaders might not exist yet if the game hasn’t started
                data = {
                    "game_status": game["gameStatusText"],
                    "game_started_yet": has_game_started(game["gameTimeUTC"]),
                    "best_stats_home": "N/A",
                    "best_stats_away": "N/A",
                }
        else:
            # Not found → game is likely tomorrow or later
            data = {
                "game_status": "Scheduled (no data yet)",
                "game_started_yet": False,
                "best_stats_home": "N/A",
                "best_stats_away": "N/A",
            }

        game_scoreboards[teams] = data

    return game_scoreboards


# games = ['NOPOKC', 'PHIBKN', 'UTACHA', 'ATLCLE', 'MEMTOR', 'CHINYK', 'SASPHX', 'MIALAL', 'MINBKN', 'MILIND', 'UTABOS', 'WASNYK', 'DALHOU', 'DETMEM', 'SACDEN', 'LALPOR', 'MIALAC']
# print(get_scoreboard_data(games))
