from nba_api.live.nba.endpoints import playbyplay
from services.redis_service import get_cache, set_cache
import json

CACHE_TIMEOUT = 60

def get_momentum_data(game_id):
    """
    Fetches play-by-play data using nba_api (Live Endpoint).

    FIX: Manually detects score changes instead of relying on 'isScoreChange' flag.
    """
    if not game_id:
        return []

    cache_key = f"momentum:{game_id}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data

    try:
        pbp = playbyplay.PlayByPlay(game_id=game_id)
        data = pbp.get_dict()

        actions = data.get('game', {}).get('actions', [])

        # print(f"[Momentum] Game {game_id}: Found {len(actions)} total actions.")

        chart_data = []
        chart_data.append({'label': 'Start', 'value': 0, 'period': 1})

        # Track the score from the previous loop
        last_home = 0
        last_away = 0
        score_updates_found = 0

        for action in actions:
            try:
                # Safely extract scores, defaulting to the previous known score if missing
                raw_home = action.get('scoreHome')
                raw_away = action.get('scoreAway')

                curr_home = int(float(raw_home)) if raw_home is not None else last_home
                curr_away = int(float(raw_away)) if raw_away is not None else last_away

                # --- MANUAL CHECK: Did the score change ---
                if curr_home != last_home or curr_away != last_away:

                    # Update our tracker
                    last_home = curr_home
                    last_away = curr_away

                    # Format Clock
                    period = action.get('period', 0)
                    clock = action.get('clock', '')

                    if clock:
                        time_str = clock.replace('PT', '').replace('.00S', '').replace('M', ':')
                        if 'S' in time_str: time_str = time_str.replace('S', '')
                    else:
                        time_str = "00:00"

                    chart_data.append({
                        'label': f"Q{period} {time_str}",
                        'value': curr_home - curr_away,
                        'period': period
                    })
                    score_updates_found += 1

            except (ValueError, TypeError) as e:
                continue


        set_cache(cache_key, chart_data, CACHE_TIMEOUT)
        return chart_data

    except Exception as e:
        print(f"[Momentum] Error for {game_id}: {e}")
        return []
