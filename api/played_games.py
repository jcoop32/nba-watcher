import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
import calendar

def create_slug(name):
    return name.lower().replace(' ', '-')

def scrape_nba_schedule():
    """
    Scrapes the 2025-26 NBA schedule and results month-by-month from
    Basketball-Reference.com, dynamically stopping at the day before the
    current date.

    Returns:
        A JSON string containing the list of games and scores.
    """

    # 1. Configuration and Dynamic Date Setup
    SEASON_START_YEAR = 2025
    SEASON_START_MONTH = 10  # NBA season starts in October
    BASE_URL = "https://www.basketball-reference.com/leagues/NBA_2026_games-"

    # Calculate the dynamic end date (day before today)
    end_date_limit = date.today() - timedelta(days=1)
    END_DATE_STRING = end_date_limit.strftime("%Y-%m-%d")

    games_list = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # print(f"--- Fetching NBA 2025-26 Schedule up to {END_DATE_STRING} month-by-month ---")

    # 2. Generate a list of (year, month) tuples to iterate through
    current_year = SEASON_START_YEAR
    current_month = SEASON_START_MONTH

    months_to_scrape = []

    # Loop from the season start until we hit the current month
    while current_year < end_date_limit.year or (current_year == end_date_limit.year and current_month <= end_date_limit.month):
        months_to_scrape.append((current_year, current_month))

        if current_month == 12:
            current_month = 1
            current_year += 1
        else:
            current_month += 1

    # 3. Loop through the required months and scrape
    for year, month in months_to_scrape:
        month_name = calendar.month_name[month].lower()

        # Construct the month-specific URL
        url = f"{BASE_URL}{month_name}.html"
        # print(f"Fetching data for {month_name.capitalize()} {year} from: {url}")

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Continue to the next month if this one fails, but log the error
            # print(f"WARNING: Failed to fetch {month_name.capitalize()} schedule: {e}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        schedule_table = soup.find('table', {'id': 'schedule'})

        if not schedule_table:
            # print(f"WARNING: Could not find the schedule table for {month_name.capitalize()}.")
            continue

        # Iterate through all table rows, skipping the header row
        for row in schedule_table.find_all('tr')[1:]:
            cols = row.find_all(['td', 'th'])

            if len(cols) < 7:
                continue

            try:
                date_str = cols[0].text.strip()
                # Parse the full datetime object
                game_date_dt = datetime.strptime(date_str, "%a, %b %d, %Y")
                game_date = game_date_dt.date()

                # Final check to respect the dynamic limit
                if game_date > end_date_limit:
                    # Since the table is chronological, we can stop scraping this month's table now
                    break

                # Data extraction:
                away_team = cols[2].text.strip()
                away_score_str = cols[3].text.strip()
                away_score = int(away_score_str) if away_score_str.isdigit() else None

                home_team = cols[4].text.strip()
                home_score_str = cols[5].text.strip()
                home_score = int(home_score_str) if home_score_str.isdigit() else None

                notes = cols[7].text.strip() if len(cols) > 7 else ""

                # --- REPLAY URL LOGIC with unpadded day ---
                # 1. Create slugs for team names
                away_slug = create_slug(away_team)
                home_slug = create_slug(home_team)

                # 2. Format the date for the URL: month-day-year (e.g., november-5-2025)
                # Use .day for unpadded day number.
                month_name_slug = game_date_dt.strftime("%B").lower()
                day_number = game_date_dt.day
                year_number = game_date_dt.year

                date_slug = f"{month_name_slug}-{day_number}-{year_number}"

                # 3. Construct the final replay_url string
                replay_url_str = f"{away_slug}-vs-{home_slug}-full-game-replay-{date_slug}-nba"
                # ----------------------------------------

                game_data = {
                    "game_date": game_date.strftime("%Y-%m-%d"),
                    "replay_url": replay_url_str,
                    "away_team": away_team,
                    "away_score": away_score,
                    "home_team": home_team,
                    "home_score": home_score,
                    "notes": notes,
                    "iframe_url": None
                }

                games_list.append(game_data)

            except (ValueError, IndexError, TypeError) as e:
                # print(f"Skipping row due to error: {e} in month {month_name}")
                continue

    return games_list

