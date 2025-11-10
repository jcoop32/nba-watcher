from utils.get_iframe_urls import start_replay_scrape
from db_service import get_supabase_client, TABLE_NAME, bulk_upsert_game_data
import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def send_email_notification(message: str):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "coopj3265@gmail.com"
        smtp_password = os.environ.get("GMAIL_PASS")

        recipient_email = "joshuacooper332@gmail.com"

        if not all([smtp_server, smtp_user, smtp_password, recipient_email]):
            print("❌ EMAIL FAILED: SMTP/Recipient credentials missing.")
            return

        # Create the email content
        msg = MIMEText(message)
        msg['Subject'] = "NBA Replay Games Updated"
        msg['From'] = smtp_user
        msg['To'] = recipient_email

        # Connect to the SMTP server and send
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()

            # This is the crucial authentication step
            server.login(smtp_user, smtp_password)

            # Send the mail
            server.sendmail(smtp_user, recipient_email, msg.as_string())

        print(f"✅ Email notification sent successfully to {recipient_email}.")

    except smtplib.SMTPAuthenticationError:
        print("❌ CRITICAL EMAIL SEND ERROR: SMTP Authentication Failed.")
        print("ACTION: Please re-check your 16-character App Password.")
    except Exception as e:
        print(f"❌ CRITICAL EMAIL SEND ERROR: {type(e).__name__} - {e}")

def update_and_fetch_new_replay_games():
    supabase = get_supabase_client()
    print("Updating db with new games played...")
    bulk_upsert_game_data()
    print("\n--- Running Scraper ---")
    start_replay_scrape(supabase, TABLE_NAME)

    send_email_notification(
        "NBA Watcher cron job complete! Game replays are now updated and live."
    )

update_and_fetch_new_replay_games()

