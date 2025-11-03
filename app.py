from flask import Flask, render_template, abort, jsonify
from api.scoreboard_data import get_scoreboard_data
from datetime import date
from api.games_streams import get_basketball_games

current_date = date.today().strftime("%Y-%m-%d")

app = Flask(__name__)

# Global list of games is necessary to keep track of streams for the viewer route
RAW_GAMES_LIST = []

def get_game_list_from_cache_or_api():
    global RAW_GAMES_LIST
    if not RAW_GAMES_LIST:
        RAW_GAMES_LIST = get_basketball_games()
    return RAW_GAMES_LIST

@app.route('/')
def index():
    games_list = get_game_list_from_cache_or_api()

    scoreboard_data_teams = [game["teams"] for game in games_list]

    scoreboard_data = get_scoreboard_data(scoreboard_data_teams)
    return render_template('index.html', games=games_list, sb_data=scoreboard_data)

# NEW ROUTE FOR AJAX POLLING
@app.route('/api/scoreboard')
def api_scoreboard():
    # EFFICIENCY FIX: Rely on the global list populated by the index page.
    # We DO NOT call the stream API (get_basketball_games) again here.
    games_list = get_game_list_from_cache_or_api()

    # Only fetch scoreboard data (nba_api), which is necessary for live updates.
    scoreboard_data_teams = [game["teams"] for game in games_list]

    scoreboard_data = get_scoreboard_data(scoreboard_data_teams)

    # Format the data to be easily consumable by the frontend
    response_data = {}
    for game in games_list:
        teams_key = game["teams"]
        if teams_key in scoreboard_data:
            response_data[teams_key] = scoreboard_data[teams_key]

    return jsonify(response_data)


@app.route('/watch/<stream_id>')
def iframe_viewer(stream_id):
    games_list = get_game_list_from_cache_or_api()

    BASKETBALL_STREAMS = {stream['id']: stream for stream in games_list}
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
