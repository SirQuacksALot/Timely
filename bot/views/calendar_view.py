"""Confirmation DM view with .ics download and Google Calendar link buttons."""
from __future__ import annotations

import discord

from bot.strings import S


def build_confirmation_view(gcal_url: str, event_id: int) -> "CalendarView":
    return CalendarView(gcal_url=gcal_url, event_id=event_id)


class CalendarView(discord.ui.View):
    def __init__(self, gcal_url: str, event_id: int) -> None:
        super().__init__(timeout=None)
        self.event_id = event_id
        self.add_item(discord.ui.Button(
            label=S.GCAL_BUTTON,
            url=gcal_url,
            style=discord.ButtonStyle.link,
            emoji="📅",
            row=0,
        ))
        self.add_item(_IcsButton(event_id=event_id))


class _IcsButton(discord.ui.Button):
    def __init__(self, event_id: int) -> None:
        super().__init__(
            label=S.ICS_BUTTON,
            style=discord.ButtonStyle.secondary,
            emoji="📥",
            custom_id=f"timely:ics:{event_id}",
            row=0,
        )
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction) -> None:
        from sqlalchemy import select

        from bot.database.db import SessionLocal
        from bot.database.models import Event, TimeSlot
        from bot.ical import build_ics

        async with SessionLocal() as session:
            event = await session.get(Event, self.event_id)
            if not event or not event.confirmed_slot_id:
                await interaction.response.send_message("Event not found.", ephemeral=True)
                return
            slot = await session.get(TimeSlot, event.confirmed_slot_id)

        ics = build_ics(
            title=event.title,
            description=event.description or "",
            start=slot.start_time,
        )
        await interaction.response.send_message(
            S.ICS_SENT,
            file=discord.File(ics, filename="appointment.ics"),
            ephemeral=True,
        )
