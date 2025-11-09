import os
from dotenv import load_dotenv
from supabase import create_client, Client
from api.played_games import scrape_nba_schedule

load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")
TABLE_NAME = "nba_game_data_2025_26" # Ensure this matches your table name

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env file.")
    exit()

try:
    # Synchronous client initialized
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client initialized successfully.")
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    exit()


def get_games_to_scrape(limit: int = 1300) -> list:
    try:
        print(f"[DB] Fetching up to {limit} rows where iframe_url IS NULL...")
        response = (
            supabase.table(TABLE_NAME)
            .select("id, replay_url")
            .is_("iframe_url", None)   # Filter for rows where iframe_url IS NULL
            .limit(limit)
            .execute()
        )
        print(f"[DB] Fetch successful. Rows returned: {len(response.data)}")
        return response.data
    except Exception as e:
        print(f"[DB Error fetching NULL games]: {e}")
        return []
# ----------------------------------------


def bulk_upsert_game_data():
    data_list = scrape_nba_schedule()

    # We rely on scrape_nba_schedule setting 'iframe_url': None (or omitting it)

    if not data_list:
        print("No schedule data scraped for upsert. Exiting.")
        return

    num_rows = len(data_list)
    # The composite key for uniqueness check
    conflict_cols = "replay_url"

    print(f"\n--- Starting Bulk UPSERT for {num_rows} schedule records into '{TABLE_NAME}' ---")

    try:
        response = (
            supabase.table(TABLE_NAME)
            .upsert(data_list, on_conflict=conflict_cols)
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


def get_all_games():
    try:
        response = (
            supabase.table(table_name=TABLE_NAME).select("*, iframe_url").execute()
        )
        return response.data
    except Exception as e:
        print(f"[Error]: {e}")


def get_all_replays():
    try:
        # Fetch all records where iframe_url is NOT NULL, ordered by game_date descending
        response = (
            supabase.table(TABLE_NAME)
            .select("*")
            .not_.is_("iframe_url", None)
            .order("game_date", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"[DB Error fetching replays]: {e}")
        return []
