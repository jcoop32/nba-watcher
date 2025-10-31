from datetime import datetime, timezone

def has_game_started(game_start_time_str):
    try:
        target_time = datetime.fromisoformat(game_start_time_str.replace('Z', '+00:00'))

        # 2. Get Current Time (Always use UTC for comparison)
        current_time_utc = datetime.now(timezone.utc)

        # 3. Compare Times
        # If the target time is GREATER than the current time, the game has NOT started.
        started_yet = target_time <= current_time_utc

        return started_yet

    except ValueError:
        # Handle cases where the time string is in an unexpected format
        print(f"Error: Could not parse time string '{game_start_time_str}'.")
        return False

