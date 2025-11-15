from datetime import datetime, timezone, timedelta
import pytz
import re

def convert_time_and_check_day_12hr(est_time_str: str) -> str:
    """
    Converts a time string from EST/EDT to CST/CDT, outputs in 12-hour format (hh:mm PM),
    and prefixes with 'Tomorrow' if the date is the next day in CST.

    :param est_time_str: The target time string in 'yyyy-mm-dd hh:mm' EST format.
    :return: Formatted time string (e.g., '7:00 PM' or 'Tomorrow 7:00 PM').
    """

    # 1. Define Time Zones
    ET_ZONE = pytz.timezone('US/Eastern')
    CST_ZONE = pytz.timezone('US/Central')
    format_code_input = "%Y-%m-%d %H:%M"
    # Format code for 12-hour clock: %I (hour, zero-padded), %M (minute), %p (AM/PM)
    # We use %-I (or #I on some systems) to avoid leading zero for single-digit hours.
    # We will manually handle the removal of the leading zero for robustness across systems.
    format_code_output = "%I:%M %p"

    # 2. Localize the Target Time (EST/EDT)
    try:
        naive_target_time = datetime.strptime(est_time_str, format_code_input)
        target_time_est = ET_ZONE.localize(naive_target_time)
    except ValueError:
        return "Error: Input format must be 'yyyy-mm-dd hh:mm'."

    # 3. Convert to Central Time (CST/CDT)
    target_time_cst = target_time_est.astimezone(CST_ZONE)

    # 4. Get Current Date (in CST) for Comparison
    current_date_cst = datetime.now(CST_ZONE).date()
    tomorrow_date_cst = current_date_cst + timedelta(days=1)

    # 5. Format the Time (and remove leading zero for hours 1-9)
    # Use .lstrip('0') to remove the leading zero if the hour is < 10 (e.g., '07:00 PM' -> '7:00 PM')
    time_format_12hr = target_time_cst.strftime(format_code_output).lstrip('0')

    # 6. Conditional Formatting Logic
    target_date_cst = target_time_cst.date()

    if target_date_cst == tomorrow_date_cst:
        return f"Tomorrow @ {time_format_12hr}"
    else:
        return time_format_12hr




def has_game_started(game_start_time_str):
    try:
        target_time = datetime.fromisoformat(game_start_time_str.replace('Z', '+00:00'))

        # 2. Get Current Time (Always use UTC for comparison)
        current_time_utc = datetime.now(timezone.utc)

        # 3. Compare Times
        # If the target time is GREATER than the current time, the game has NOT started.
        started_yet = target_time <= current_time_utc

        return started_yet

    except ValueError:
        # Handle cases where the time string is in an unexpected format
        print(f"Error: Could not parse time string '{game_start_time_str}'.")
        return False


def get_game_day_status(game_start_time_str: str) -> str:

    CST_ZONE = pytz.timezone('US/Central')

    try:
        # 1. Localize Target Time (API time is UTC)
        # Convert API string to a UTC-aware datetime object
        target_time_utc = datetime.fromisoformat(game_start_time_str.replace('Z', '+00:00'))

        # 2. Get Current Date in CST
        current_time_cst = datetime.now(CST_ZONE)
        current_date_cst = current_time_cst.date()

        # 3. Convert Target Time to CST
        target_time_cst = target_time_utc.astimezone(CST_ZONE)
        target_date_cst = target_time_cst.date()

        # Calculate Tomorrow's Date (in CST)
        tomorrow_date_cst = current_date_cst + timedelta(days=1)

        # 4. Format the Time
        # Output format: H:MM PM/AM (remove leading zero for hours 1-9)
        formatted_time = target_time_cst.strftime("%I:%M %p").lstrip('0')

        # 5. Conditional Output Logic

        if target_date_cst == current_date_cst:
            # Game is today
            return f"Today @ {formatted_time} CST"

        elif target_date_cst == tomorrow_date_cst:
            # Game is tomorrow
            return f"Tomorrow @ {formatted_time} CST"
        else:
            # Game is in the past, or further in the future (e.g., in two days or more)
            return ""

    except ValueError:
        # Handle cases where the time string is in an unexpected format
        print(f"Error: Could not parse time string '{game_start_time_str}'.")
        return "N/A"


def convert_et_to_cst_conditional(input_string: str) -> str:
    """
    Converts a time string from Eastern Time (ET) to Central Time (CST/CDT)
    only if it matches the format 'H:MM AM/PM ET'. Returns the original string
    if the format does not match.
    """

    # Regular Expression to match 'H:MM AM/PM ET'
    # Use re.IGNORECASE flag to allow 'am', 'pm', 'AM', or 'PM'.
    # Note: We must also check the case of 'ET' if we want maximum flexibility,
    # but the API usually uses 'ET' or 'EST', so we stick with 'ET' here.
    TIME_PATTERN = r'^\d{1,2}:\d{2}\s(am|pm)\sET$'

    # Check if the input string matches the required time format
    # Use re.IGNORECASE to fix the case mismatch
    if not re.match(TIME_PATTERN, input_string, re.IGNORECASE):
        # If it does not match (e.g., 'Final', 'Scheduled', etc.), return the original string
        return input_string

    # --- Conversion Logic ---

    # Define Time Zones
    ET_ZONE = pytz.timezone('US/Eastern')
    CST_ZONE = pytz.timezone('US/Central')

    # 1. Establish Date Context (Necessary for accurate DST handling)
    current_date_et = datetime.now(CST_ZONE).astimezone(ET_ZONE).date()

    # 2. Prepare and Parse the Input Time
    try:
        # Step A: Standardize the string for parsing (Crucial for %p to work!)
        # Python's datetime parser (%p) usually expects AM/PM to be uppercase.
        # This fixes inputs like "7:00 pm ET" or "7:00 PM ET".
        time_part_for_parsing = input_string.upper().replace(" ET", "").strip()

        # Step B: Parse the time
        time_part_naive = datetime.strptime(time_part_for_parsing, "%I:%M %p")

    except ValueError:
        # If parsing fails despite the regex match, return the original string as a fallback
        return input_string

    # 3. Localize to ET
    target_time_naive = datetime.combine(current_date_et, time_part_naive.time())
    target_time_et = ET_ZONE.localize(target_time_naive)

    # 4. Convert to Central Time (CST/CDT)
    target_time_cst = target_time_et.astimezone(CST_ZONE)

    # 5. Format and Return the CST Time
    # Output format: H:MM PM CST (remove leading zero from hour, append Time Zone Abbreviation)
    # .lstrip('0') handles removing leading zero for hours 1-9
    formatted_cst_time = target_time_cst.strftime("%I:%M %p").lstrip('0')

    return f"{formatted_cst_time} {target_time_cst.strftime('%Z')}"


def convert_iso_minutes(iso_time_str):
    """Converts ISO 8601 duration string (e.g., 'PT25M01.00S') to M:SS format."""
    if not isinstance(iso_time_str, str) or not iso_time_str.startswith('PT'):
        return ""

    # Pattern to match Minutes and Seconds
    match = re.match(r'PT(\d+)M(\d+)\.', iso_time_str)

    if match:
        minutes = int(match.group(1))
        # Take the integer part of seconds
        seconds = int(match.group(2))
        return f"{minutes}:{seconds:02}"

    # Fallback for minutes only (e.g., 'PT1M')
    match_m_only = re.match(r'PT(\d+)M', iso_time_str)
    if match_m_only:
        return f"{int(match_m_only.group(1))}:00"

    return ""

def format_et_to_cst_status(et_datetime_str: str) -> str:

    et_tz = pytz.timezone('America/New_York')
    cst_tz = pytz.timezone('America/Chicago')
    input_format_24hr = '%Y-%m-%d %H:%M'
    output_format_12hr = '%l:%M %p' # e.g., 09:00 PM

    try:
        # 1. Parse and localize the input time as ET
        dt_et_naive = datetime.strptime(et_datetime_str, input_format_24hr)
        dt_et = et_tz.localize(dt_et_naive)

        # 2. Convert to CST
        dt_cst = dt_et.astimezone(cst_tz)

        # 3. Get the current date in CST for comparison
        # (Current time is Tuesday, November 4, 2025 at 12:48:19 PM CST)
        now_cst = datetime.now(cst_tz)
        today_date = now_cst.date()
        target_date = dt_cst.date()

        # 4. Determine status and format time
        cst_time_12hr = dt_cst.strftime(output_format_12hr)

        if target_date == today_date:
            date_status = 'Today'
        elif target_date == (today_date + timedelta(days=1)):
            date_status = 'Tomorrow'
        else:
            # If neither, return the full date (YYYY-MM-DD)
            date_status = target_date.strftime('%Y-%m-%d')

        # 5. Return the final formatted string
        return f"{date_status} @ {cst_time_12hr}"

    except ValueError:
        return "Error: Invalid datetime format. Please use 'YYYY-MM-DD HH:MM'."
    except pytz.exceptions.UnknownTimeZoneError:
        return "Error: Time zone configuration issue."


def convert_ms_to_yyyymmdd(ms_timestamp, timezone_str='US/Central'):
    """
    Converts a 13-digit millisecond Unix timestamp to a YYYY-MM-DD string
    in the specified timezone.
    """
    try:
        ms_timestamp = float(ms_timestamp)
        s_timestamp = ms_timestamp / 1000

        dt_naive_utc = datetime.utcfromtimestamp(s_timestamp)
        dt_aware_utc = pytz.utc.localize(dt_naive_utc)

        target_timezone = pytz.timezone(timezone_str)
        dt_target = dt_aware_utc.astimezone(target_timezone)

        # Return in YYYY-MM-DD format
        return dt_target.strftime('%Y-%m-%d')

    except (ValueError, TypeError, OSError):
        return None

def convert_ms_timestamp_to_12hr(ms_timestamp):
    """
    Converts a 13-digit millisecond Unix timestamp to a formatted 12-hour
    string (YYYY MM DD HH:MM AM/PM) in the US/Central timezone (CST/CDT).

    :param ms_timestamp: The 13-digit timestamp (e.g., 1763155800000).
    :return: A formatted time string in US/Central time.
    """
    try:
        # Convert timestamp from string or int to a number
        ms_timestamp = float(ms_timestamp)

        # Convert from milliseconds to seconds
        s_timestamp = ms_timestamp / 1000

        # 1. Create a naive datetime object from the timestamp in UTC
        dt_naive_utc = datetime.datetime.utcfromtimestamp(s_timestamp)

        # 2. Localize the naive object to make it timezone-aware (aware of itself as UTC)
        dt_aware_utc = pytz.utc.localize(dt_naive_utc)

        # 3. Convert to the target timezone
        try:
            target_timezone = pytz.timezone('US/Central')
            dt_target_original = dt_aware_utc.astimezone(target_timezone)

            dt_target = dt_target_original + datetime.timedelta(hours=1)
            return dt_target.strftime('%Y %m %d %I:%M %p')

        except pytz.exceptions.UnknownTimeZoneError:
            return "Error: Could not load US/Central timezone"

    except (ValueError, TypeError, OSError):
        return "Error: Invalid timestamp provided"
