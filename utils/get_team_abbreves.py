def extract_teams_from_game_title(game_title):
    # 1. Split the string using the separator ' vs. '
    parts = game_title.split(' vs. ')

    if len(parts) < 2:
        return "N/A", "N/A" # Handle unexpected format

    # 2. Away Team is the first part (and should be clean)
    away_team = parts[0].strip()

    # 3. Home Team is the second part, which needs cleaning
    home_team_raw = parts[1].strip()

    # Find the index of the first parenthesis '('
    parenthesis_start = home_team_raw.find('(')

    if parenthesis_start != -1:
        # If parenthesis is found, slice the string to keep only the part before it
        home_team = home_team_raw[:parenthesis_start].strip()
    else:
        # If no parenthesis is found, use the raw string (it's already clean)
        home_team = home_team_raw

    return away_team, home_team
