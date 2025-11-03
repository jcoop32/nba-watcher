import requests
import re
import json
from utils.team_abbrv import nba_team_abbreviations as abv
from utils.get_team_abbreves import extract_teams_from_game_title

def get_nba_streams():
    # url = 'https://embedhd.io/'
    url = "https://lotusgamehd.xyz/api-event.php"
    # url = 'https://lotusgamehd.xyz/'
    try:
        # 1. Fetch the webpage content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return []

    html_content = response.text

    # 2. Extract the STREAMS JSON-like string
    match = re.search(r'const STREAMS = ({.*?});', html_content, re.DOTALL)

    if not match:
        print("Variable 'const STREAMS = {...}' not found on the page.")
        return []

    json_string = match.group(1)

    # 3. Fix and load the JSON
    json_string = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+):', r'\1"\2":', json_string)

    try:
        streams_dict = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Error decoding the JSON data: {e}. Cannot filter streams.")
        return []

    basketball_streams = []

    # 4. Filter for 'Basketball' league and structure the output
    for stream_id, data in streams_dict.items():
        if data.get('league') == 'Basketball':
            away_team, home_team = extract_teams_from_game_title(data["name"])
            basketball_streams.append({
                'title': data.get('name', 'N/A'),
                'id': stream_id,
                # "home_team": home_team,
                # "away_team": away_team,
                "teams": abv[away_team] + abv[home_team]
            })

    return basketball_streams


