import os
from dotenv import load_dotenv
from supabase import create_client, Client
from api.played_games import scrape_nba_schedule

load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")
TABLE_NAME = "nba_game_data_2025_26"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env file.")
    exit()

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client initialized successfully.")
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    exit()



def bulk_upsert_game_data():
    data_list = scrape_nba_schedule()
    if not data_list:
        print("No data provided for upsert. Exiting.")
        return

    num_rows = len(data_list)

    print(f"\n--- Starting Bulk UPSERT for {num_rows} records into '{TABLE_NAME}' ---")

    try:
        response = (
            supabase.table(TABLE_NAME)
            .upsert(data_list, on_conflict="replay_url")
            .execute()
        )

        inserted_data = response.data

        if inserted_data:
            print(f"✅ UPSERT successful! Processed {num_rows} records")
        else:
            print("⚠️ UPSERT request succeeded but returned no data.")

    except Exception as e:
        print(f"❌ Critical Error during bulk UPSERT: {e}")
        print("HINT: Ensure the conflict columns (game_date, away_team, home_team) form a Unique Constraint on the table.")



def get_all_games():
    try:
        response = (
            supabase.table(table_name=TABLE_NAME).select("*").execute()
        )
        return response.data
    except Exception as e:
        print(f"[Error]: {e}")
