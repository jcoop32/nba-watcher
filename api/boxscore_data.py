import requests
from nba_api.stats.endpoints import BoxScoreTraditionalV2
import time

_BOXSCORE_CACHE = {}
BOXSCORE_CACHE_TIMEOUT = 10  # Seconds to cache individual box scores

def get_single_game_boxscore(game_id: str):
    global _BOXSCORE_CACHE

    # 1. Check Cache
    if game_id in _BOXSCORE_CACHE and time.time() - _BOXSCORE_CACHE[game_id]['timestamp'] < BOXSCORE_CACHE_TIMEOUT:
        return _BOXSCORE_CACHE[game_id]['data']

    # 2. Fetch Fresh Data
    try:
        # Fetch Traditional Box Score
        boxscore = BoxScoreTraditionalV2(game_id=game_id).get_dict()

        # Extract Player Stats and Game Info
        player_stats_list = boxscore.get('resultSets', [])[0].get('rowSet', [])

        # This is a fixed column list based on the NBA API response structure
        columns = [
            "PLAYER_ID", "PLAYER_NAME", "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT",
            "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS",
            "TEAM_ID", "TEAM_ABBREVIATION"
        ]

        # Restructure data into a more readable format keyed by team
        processed_data = {}

        for player_stats in player_stats_list:
            player_data = dict(zip(columns, player_stats))
            team_tricode = player_data['TEAM_ABBREVIATION']

            # Format minutes (MIN)
            minutes = player_data.get('MIN')
            if minutes is not None:
                # Convert decimal minutes (e.g., 30.5) to M:SS format
                min_int = int(minutes)
                sec_frac = int((minutes - min_int) * 60)
                player_data['MIN'] = f"{min_int}:{sec_frac:02}"
            else:
                 player_data['MIN'] = ""

            if team_tricode not in processed_data:
                processed_data[team_tricode] = {
                    'players': [],
                    'team_total': None
                }

            # Use only necessary fields for display
            processed_data[team_tricode]['players'].append({
                'name': player_data['PLAYER_NAME'],
                'min': player_data['MIN'],
                'pts': player_data['PTS'],
                'reb': player_data['REB'],
                'ast': player_data['AST'],
                'stl': player_data['STL'],
                'blk': player_data['BLK'],
                'to': player_data['TO'],
                'fgm_fga': f"{player_data['FGM']}/{player_data['FGA']}",
                'fg3m_fg3a': f"{player_data['FG3M']}/{player_data['FG3A']}",
            })

        # 3. Update Cache
        _BOXSCORE_CACHE[game_id] = {
            'data': processed_data,
            'timestamp': time.time()
        }

        return processed_data

    except requests.exceptions.RequestException:
        return {"error": "API request failed for Box Score."}
    except Exception as e:
        return {"error": f"Error processing box score data: {e}"}
