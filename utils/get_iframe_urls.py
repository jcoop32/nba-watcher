import asyncio
from playwright.async_api import async_playwright, Playwright
from supabase import Client
import time


REPLAY_BASE_URL = "https://basketball-video.com/"
CONCURRENCY_LIMIT = 5
SEMAPHORE = asyncio.Semaphore(CONCURRENCY_LIMIT)

# --- A. Scraping Logic with Robust Click Handling and Debugging Prints ---

async def scrape_iframe_url(p: Playwright, game_record: dict) -> dict:

    game_id = game_record['id']
    url_to_scrape = REPLAY_BASE_URL + game_record['replay_url']
    game_record['iframe_url'] = "Error: Failed"

    async with SEMAPHORE:
        # Launch browser context
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"[{game_id}] ⏳ Starting scrape for: {game_record['replay_url']}")
        iframe_src = None

        try:
            # 1. Go to the primary replay page (slug)
            await page.goto(url_to_scrape, wait_until='domcontentloaded', timeout=15000)
            print(f"[{game_id}] Step 1/3: Loaded replay page: {page.url}")

            # 2. Click the 'Watch' button and switch to the new page/tab
            try:
                # Use expect_popup to intercept the new page opened by target="_blank"
                async with page.expect_popup() as popup_info:
                    await page.click('a.su-button:has-text("Watch")', timeout=10000)

                # Switch the focus to the new page/tab
                new_page = await popup_info.value

                # Wait for the new page to load its content
                await new_page.wait_for_load_state('domcontentloaded')

                page = new_page

                print(f"[{game_id}] Step 2/3: Click successful and switched focus.")
                print(f"[{game_id}] DEBUG: Current URL after navigation: {page.url}")

            except Exception as click_error:
                print(f"[{game_id}] Step 2/3: ❌ CLICK FAILED (Timeout or New Page Error): {click_error.__class__.__name__}")
                game_record['iframe_url'] = "Error: Click Failed"
                return game_record # Exit early on failure


            # 3. Explicitly wait for the iframe selector to appear before locating it
            await page.wait_for_selector('iframe.yt-embed', state='attached', timeout=15000)
            print(f"[{game_id}] Step 3/3: Iframe selector found on page.")

            # Now, locate and extract the element
            iframe_locator = page.locator('iframe.yt-embed')

            if await iframe_locator.count() > 0:
                iframe_src = await iframe_locator.first.get_attribute('src')

                if iframe_src:
                    # Prepend https: if necessary (handles //ok.ru/videoembed/...)
                    if iframe_src.startswith('//'):
                        iframe_src = f"https:{iframe_src}"

                    game_record['iframe_url'] = iframe_src
                    print(f"[{game_id}] Step 3/3: ✅ Success! Extracted iframe URL: {iframe_src[:50]}...")
                else:
                    game_record['iframe_url'] = "Error: Empty SRC"
                    print(f"[{game_id}] Step 3/3: ❌ Error: Found iframe element but src attribute was empty.")
            else:
                game_record['iframe_url'] = "Error: Iframe Not Found"
                print(f"[{game_id}] Step 3/3: ❌ Error: Could not find the streaming iframe (iframe.yt-embed).")


        except Exception as e:
            # General catch-all for navigation timeouts, network errors, etc.
            print(f"[{game_id}] ❌ CRITICAL ERROR during scraping: {e.__class__.__name__} - {e}")

        finally:
            await browser.close()
            print(f"[{game_id}] Browser closed.")
            return game_record

# --- B. Orchestration and Database Update ---

async def run_replay_scraper(supabase_client: Client, table_name: str):

    # Import the fetching function from db_service locally
    from db_service import get_games_to_scrape

    start_time = time.time()
    print("\n-----------------------------------------------------")
    print("--- STARTING ASYNCHRONOUS REPLAY SCRAPER PIPELINE ---")
    print("-----------------------------------------------------")

    # 1. Fetch only the records where iframe_url is NULL
    games_to_scrape = get_games_to_scrape(limit=1300)

    if not games_to_scrape:
        print("✅ Filter complete: No new games found to scrape. Exiting scraper.")
        return

    print(f"Found {len(games_to_scrape)} games requiring scraping.")

    # 2. Run all scraping tasks concurrently
    async with async_playwright() as p:
        tasks = [scrape_iframe_url(p, game) for game in games_to_scrape]
        updated_records = await asyncio.gather(*tasks)

    # 3. Prepare the payload for bulk update
    update_payload = []
    failed_count = 0
    for record in updated_records:
        if record['iframe_url'] and "Error" not in record['iframe_url']:
            update_payload.append({
                'id': record['id'],
                'iframe_url': record['iframe_url']
            })
        else:
            failed_count += 1

    print(f"\nScraping phase finished. Successful records found: {len(update_payload)}")

    # --- 4. Database Update using concurrent individual UPDATEs ---
    async def concurrent_db_update(payload_item: dict):
        """Runs a single, atomic update operation for one row using asyncio.to_thread."""
        try:
            update_data = {'iframe_url': payload_item['iframe_url']}

            # --- THE FIX: Use asyncio.to_thread to run the synchronous execute() call ---
            await asyncio.to_thread(
                supabase_client.table(table_name)
                .update(update_data)
                .eq('id', payload_item['id'])
                .execute
            )
            # --------------------------------------------------------------------------
            return True
        except Exception as e:
            # Log failure but do not crash the concurrent process
            print(f"[{payload_item['id']}] ❌ Individual DB Update FAILED: {e.__class__.__name__} - Row skipped.")
            return False

    successful_updates = 0
    if update_payload:
        print(f"Starting concurrent database updates for {len(update_payload)} records...")

        # Create a task for every update request and run them concurrently
        update_tasks = [concurrent_db_update(item) for item in update_payload]
        update_results = await asyncio.gather(*update_tasks)

        successful_updates = sum(update_results)

        print(f"✅ Bulk update complete. {successful_updates} rows updated successfully.")

    # -------------------------------------------------------------------------------------

    end_time = time.time()
    print(f"\n--- Scraper Summary ---")
    print(f"Total time: {end_time - start_time:.2f} seconds.")
    print(f"Total rows scraped: {len(games_to_scrape)}")
    print(f"Rows updated successfully: {successful_updates}")
    print(f"Rows failed/skipped: {failed_count + (len(games_to_scrape) - successful_updates) - failed_count}") # Simplified counting



def start_replay_scrape(supabase_client: Client, table_name: str):
    """Synchronous wrapper to run the asynchronous scraper from a sync context."""
    return asyncio.run(run_replay_scraper(supabase_client, table_name))

