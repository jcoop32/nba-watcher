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
            return "" # Return empty string

        elif target_date_cst == tomorrow_date_cst:
            # Game is tomorrow
            return f"Tomorrow @ {formatted_time}"

        else:
            # Game is in the past, or further in the future (e.g., in two days or more)
            return "" # Return empty string for any other case, prioritizing today/tomorrow

    except ValueError:
        # Handle cases where the time string is in an unexpected format
        print(f"Error: Could not parse time string '{game_start_time_str}'.")
        return "N/A" # Return a safe default string for errors


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

