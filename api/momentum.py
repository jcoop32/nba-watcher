from nba_api.live.nba.endpoints import playbyplay
from services.redis_service import get_cache, set_cache
import json

CACHE_TIMEOUT = 60

def get_momentum_data(game_id):
    """
    Fetches play-by-play data and samples the score differential
    roughly every 3 minutes (e.g. 12:00, 9:00, 6:00, 3:00).
    """
    if not game_id:
        return []

    cache_key = f"momentum_3min:{game_id}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data

    try:
        pbp = playbyplay.PlayByPlay(game_id=game_id)
        data = pbp.get_dict()
        actions = data.get('game', {}).get('actions', [])

        chart_data = []
        chart_data.append({'label': 'Start', 'value': 0, 'period': 1})

        last_home = 0
        last_away = 0

        # Track 3-minute buckets
        # Buckets for 12 min Q: 4=(12-9), 3=(9-6), 2=(6-3), 1=(3-0), 0=(<0)
        current_period = 0
        last_bucket = 5 # Start higher than any possible bucket (12min / 3 = 4)

        for action in actions:
            try:
                raw_home = action.get('scoreHome')
                raw_away = action.get('scoreAway')
                curr_home = int(float(raw_home)) if raw_home is not None else last_home
                curr_away = int(float(raw_away)) if raw_away is not None else last_away

                last_home = curr_home
                last_away = curr_away

                period = action.get('period', 0)
                clock = action.get('clock', '')

                # Reset bucket logic on new period
                if period != current_period:
                    current_period = period
                    last_bucket = 5 # Reset to start of quarter

                if clock:
                    time_str = clock.replace('PT', '').replace('.00S', '').replace('M', ':')
                    if 'S' in time_str: time_str = time_str.replace('S', '')

                    # Calculate seconds remaining to determine bucket
                    parts = time_str.split(':')
                    if len(parts) == 2:
                        minutes = int(parts[0])
                        seconds = int(parts[1])
                        total_seconds = minutes * 60 + seconds
                    else:
                        total_seconds = 0
                else:
                    time_str = "00:00"
                    total_seconds = 0

                current_bucket = total_seconds // 180

                # 4. Capture Data ONLY if we dropped into a new bucket
                if current_bucket < last_bucket:
                    chart_data.append({
                        'label': f"Q{period} {time_str}",
                        'value': curr_home - curr_away,
                        'period': period
                    })
                    last_bucket = current_bucket

            except (ValueError, TypeError):
                continue

        set_cache(cache_key, chart_data, CACHE_TIMEOUT)
        return chart_data

    except Exception as e:
        print(f"[Momentum] Error for {game_id}: {e}")
        return []
