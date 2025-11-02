from flask import Flask, render_template, abort
# from api.scrap_data import get_nba_streams
from api.game_data import get_scoreboard_data
# from utils.check_if_game_exists import check_game
from datetime import date
from api.get_games_streams import get_basketball_games

current_date = date.today().strftime("%Y-%m-%d")

app = Flask(__name__)

# RAW_GAMES_LIST = get_nba_streams()
RAW_GAMES_LIST = get_basketball_games()
# print(RAW_GAMES_LIST)


BASKETBALL_STREAMS = {stream['stream_id']: stream for stream in RAW_GAMES_LIST}

scoreboard_data_teams = [game["teams"] for game in RAW_GAMES_LIST]

# print(scoreboard_data_teams)

scoreboard_data = get_scoreboard_data(scoreboard_data_teams)
# print(scoreboard_data)

# TODO: fix scoreboard data to be able to integrate well with stream api

@app.route('/')
def index():
    return render_template('index.html', games=RAW_GAMES_LIST, sb_data=scoreboard_data)

@app.route('/watch/<stream_id>')
def iframe_viewer(stream_id):

    stream_info = BASKETBALL_STREAMS.get(stream_id)

    if stream_info:
        id = stream_info.get('id')
        if not id:
            abort(404, description="Stream found, but embed URL is missing.")

        return render_template('stream.html', id=id, title=stream_info.get('title'))
    else:
        abort(404, description=f"stream ID {stream_id} not found in the basketball list.")


if __name__ == '__main__':
    app.run(debug=True)
