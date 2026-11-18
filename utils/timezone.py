from zoneinfo import ZoneInfo


def format_datetime_wib(dt):
    if not dt:
        return ""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    return dt.astimezone(
        ZoneInfo("Asia/Jakarta")
    ).strftime("%d %b %Y %H:%M WIB")