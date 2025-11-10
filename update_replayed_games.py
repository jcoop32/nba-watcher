from utils.get_iframe_urls import start_replay_scrape
from db_service import get_supabase_client, TABLE_NAME, bulk_upsert_game_data


def update_and_fetch_new_replay_games():
    supabase = get_supabase_client()
    print("Updating db with new games played...")
    bulk_upsert_game_data()
    print("\n--- Running Scraper ---")
    start_replay_scrape(supabase, TABLE_NAME)

update_and_fetch_new_replay_games()
