from flask import Flask, render_template, abort, jsonify
from api.scoreboard_data import get_scoreboard_data
from api.boxscore_data import get_single_game_boxscore
from datetime import date, datetime
from api.games_streams import get_basketball_games
import time
from utils.get_team_abbreves import team_colors, nba_logo_code, abv
from db_service import get_all_replays, get_supabase_client

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
        away_tricode = game.get("away_tricode", "ATL")
        home_tricode = game.get("home_tricode", "ATL")
        default_color = "#333333"

        game["away_color"] = team_colors.get(away_tricode, default_color)
        game["home_color"] = team_colors.get(home_tricode, default_color)
        game["away_logo"] = nba_logo_code.get(away_tricode, "1610612737")
        game["home_logo"] = nba_logo_code.get(home_tricode, "1610612737")
    # ----------------

    scoreboard_data_teams = [game["teams"] for game in games_list]
    scoreboard_data = get_scoreboard_data(scoreboard_data_teams)

    return render_template('index.html', games=games_list, sb_data=scoreboard_data)

@app.route('/stream/<stream_id>')
def stream_viewer(stream_id):
    games_list = get_game_list_from_cache_or_api()

    BASKETBALL_STREAMS = {stream['id']: stream for stream in games_list}

    stream_info = BASKETBALL_STREAMS.get(stream_id)

    if stream_info:
        scoreboard_data_raw = get_scoreboard_data([stream_info['teams']])
        game_id_nba = scoreboard_data_raw.get(stream_info.get("teams")).get("game_id")

        if not stream_info.get('streams'):
            abort(404, description="Stream found, but embed URL list is missing.")

        return render_template('stream.html',
                               stream_info=stream_info,
                               title=stream_info['title'],
                               game_id_nba=game_id_nba,
                               teams=stream_info['teams'])
    else:
        abort(404, description=f"stream ID {stream_id} not found in the basketball list.")


@app.route('/replays')
def replays_index():
    raw_replays = get_all_replays()

    grouped_replays = {}
    ordered_display_dates = []

    for game in raw_replays:
        away_team_name = game["away_team"]
        home_team_name = game["home_team"]

        try:
            away_tricode = abv[away_team_name]
            home_tricode = abv[home_team_name]
            teams_tricode = away_tricode + home_tricode

            default_color = "#333333"
            game["away_color"] = team_colors.get(away_tricode, default_color)
            game["home_color"] = team_colors.get(home_tricode, default_color)
            game["away_logo"] = nba_logo_code[away_tricode]
            game["home_logo"] = nba_logo_code[home_tricode]
            game["teams"] = teams_tricode
            game["title"] = f"{away_team_name} vs. {home_team_name}"

        except KeyError:
            continue

        game_date_str = game["game_date"]
        try:
            dt_object = datetime.strptime(game_date_str, "%Y-%m-%d")
            display_date = dt_object.strftime("%B %d, %Y")
        except ValueError:
            display_date = game_date_str

        if display_date not in grouped_replays:
            grouped_replays[display_date] = []

        grouped_replays[display_date].append(game)

    unique_raw_dates = sorted(list(set(g['game_date'] for g in raw_replays)), reverse=True)
    for raw_date in unique_raw_dates:
        try:
            dt_object = datetime.strptime(raw_date, "%Y-%m-%d")
            ordered_display_dates.append(dt_object.strftime("%B %d, %Y"))
        except ValueError:
            ordered_display_dates.append(raw_date)

    return render_template('replays.html', grouped_replays=grouped_replays, ordered_dates=ordered_display_dates)


@app.route('/replay/<stream_id>')
def replay_stream_viewer(stream_id):
    supabase = get_supabase_client()
    try:
        response = supabase.table("nba_game_data_2025_26").select("iframe_url, away_team, home_team").eq("id", stream_id).limit(1).execute()
        db_game_info = response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching replay {stream_id} from DB: {e}")
        abort(500, description="Database error fetching replay data.")

    if db_game_info and db_game_info.get('iframe_url'):
        return render_template('replay_stream.html',
                               title=f"{db_game_info['away_team']} vs. {db_game_info['home_team']}",
                               replay_url=db_game_info['iframe_url'])
    else:
        abort(404, description=f"Replay ID {stream_id} not found or iframe link is still pending scrape.")

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


if __name__ == '__main__':
    _GAMES_LIST_CACHE_TIME = time.time()
    # app.run(host="0.0.0.0", debug=True)
    app.run(debug=True)
