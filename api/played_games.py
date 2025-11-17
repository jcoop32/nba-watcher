from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
import calendar
import time

def create_slug(name):
    return name.lower().replace(' ', '-')

def scrape_nba_schedule():
    """
    Scrapes the 2025-26 NBA schedule using Playwright with resource blocking
    and robust retry logic to handle bot checks.
    """
    SEASON_START_YEAR = 2025
    SEASON_START_MONTH = 10
    BASE_URL = "https://www.basketball-reference.com/leagues/NBA_2026_games-"
    end_date_limit = date.today() - timedelta(days=1)

    games_list = []

    current_year = SEASON_START_YEAR
    current_month = SEASON_START_MONTH
    months_to_scrape = []

    while current_year < end_date_limit.year or (current_year == end_date_limit.year and current_month <= end_date_limit.month):
        months_to_scrape.append((current_year, current_month))
        if current_month == 12:
            current_month = 1
            current_year += 1
        else:
            current_month += 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        context.route("**/*", lambda route: route.abort()
            if route.request.resource_type in ["image", "media", "font", "stylesheet", "other"]
            else route.continue_()
        )

        page = context.new_page()

        for year, month in months_to_scrape:
            month_name = calendar.month_name[month].lower()
            url = f"{BASE_URL}{month_name}.html"

            print(f"Fetching {month_name.capitalize()} {year}...")

            success = False
            attempts = 0
            max_attempts = 3

            while not success and attempts < max_attempts:
                attempts += 1
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)

                    try:
                        page.wait_for_selector('#schedule', state='attached', timeout=10000)
                        success = True
                    except Exception:
                        print(f"  Attempt {attempts}/{max_attempts}: Table not found. Page title: '{page.title()}'")
                        if attempts < max_attempts:
                            time.sleep(2)
                            print("  Retrying...")
                        else:
                            print(f"❌ Failed to find schedule for {month_name} after {max_attempts} attempts.")

                except Exception as e:
                    print(f"  Attempt {attempts}/{max_attempts} error: {e}")

            if not success:
                continue
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            schedule_table = soup.find('table', {'id': 'schedule'})

            if not schedule_table:
                continue

            for row in schedule_table.find_all('tr')[1:]:
                cols = row.find_all(['td', 'th'])
                if len(cols) < 7: continue

                try:
                    date_str = cols[0].text.strip()
                    try:
                        game_date_dt = datetime.strptime(date_str, "%a, %b %d, %Y")
                    except ValueError:
                        continue

                    game_date = game_date_dt.date()
                    if game_date > end_date_limit: break

                    away_team = cols[2].text.strip()
                    away_score_str = cols[3].text.strip()
                    away_score = int(away_score_str) if away_score_str.isdigit() else None

                    home_team = cols[4].text.strip()
                    home_score_str = cols[5].text.strip()
                    home_score = int(home_score_str) if home_score_str.isdigit() else None

                    notes = cols[7].text.strip() if len(cols) > 7 else ""

                    if home_team == "Los Angeles Clippers": home_team = "LA Clippers"
                    if away_team == "Los Angeles Clippers": away_team = "LA Clippers"

                    away_slug = create_slug(away_team)
                    home_slug = create_slug(home_team)
                    month_name_slug = game_date_dt.strftime("%B").lower()
                    date_slug = f"{month_name_slug}-{game_date_dt.day}-{game_date_dt.year}"
                    replay_url_str = f"{away_slug}-vs-{home_slug}-full-game-replay-{date_slug}-nba"

                    games_list.append({
                        "game_date": game_date.strftime("%Y-%m-%d"),
                        "replay_url": replay_url_str,
                        "away_team": away_team,
                        "away_score": away_score,
                        "home_team": home_team,
                        "home_score": home_score,
                        "notes": notes,
                        "iframe_url": None
                    })

                except (ValueError, IndexError, TypeError):
                    continue

            time.sleep(1)

        browser.close()

    return games_list
