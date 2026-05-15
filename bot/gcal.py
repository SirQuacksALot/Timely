"""Google Calendar 'Add to Calendar' URL builder."""
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode


def build_gcal_url(
    title: str,
    description: str,
    start: datetime,
    duration_hours: int = 1,
) -> str:
    start_utc = start.replace(tzinfo=timezone.utc)
    end_utc = start_utc + timedelta(hours=duration_hours)

    fmt = "%Y%m%dT%H%M%SZ"
    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{start_utc.strftime(fmt)}/{end_utc.strftime(fmt)}",
        "details": description or "",
    }
    return "https://calendar.google.com/calendar/render?" + urlencode(params)
