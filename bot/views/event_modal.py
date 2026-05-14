"""Step 2 of event creation: fill in details and create the event."""
from __future__ import annotations

from datetime import datetime

import discord

from bot.database.db import SessionLocal
from bot.database.models import AppointmentType, Event, Participant, TimeSlot


def _parse_slots(raw: str) -> list[datetime]:
    slots = []
    for part in raw.split(","):
        part = part.strip()
        try:
            slots.append(datetime.strptime(part, "%Y-%m-%d %H:%M"))
        except ValueError:
            pass
    return slots


class EventModal(discord.ui.Modal, title="Schritt 2/2 — Termin Details"):
    event_title = discord.ui.TextInput(
        label="Titel",
        placeholder="z.B. Team-Meeting Q2",
        max_length=200,
    )
    description = discord.ui.TextInput(
        label="Beschreibung",
        placeholder="Worum geht es?",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=2000,
    )
    time_slots = discord.ui.TextInput(
        label="Zeitvorschläge (kommagetrennt)",
        placeholder="2026-06-01 14:00, 2026-06-02 10:00",
        max_length=500,
    )

    def __init__(self, apt_id: int, participants: list[discord.Member]) -> None:
        super().__init__()
        self.apt_id = apt_id
        self.participants = participants

    async def on_submit(self, interaction: discord.Interaction) -> None:
        from bot.views.creator_view import CreatorView, build_creator_initial_embed
        from bot.views.vote_view import build_vote_message

        slots = _parse_slots(self.time_slots.value)
        if not slots:
            await interaction.response.send_message(
                "Keine gültigen Zeitvorschläge gefunden. Format: JJJJ-MM-TT HH:MM",
                ephemeral=True,
            )
            return

        async with SessionLocal() as session:
            event = Event(
                guild_id=interaction.guild_id,
                creator_id=interaction.user.id,
                appointment_type_id=self.apt_id,
                title=self.event_title.value,
                description=self.description.value or "",
            )
            session.add(event)
            await session.flush()

            db_slots: list[TimeSlot] = []
            for dt in slots:
                slot = TimeSlot(event_id=event.id, start_time=dt)
                session.add(slot)
                db_slots.append(slot)
            await session.flush()

            for member in self.participants:
                session.add(Participant(event_id=event.id, user_id=member.id))

            await session.commit()

            # Refresh to ensure all IDs are populated
            await session.refresh(event)
            for slot in db_slots:
                await session.refresh(slot)

        # DM all participants with the vote view
        failed: list[str] = []
        for member in self.participants:
            try:
                embed, view = build_vote_message(event, db_slots, interaction.user)
                await member.send(embed=embed, view=view)
            except discord.Forbidden:
                failed.append(member.display_name)

        # DM creator with their status/control view
        try:
            creator_embed = build_creator_initial_embed(event, db_slots, self.participants)
            creator_view = CreatorView(event_id=event.id)
            await interaction.user.send(embed=creator_embed, view=creator_view)
        except discord.Forbidden:
            pass

        msg = (
            f"Termin **{self.event_title.value}** erstellt! Einladungen wurden versendet.\n"
            "Du erhältst die Status-Übersicht und den Bestätigungs-Button per DM."
        )
        if failed:
            msg += f"\nFolgende Nutzer konnten nicht per DM erreicht werden: {', '.join(failed)}"

        await interaction.response.send_message(msg, ephemeral=True)
