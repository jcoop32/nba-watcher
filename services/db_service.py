import os
from dotenv import load_dotenv
from supabase import create_client, Client
from api.played_games import scrape_nba_schedule
from services.redis_service import get_cache, set_cache

load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")
TABLE_NAME = "nba_game_data_2025_26"

_supabase_client = None
def get_supabase_client() -> Client:
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
             raise ValueError("Supabase URL or Key is missing.")

        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _supabase_client
    except Exception as e:
        raise Exception(f"Failed to initialize Supabase client: {e}")


def bulk_upsert_game_data():
    try:
        supabase = get_supabase_client()
    except Exception as e:
        print(f"❌ Aborting bulk upsert due to DB connection failure: {e}")
        return

    data_list = scrape_nba_schedule()

    if not data_list:
        print("No schedule data scraped for upsert. Exiting.")
        return

    num_rows = len(data_list)
    conflict_cols = "replay_url"

    print(f"\n--- Starting SELECTIVE Bulk UPSERT for {num_rows} schedule records ---")
    column_to_preserve = "iframe_url"

    data_list_for_upsert = []
    for record in data_list:
        record_copy = record.copy()
        if column_to_preserve in record_copy:
            del record_copy[column_to_preserve]
        data_list_for_upsert.append(record_copy)
    try:
        response = (
            supabase.table(TABLE_NAME)
            .upsert(data_list_for_upsert, on_conflict=conflict_cols)
            .execute()
        )

        inserted_data = response.data

        if inserted_data:
            print(f"✅ UPSERT successful! Processed {num_rows} records (inserted or updated).")
        else:
            print("⚠️ UPSERT request succeeded but returned no data.")

    except Exception as e:
        print(f"❌ Critical Error during initial bulk UPSERT: {e}")
        print("HINT: Ensure the conflict columns form a Unique Constraint on the table.")

# bulk_upsert_game_data()

def get_games_to_scrape(limit: int = 1300) -> list:
    try:
        supabase = get_supabase_client()
    except Exception as e:
        print(f"❌ Aborting DB query due to connection failure: {e}")
        return []

    try:
        print(f"[DB] Fetching up to {limit} rows where iframe_url IS NULL...")
        response = (
            supabase.table(TABLE_NAME)
            .select("id, replay_url")
            .is_("iframe_url", None)
            .limit(limit)
            .execute()
        )
        print(f"[DB] Fetch successful. Rows returned: {len(response.data)}")
        return response.data
    except Exception as e:
        print(f"[DB Error fetching NULL games]: {e}")
        return []


def increment_view_count(game_id):
    """
    Increments the view count in Supabase AND updates the Redis cache
    so the UI reflects the change immediately.
    """
    try:
        supabase = get_supabase_client()
        game_id_int = int(game_id)
        supabase.rpc('increment_views', {'row_id': game_id_int}).execute()

        cache_key = "replays_list_full"
        cached_games = get_cache(cache_key)

        if cached_games:
            game_found = False
            for game in cached_games:
                if str(game.get('id')) == str(game_id):
                    current_views = game.get('views') or 0
                    game['views'] = current_views + 1
                    game_found = True
                    break

            if game_found:
                set_cache(cache_key, cached_games, 43200)

    except Exception as e:
        print(f"❌ Failed to increment view count for {game_id}: {e}")

def get_all_replays():
    try:
        supabase = get_supabase_client()
    except Exception as e:
        print(f"❌ Aborting replay fetch due to connection failure: {e}")
        return []
    try:
        response = (
            supabase.table(table_name=TABLE_NAME)
            .select("id, game_date, away_team, home_team, iframe_url, notes, away_score, home_score, views")
            .not_.is_("iframe_url", None)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"[Error]: {e}")
        return []

def get_all_games():
    try:
        supabase = get_supabase_client()
    except Exception as e:
        print(f"❌ Aborting game fetch due to connection failure: {e}")
        return []

    try:
        response = (
            supabase.table(table_name=TABLE_NAME).select("*, iframe_url").execute()
        )
        return response.data
    except Exception as e:
        print(f"[Error]: {e}")
        return []


def count_games_without_iframe() -> int:
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table(TABLE_NAME)
            .select("id", count='exact', head=True)
            .is_("iframe_url", None)
            .execute()
        )
        return response.count
    except Exception as e:
        print(f"[DB Error counting null iframes]: {e}")
        return -1 # Return -1 to signal an error


