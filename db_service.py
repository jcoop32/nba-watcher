# jcoop32/nba-watcher/nba-watcher-a4c77f1f60af3f329fe1623e00dceda3da0d2c7f/db_service.py

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from api.played_games import scrape_nba_schedule

load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")
TABLE_NAME = "nba_game_data_2025_26" # Ensure this matches your table name

# --- NEW FUNCTION: Lazy Client Getter ---
def get_supabase_client() -> Client:
    """Initializes and returns the Supabase client when called."""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
             raise ValueError("Supabase URL or Key is missing from environment.")

        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client
    except Exception as e:
        # Re-raise the error so the calling function (bulk_upsert) can handle the connection failure
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


def get_all_replays():
    try:
        supabase = get_supabase_client()
    except Exception as e:
        print(f"❌ Aborting replay fetch due to connection failure: {e}")
        return []

    try:
        response = (
            supabase.table(table_name=TABLE_NAME).select("*, iframe_url").execute()
        )
        return response.data
    except Exception as e:
        print(f"[Error]: {e}")
        return []

# --- Note: get_all_games is used by the Flask index route and should be fixed here too ---
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
