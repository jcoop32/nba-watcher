from datetime import datetime, timedelta
import pytz

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
        return f"Tomorrow {time_format_12hr}"
    else:
        return time_format_12hr

