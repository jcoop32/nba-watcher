from flask import Flask, render_template, abort
from api.scoreboard_data import get_scoreboard_data
from datetime import date
from api.games_streams import get_basketball_games

current_date = date.today().strftime("%Y-%m-%d")

app = Flask(__name__)

@app.route('/')
def index():
    global RAW_GAMES_LIST
    RAW_GAMES_LIST = get_basketball_games()

    scoreboard_data_teams = [game["teams"] for game in RAW_GAMES_LIST]

    scoreboard_data = get_scoreboard_data(scoreboard_data_teams)
    return render_template('index.html', games=RAW_GAMES_LIST, sb_data=scoreboard_data)

@app.route('/watch/<stream_id>')
def iframe_viewer(stream_id):
    BASKETBALL_STREAMS = {stream['id']: stream for stream in RAW_GAMES_LIST}
    stream_info = BASKETBALL_STREAMS.get(int(stream_id))
    if stream_info:
        id = stream_info.get('id')
        if not id:
            abort(404, description="Stream found, but embed URL is missing.")
        return render_template('stream.html', id=id, title=stream_info['title'])
    else:
        abort(404, description=f"stream ID {stream_id} not found in the basketball list.")

if __name__ == '__main__':
    app.run(debug=True)
