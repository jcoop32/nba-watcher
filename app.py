from flask import Flask, render_template, abort
from flask_compress import Compress
from api.scoreboard_data import get_scoreboard_data
from api.boxscore_data import get_single_game_boxscore
from datetime import date, datetime
import time
import threading
from api.games_streams import get_basketball_games,  get_euro_basketball_games
from utils.get_team_abbreves import team_colors, nba_logo_code, abv
from services.db_service import get_all_replays, get_supabase_client
from services.redis_service import get_cache, set_cache
from utils.optimizations import jsonify_with_etag, OrJSONProvider

app = Flask(__name__)
Compress(app)

app.json = OrJSONProvider(app)

current_date = date.today().strftime("%Y-%m-%d")

GAMES_LIST_CACHE_TIMEOUT = 3600

def background_cache_worker():
    """
    Runs in the background to keep game data fresh.
    This prevents the UI from ever waiting on the slow external APIs.
    """
    while True:
        try:
            nba_games = get_basketball_games()
            if nba_games:
                set_cache("nba_games_list", nba_games, GAMES_LIST_CACHE_TIMEOUT)

            euro_games = get_euro_basketball_games()
            if euro_games:
                set_cache("euro_games_list", euro_games, GAMES_LIST_CACHE_TIMEOUT)

        except Exception as e:
            print(f"[Background Worker] ❌ Error updating cache: {e}")

        time.sleep(1800)

cache_thread = threading.Thread(target=background_cache_worker, daemon=True)
cache_thread.start()

def get_game_list_from_cache_or_api():
    cached_games = get_cache("nba_games_list")
    if cached_games:
        return cached_games

    raw_games_list = get_basketball_games()
    set_cache("nba_games_list", raw_games_list, GAMES_LIST_CACHE_TIMEOUT)

    return raw_games_list

def get_euro_games_from_cache_or_api():
    cached_games = get_cache("euro_games_list")
    if cached_games:
        return cached_games

    raw_games = get_euro_basketball_games()
    set_cache("euro_games_list", raw_games, 3600) # Cache for 1 hour
    return raw_games

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

    earliest_timestamp = 0
    if games_list:
        valid_timestamps = [g.get("start_timestamp", 0) for g in games_list if g.get("start_timestamp", 0) > 0]
        if valid_timestamps:
            earliest_timestamp = min(valid_timestamps)

    scoreboard_data_teams = [game["teams"] for game in games_list]
    scoreboard_data = get_scoreboard_data(scoreboard_data_teams)

    return render_template('index.html',
                           games=games_list,
                           sb_data=scoreboard_data,
                           earliest_timestamp=earliest_timestamp)


@app.route('/euro-league')
def euro_leagues():
    games_list = get_euro_games_from_cache_or_api()
    return render_template('euro_league_games.html', games=games_list)


@app.route('/stream/<stream_id>')
def stream_viewer(stream_id):
    # 1. Try Main NBA List
    games_list = get_game_list_from_cache_or_api()
    BASKETBALL_STREAMS = {stream['id']: stream for stream in games_list}
    stream_info = BASKETBALL_STREAMS.get(stream_id)

    game_id_nba = None
    game_started = False

    # 2. If not found, try Other Leagues List
    if not stream_info:
        other_games = get_euro_games_from_cache_or_api()
        OTHER_STREAMS = {stream['id']: stream for stream in other_games}
        stream_info = OTHER_STREAMS.get(stream_id)

    if stream_info:
        # Only try to get NBA scoreboard data if it looks like an NBA game (has specific teams key)
        if stream_info.get("teams") != "OTHER":
            scoreboard_data_raw = get_scoreboard_data([stream_info['teams']])
            if scoreboard_data_raw and stream_info.get("teams") in scoreboard_data_raw:
                game_data = scoreboard_data_raw.get(stream_info.get("teams"))
                game_id_nba = game_data.get("game_id")
                game_started = game_data.get("game_started_yet")

        if not stream_info.get('streams'):
            abort(404, description="Stream found, but embed URL list is missing.")

        return render_template('stream.html',
                               stream_info=stream_info,
                               title=stream_info['title'],
                               game_id_nba=game_id_nba, # Will be None for other leagues, disabling boxscore
                               teams=stream_info['teams'],
                               game_started=game_started
                               )
    else:
        abort(404, description=f"stream ID {stream_id} not found.")


@app.route('/replays')
def replays_index():
    cache_key = "replays_list_full"
    raw_replays = get_cache(cache_key)

    if not raw_replays:
        raw_replays = get_all_replays()
        if raw_replays:
             set_cache(cache_key, raw_replays, 43200) #12 hours
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

    return jsonify_with_etag(response_data, app)

@app.route('/api/boxscore/<game_id>')
def api_boxscore(game_id):
    boxscore_data = get_single_game_boxscore(game_id)
    return jsonify_with_etag(boxscore_data, app)

@app.route('/multi-view')
def multi_view():
    return render_template('multiview.html')

@app.route('/api/games-today')
def games_today():
    games = get_game_list_from_cache_or_api()
    return jsonify_with_etag(games, app)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
    # app.run(debug=True)
