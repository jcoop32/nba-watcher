from flask import Flask, render_template, abort, jsonify
from api.scoreboard_data import get_scoreboard_data
from api.boxscore_data import get_single_game_boxscore
from datetime import date
from api.games_streams import get_basketball_games
import time
from utils.get_team_abbreves import team_colors, nba_logo_code

current_date = date.today().strftime("%Y-%m-%d")

app = Flask(__name__)

RAW_GAMES_LIST = []
_GAMES_LIST_CACHE_TIME = 0
GAMES_LIST_CACHE_TIMEOUT = 3600

def get_game_list_from_cache_or_api():
    global RAW_GAMES_LIST, _GAMES_LIST_CACHE_TIME
    if not RAW_GAMES_LIST or (time.time() - _GAMES_LIST_CACHE_TIME > GAMES_LIST_CACHE_TIMEOUT):
        RAW_GAMES_LIST = get_basketball_games()
        _GAMES_LIST_CACHE_TIME = time.time()
    return RAW_GAMES_LIST

@app.route('/')
def index():
    games_list = get_game_list_from_cache_or_api()

    for game in games_list:
        teams_tricode = game["teams"]
        away_tricode = teams_tricode[:3]
        home_tricode = teams_tricode[3:]
        default_color = "#333333"
        away_color = team_colors.get(away_tricode, default_color)
        home_color = team_colors.get(home_tricode, default_color)

        game["away_color"] = away_color
        game["home_color"] = home_color
        game["away_logo"] = nba_logo_code[away_tricode]
        game["home_logo"] = nba_logo_code[home_tricode]

    scoreboard_data_teams = [game["teams"] for game in games_list]

    scoreboard_data = get_scoreboard_data(scoreboard_data_teams)
    return render_template('index.html', games=games_list, sb_data=scoreboard_data)

@app.route('/api/scoreboard')
def api_scoreboard():
    games_list = get_game_list_from_cache_or_api()
    scoreboard_data_teams = [game["teams"] for game in games_list]

    scoreboard_data = get_scoreboard_data(scoreboard_data_teams)

    response_data = {}
    for game in games_list:
        teams_key = game["teams"]
        if teams_key in scoreboard_data:
            response_data[teams_key] = scoreboard_data[teams_key]

    return jsonify(response_data)

@app.route('/api/boxscore/<game_id>')
def api_boxscore(game_id):
    boxscore_data = get_single_game_boxscore(game_id)
    return jsonify(boxscore_data)


@app.route('/watch/<stream_id>')
def iframe_viewer(stream_id):
    games_list = get_game_list_from_cache_or_api()

    BASKETBALL_STREAMS = {stream['id']: stream for stream in games_list}
    stream_info = BASKETBALL_STREAMS.get(int(stream_id))

    if stream_info:
        scoreboard_data_raw = get_scoreboard_data([stream_info['teams']])

        game_id_nba = None
        for game_item in scoreboard_data_raw.get('scoreboard', {}).get('games', []):
            if stream_info['teams'] in game_item['gameCode']:
                game_id_nba = game_item['gameId']
                break


        id = stream_info.get('id')
        if not id:
            abort(404, description="Stream found, but embed URL is missing.")

        return render_template('stream.html',
                               id=id,
                               title=stream_info['title'],
                               game_id_nba=game_id_nba,
                               teams=stream_info['teams'])
    else:
        abort(404, description=f"stream ID {stream_id} not found in the basketball list.")

if __name__ == '__main__':
    _GAMES_LIST_CACHE_TIME = time.time()
    app.run(debug=True)
