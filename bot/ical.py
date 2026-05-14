from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

from icalendar import Calendar
from icalendar import Event as CalEvent


def build_ics(title: str, description: str, start: datetime, duration_hours: int = 1) -> io.BytesIO:
    cal = Calendar()
    cal.add("prodid", "-//Timely Discord Bot//EN")
    cal.add("version", "2.0")

    ev = CalEvent()
    ev.add("summary", title)
    ev.add("description", description or "")
    ev.add("dtstart", start.replace(tzinfo=timezone.utc))
    ev.add("dtend", (start + timedelta(hours=duration_hours)).replace(tzinfo=timezone.utc))
    ev.add("dtstamp", datetime.now(tz=timezone.utc))

    cal.add_component(ev)

    buf = io.BytesIO(cal.to_ical())
    buf.seek(0)
    return buf
