from nba_api.stats.endpoints import leaguedashplayerstats
from services.redis_service import get_cache, set_cache

PLAYER_STATS_CACHE_KEY = "nba_player_season_stats_2025_26"
CACHE_DURATION = 86400  # 24 Hours

def update_league_player_stats():
    """
    Fetches stats for ALL players in the league for the current season.
    Stores them in Redis as a dictionary keyed by Player ID.
    Uses get_dict() to avoid pandas dependency.
    """
    try:
        stats_endpoint = leaguedashplayerstats.LeagueDashPlayerStats(
            season='2025-26',
            per_mode_detailed='PerGame',
            season_type_all_star='Regular Season'
        )

        # Use get_dict() instead of get_data_frames()
        data = stats_endpoint.get_dict()
        result_set = data['resultSets'][0]
        headers = result_set['headers']
        row_set = result_set['rowSet']

        # Map header names to indices for safe lookup
        h = {name: i for i, name in enumerate(headers)}

        stats_dict = {}
        for row in row_set:
            pid = str(row[h['PLAYER_ID']])
            stats_dict[pid] = {
                'gp': row[h['GP']],
                'pts': round(row[h['PTS']], 1),
                'reb': round(row[h['REB']], 1),
                'ast': round(row[h['AST']], 1),
                'stl': round(row[h['STL']], 1),
                'blk': round(row[h['BLK']], 1),
                'fg_pct': round(row[h['FG_PCT']] * 100, 1),
                'fg3_pct': round(row[h['FG3_PCT']] * 100, 1),
                'fg3a': round(row[h['FG3A']], 1),
                'ft_pct': round(row[h['FT_PCT']] * 100, 1),
            }

        set_cache(PLAYER_STATS_CACHE_KEY, stats_dict, CACHE_DURATION)
        return stats_dict

    except Exception as e:
        print(f"[Player Stats] Error fetching league stats: {e}")
        return {}

def get_player_season_stats(player_id):
    """
    Retrieves stats for a single player from the Redis cache.
    If cache is empty, it triggers an update.
    """
    stats_map = get_cache(PLAYER_STATS_CACHE_KEY)

    if not stats_map:
        stats_map = update_league_player_stats()

    return stats_map.get(str(player_id), {})
