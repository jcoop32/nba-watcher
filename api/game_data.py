from nba_api.live.nba.endpoints import scoreboard

def get_scoreboard_data():
    # Today's Score Board
    games = scoreboard.ScoreBoard()
    g_to_dict = games.get_dict()
    print(g_to_dict["scoreboard"]["games"])
    all_game_scoreboard = g_to_dict["scoreboard"]["games"]
    game_scoreboards = {}
    for game in all_game_scoreboard:
        parts = game["gameCode"].split('/')
        teams = parts[1]
        home_scoreboard =  game["gameLeaders"]["homeLeaders"]
        away_scoreboard =  game["gameLeaders"]["awayLeaders"]
        data = {
            "game_status": game["gameStatusText"],
            "best_stats_home": f'{home_scoreboard["name"]} -  {home_scoreboard["points"]}pts - {home_scoreboard["rebounds"]}rebs - {home_scoreboard["assists"]}asts',
            "best_stats_away": f'{away_scoreboard["name"]} -  {away_scoreboard["points"]}pts - {away_scoreboard["rebounds"]}rebs - {home_scoreboard["assists"]}asts',
        }
        game_scoreboards[teams] = data

    return game_scoreboards

# scoreboard_data = get_scoreboard_data()
# print(scoreboard_data)
# print(scoreboard_data["GSWMIL"])

