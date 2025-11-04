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

team_colors = {
    "ATL": "#C8102E",           # Atlanta Hawks: Torch Red
    "BOS": "#007A33",           # Boston Celtics: Celtic Green
    "BKN": "#000000",           # Brooklyn Nets: White (Primary contrast for dark mode)
    "CHA": "#1D1160",           # Charlotte Hornets: Dark Purple
    "CHI": "#BA0C2F",           # Chicago Bulls: Red
    "CLE": "#6F263D",           # Cleveland Cavaliers: Wine
    "DAL": "#0053BC",           # Dallas Mavericks: Royal Blue
    "DEN": "#0E2240",           # Denver Nuggets: Midnight Blue
    "DET": "#1D428A",           # Detroit Pistons: Royal Blue
    "GSW": "#006BB6",           # Golden State Warriors: Royal Blue
    "HOU": "#CE1141",           # Houston Rockets: Red
    "IND": "#002D62",           # Indiana Pacers: Navy Blue
    "LAC": "#0C2340",           # Los Angeles Clippers: Navy Blue
    "LAL": "#552583",           # Los Angeles Lakers: Purple
    "MEM": "#5D76A9",           # Memphis Grizzlies: Grizzlies Blue
    "MIA": "#98002E",           # Miami Heat: Heat Red
    "MIL": "#00471B",           # Milwaukee Bucks: Good Land Green
    "MIN": "#0C2340",           # Minnesota Timberwolves: Midnight Blue
    "NOP": "#002B5C",           # New Orleans Pelicans: Navy Blue
    "NYK": "#006BB6",           # New York Knicks: Blue
    "OKC": "#007AC1",           # Oklahoma City Thunder: Thunder Blue
    "ORL": "#0077C0",           # Orlando Magic: Blue
    "PHI": "#006BB6",           # Philadelphia 76ers: Blue
    "PHX": "#1D1160",           # Phoenix Suns: Purple
    "POR": "#E03A3E",           # Portland Trail Blazers: Red
    "SAC": "#5A2D81",           # Sacramento Kings: Purple
    "SAS": "#C4CED4",           # San Antonio Spurs: Silver
    "TOR": "#CE1141",           # Toronto Raptors: Red
    "UTA": "#002B5C",           # Utah Jazz: Navy Blue
    "WAS": "#C8102E"            # Washington Wizards: Navy Blue
}

nba_logo_code = {
    "ATL": "1610612737",
    "BOS": "1610612738",
    "BKN": "1610612751",
    "CHA": "1610612766",
    "CHI": "1610612741",
    "CLE": "1610612739",
    "DAL": "1610612742",
    "DEN": "1610612743",
    "DET": "1610612765",
    "GSW": "1610612744",
    "HOU": "1610612745",
    "IND": "1610612754",
    "LAC": "1610612746",
    "LAL": "1610612747",
    "MEM": "1610612763",
    "MIA": "1610612748",
    "MIL": "1610612749",
    "MIN": "1610612750",
    "NOP": "1610612740",
    "NYK": "1610612752",
    "OKC": "1610612760",
    "ORL": "1610612753",
    "PHI": "1610612755",
    "PHX": "1610612756",
    "POR": "1610612757",
    "SAC": "1610612758",
    "SAS": "1610612759",
    "TOR": "1610612761",
    "UTA": "1610612762",
    "WAS": "1610612764"

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
