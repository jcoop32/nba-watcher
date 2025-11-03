abv = {
    # Atlantic Division
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BKN",
    "New York Knicks": "NYK",
    "Philadelphia 76ers": "PHI",
    "Toronto Raptors": "TOR",

    # Central Division
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Detroit Pistons": "DET",
    "Indiana Pacers": "IND",
    "Milwaukee Bucks": "MIL",

    # Southeast Division
    "Atlanta Hawks": "ATL",
    "Charlotte Hornets": "CHA",
    "Miami Heat": "MIA",
    "Orlando Magic": "ORL",
    "Washington Wizards": "WAS",

    # Northwest Division
    "Denver Nuggets": "DEN",
    "Minnesota Timberwolves": "MIN",
    "Oklahoma City Thunder": "OKC",
    "Portland Trail Blazers": "POR",
    "Utah Jazz": "UTA",

    # Pacific Division
    "Golden State Warriors": "GSW",
    "Los Angeles Clippers": "LAC",
    "LA Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "LA Lakers": "LAL",
    "Phoenix Suns": "PHX",
    "Sacramento Kings": "SAC",

    # Southwest Division
    "Dallas Mavericks": "DAL",
    "Houston Rockets": "HOU",
    "Memphis Grizzlies": "MEM",
    "New Orleans Pelicans": "NOP",
    "San Antonio Spurs": "SAS"
}

def extract_teams_from_game_title(game_title):
    # 1. Split the string using the separator ' vs. '
    parts = game_title.split(' - ')

    if len(parts) < 2:
        return "N/A", "N/A" # Handle unexpected format

    # 2. Away Team is the first part (and should be clean)
    away_team = parts[1].strip()

    # 3. Home Team is the second part, which needs cleaning
    home_team_raw = parts[0].strip()


    # Find the index of the first parenthesis '('
    parenthesis_start = home_team_raw.find('(')

    if parenthesis_start != -1:
        # If parenthesis is found, slice the string to keep only the part before it
        home_team = home_team_raw[:parenthesis_start].strip()
    else:
        # If no parenthesis is found, use the raw string (it's already clean)
        home_team = home_team_raw

    teams = abv[away_team] + abv[home_team]
    title = f"{away_team} vs. {home_team}"

    return title, teams
