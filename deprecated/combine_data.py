import requests
import json
from datetime import datetime, timedelta
import pytz

# --- MODIFIED IMPORTS ---
# from utils.get_team_abbreves import get_normalized_team_key, abv


def convert_ms_to_yyyymmdd(ms_timestamp, timezone_str='US/Central'):
    """
    Converts a 13-digit millisecond Unix timestamp to a YYYY-MM-DD string
    in the specified timezone.
    """
    try:
        ms_timestamp = float(ms_timestamp)
        s_timestamp = ms_timestamp / 1000

        dt_naive_utc = datetime.utcfromtimestamp(s_timestamp)
        dt_aware_utc = pytz.utc.localize(dt_naive_utc)

        target_timezone = pytz.timezone(timezone_str)
        dt_target = dt_aware_utc.astimezone(target_timezone)

        # Return in YYYY-MM-DD format
        return dt_target.strftime('%Y-%m-%d')

    except (ValueError, TypeError, OSError):
        return None

def get_normalized_team_key(title_str: str):
    """
    Finds the two competing teams from a title string, regardless of format.

    Returns a tuple containing:
    1. The normalized key (e.g., "BOSLAL")
    2. The "standard" title (e.g., "Boston Celtics vs. LA Lakers")
    3. The first team tricode found (e.g., "BOS"), used as "away"
    4. The second team tricode found (e.g., "LAL"), used as "home"
    """

    # Sort team names by length (longest first) to correctly match
    # "LA Clippers" before "LA Lakers" or "LA"
    sorted_team_names = sorted(abv.keys(), key=len, reverse=True)

    found_teams = [] # Will store ('BOS', 'Boston Celtics')

    for team_name in sorted_team_names:
        if team_name in title_str:
            tricode = abv[team_name]
            # Add the tricode and full name if not already found
            if not any(t[0] == tricode for t in found_teams):
                found_teams.append((tricode, team_name))

            # Stop once we have two teams
            if len(found_teams) == 2:
                break

    if len(found_teams) == 2:
        # We have a match
        team_1_tricode, team_1_name = found_teams[0]
        team_2_tricode, team_2_name = found_teams[1]

        # Create a stable, sorted key
        sorted_key = "".join(sorted([team_1_tricode, team_2_tricode]))

        # Create a standard title
        # We guess away/home based on which appeared first in the title
        if title_str.find(team_1_name) < title_str.find(team_2_name):
            away_tricode, home_tricode = team_1_tricode, team_2_tricode
            standard_title = f"{team_1_name} vs. {team_2_name}"
        else:
            away_tricode, home_tricode = team_2_tricode, team_1_tricode
            standard_title = f"{team_2_name} vs. {team_1_name}"

        return sorted_key, standard_title, away_tricode, home_tricode

    return None, None, None, None

# from utils.time_conversions import format_et_to_cst_status, convert_ms_to_yyyymmdd

def format_et_to_cst_status(et_datetime_str: str) -> str:

    et_tz = pytz.timezone('America/New_York')
    cst_tz = pytz.timezone('America/Chicago')
    input_format_24hr = '%Y-%m-%d %H:%M'
    output_format_12hr = '%l:%M %p' # e.g., 09:00 PM

    try:
        # 1. Parse and localize the input time as ET
        dt_et_naive = datetime.strptime(et_datetime_str, input_format_24hr)
        dt_et = et_tz.localize(dt_et_naive)

        # 2. Convert to CST
        dt_cst = dt_et.astimezone(cst_tz)

        # 3. Get the current date in CST for comparison
        # (Current time is Tuesday, November 4, 2025 at 12:48:19 PM CST)
        now_cst = datetime.now(cst_tz)
        today_date = now_cst.date()
        target_date = dt_cst.date()

        # 4. Determine status and format time
        cst_time_12hr = dt_cst.strftime(output_format_12hr)

        if target_date == today_date:
            date_status = 'Today'
        elif target_date == (today_date + timedelta(days=1)):
            date_status = 'Tomorrow'
        else:
            # If neither, return the full date (YYYY-MM-DD)
            date_status = target_date.strftime('%Y-%m-%d')

        # 5. Return the final formatted string
        return f"{date_status} @ {cst_time_12hr}"

    except ValueError:
        return "Error: Invalid datetime format. Please use 'YYYY-MM-DD HH:MM'."
    except pytz.exceptions.UnknownTimeZoneError:
        return "Error: Time zone configuration issue."


def convert_ms_timestamp_to_12hr(ms_timestamp):
    """
    Converts a 13-digit millisecond Unix timestamp to a formatted 12-hour
    string (YYYY MM DD HH:MM AM/PM) in the US/Central timezone (CST/CDT).

    :param ms_timestamp: The 13-digit timestamp (e.g., 1763155800000).
    :return: A formatted time string in US/Central time.
    """
    try:
        # Convert timestamp from string or int to a number
        ms_timestamp = float(ms_timestamp)

        # Convert from milliseconds to seconds
        s_timestamp = ms_timestamp / 1000

        # 1. Create a naive datetime object from the timestamp in UTC
        dt_naive_utc = datetime.datetime.utcfromtimestamp(s_timestamp)

        # 2. Localize the naive object to make it timezone-aware (aware of itself as UTC)
        dt_aware_utc = pytz.utc.localize(dt_naive_utc)

        # 3. Convert to the target timezone
        try:
            target_timezone = pytz.timezone('US/Central')
            dt_target_original = dt_aware_utc.astimezone(target_timezone)

            dt_target = dt_target_original + datetime.timedelta(hours=1)
            return dt_target.strftime('%Y %m %d %I:%M %p')

        except pytz.exceptions.UnknownTimeZoneError:
            return "Error: Could not load US/Central timezone"

    except (ValueError, TypeError, OSError):
        return "Error: Invalid timestamp provided"



# ------------------------

def get_basketball_games_source_1():
    """Fetches from Lotus.xyz and returns a dict keyed by 'YYYY-MM-DD_TEAMKEY'"""
    API_URL = "https://lotusgamehd.xyz/api-event.php?league=nba"
    games_dict = {}

    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        for day in data.get("days", []):
            for game in day.get("items", []):

                # 1. Get normalized team key
                team_key, title, away, home = get_normalized_team_key(game["title"])
                if not team_key:
                    continue

                # 2. Get normalized date key
                try:
                    date_str = datetime.strptime(game["when_et"], "%Y-%m-%d %H:%M").strftime("%Y-%m-%d")
                except ValueError:
                    continue

                game_key = f"{date_str}_{team_key}"
                print(game_key)

                # 3. Create stream object
                game_id = int(game["hds"][0])
                stream_url = f"https://lotusgamehd.xyz/lotushd.php?hd={game_id}"

                game_data = {
                    "id": game_key,
                    "title": title,
                    "game_start": format_et_to_cst_status(game["when_et"]),
                    "status": f"🔴 {game['status']}" if game["status"] == "LIVE" else game["status"],
                    "teams": team_key, # e.g., BOSLAL
                    "away_tricode": away,
                    "home_tricode": home,
                    "streams": [stream_url] # Store stream in a list
                }
                games_dict[game_key] = game_data

    except Exception as e:
        print(f"An unexpected error occurred in source 1: {e}")

    return games_dict

def get_basketball_games_source_2():
    """Fetches from Streamed.pk and returns a dict keyed by 'YYYY-MM-DD_TEAMKEY'"""
    API_URL = "https://streamed.pk/api/matches/basketball"
    games_dict = {}


    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        for game in data:
            # if sorted_team_names not in game.get('title', ''):
            #     continue

            # 1. Get normalized team key
            team_key, title, away, home = get_normalized_team_key(game["title"])
            if not team_key:
                continue

            # 2. Get normalized date key
            date_str = convert_ms_to_yyyymmdd(game["date"])
            if not date_str:
                continue

            game_key = f"{date_str}_{team_key}"
            print(game_key)

            # 3. Create stream objects
            streams_list = []
            for source in game.get("sources", []):
                if source.get("id"):
                    stream_url = f"https://embedsports.top/embed/{source['source']}/{source['id']}/1"
                    streams_list.append(stream_url)

            if not streams_list: # Skip game if no valid sources
                continue

            game_data = {
                "id": game_key,
                "title": title,
                "game_start": format_et_to_cst_status(game["when_et"]) if "when_et" in game else "TBD", # S2 API doesn't have this, use S1's if merged
                "status": game.get("status", "Scheduled"),
                "teams": team_key,
                "away_tricode": away,
                "home_tricode": home,
                "streams": streams_list # Store streams in a list
            }
            games_dict[game_key] = game_data

    except Exception as e:
        print(f"An unexpected error occurred in source 2: {e}")

    return games_dict

# --- Main function that combines both ---
def get_basketball_games():
    print("Fetching games from Source 1 (Lotus)...")
    games_s1_dict = get_basketball_games_source_1()
    print("Fetching games from Source 2 (Streamed.pk)...")
    games_s2_dict = get_basketball_games_source_2()

    # This is our final merged dictionary
    merged_games = {}

    # 1. Add all games from Source 1
    merged_games.update(games_s1_dict)

    # 2. Merge in games from Source 2
    for game_key, game_s2 in games_s2_dict.items():
        if game_key in merged_games:
            # GAME ALREADY EXISTS! Append streams.
            merged_games[game_key]["streams"].extend(game_s2["streams"])
        else:
            # This is a new game, just add it
            merged_games[game_key] = game_s2

    # Return the merged games as a list
    return list(merged_games.values())

print(get_basketball_games())
