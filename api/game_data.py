from nba_api.live.nba.endpoints import scoreboard
from utils.game_start import has_game_started

def get_scoreboard_data():
    games = scoreboard.ScoreBoard()
    g_to_dict = games.get_dict()
    all_game_scoreboard = g_to_dict["scoreboard"]["games"]
    game_scoreboards = {}
    for game in all_game_scoreboard:
        parts = game["gameCode"].split('/')
        teams = parts[1]
        home_scoreboard =  game["gameLeaders"]["homeLeaders"]
        away_scoreboard =  game["gameLeaders"]["awayLeaders"]
        data = {
            "game_status": game["gameStatusText"],
            "game_started_yet": has_game_started(game["gameTimeUTC"]),
            "best_stats_home": f'{home_scoreboard["name"]} -  {home_scoreboard["points"]}pts - {home_scoreboard["rebounds"]}rebs - {home_scoreboard["assists"]}asts',
            "best_stats_away": f'{away_scoreboard["name"]} -  {away_scoreboard["points"]}pts - {away_scoreboard["rebounds"]}rebs - {home_scoreboard["assists"]}asts',
        }
        game_scoreboards[teams] = data

    return game_scoreboards



