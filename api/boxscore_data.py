import requests
from utils.time_conversions import convert_iso_minutes
from utils.redis_service import get_cache, set_cache

BOXSCORE_CACHE_TIMEOUT = 15
BOXSCORE_URL_TEMPLATE = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"

# DEFINE BROWSER HEADERS to prevent 403 errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

def _process_player_stats(player_data):
    """Formats raw player data for display based on the provided JSON structure."""
    stats = player_data.get('statistics', {})

    # Parse complex minutes string
    minutes_iso = stats.get('minutes', "")
    minutes_formatted = convert_iso_minutes(minutes_iso)

    # Return a structured dict of the required fields
    return {
        'name': player_data.get('name', ''),
        'min': minutes_formatted,
        'pts': stats.get('points', 0),
        'reb': stats.get('reboundsTotal', 0),
        'ast': stats.get('assists', 0),
        'stl': stats.get('steals', 0),
        'blk': stats.get('blocks', 0),
        'to': stats.get('turnovers', 0),
        # Convert FGM/FGA and 3PTM/3PTA into display strings
        'fgm_fga': f"{stats.get('fieldGoalsMade', 0)}/{stats.get('fieldGoalsAttempted', 0)}",
        'fg3m_fg3a': f"{stats.get('threePointersMade', 0)}/{stats.get('threePointersAttempted', 0)}",
        # NEW FIELDS FOR INDICATORS
        'is_starter': player_data.get('starter') == '1',
        'is_oncourt': player_data.get('oncourt') == '1',
    }


def get_single_game_boxscore(game_id: str):
    """
    Fetches the box score for a specific game ID.
    Checks Redis cache first; otherwise fetches from NBA CDN.
    """

    # 1. Check Redis Cache
    cache_key = f"boxscore:{game_id}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data

    # 2. Fetch Fresh Data
    url = BOXSCORE_URL_TEMPLATE.format(game_id=game_id)

    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        boxscore = response.json()

        # 3. Parse Data
        game_data = boxscore.get('game', {})
        home_team = game_data.get('homeTeam', {})
        away_team = game_data.get('awayTeam', {})

        processed_data = {}

        # Helper to process team and filter for players who have played
        def process_team(team_data):
            tricode = team_data.get('teamTricode')
            if not tricode:
                return

            # Filter players who have played (status='ACTIVE' and played='1')
            active_players = [
                _process_player_stats(p) for p in team_data.get('players', [])
                if p.get('status') == 'ACTIVE' and p.get('played') == '1'
            ]

            # Helper function to convert M:SS format to seconds for reliable sorting
            def time_to_seconds(time_str):
                try:
                    m, s = map(int, time_str.split(':'))
                    return m * 60 + s
                except ValueError:
                    return 0

            # Sort players by minutes (MIN) descending
            active_players.sort(key=lambda p: time_to_seconds(p['min']), reverse=True)

            processed_data[tricode] = { 'players': active_players }

        process_team(home_team)
        process_team(away_team)

        # 4. Update Redis Cache
        set_cache(cache_key, processed_data, BOXSCORE_CACHE_TIMEOUT)

        return processed_data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
             return {"error": "Box score not found (Game ID may be incorrect or game not yet live)."}
        return {"error": f"HTTP Error fetching box score: {e.response.status_code}"}
    except Exception as e:
        return {"error": f"Error processing box score data: {e.__class__.__name__}"}
