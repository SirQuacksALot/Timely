"""Step 3 of event creation: fill in title and description, then create the event."""
from __future__ import annotations

from datetime import datetime

import discord

from bot.database.db import SessionLocal
from bot.database.models import Event, Participant, TimeSlot


class EventModal(discord.ui.Modal, title="Schritt 3/3 — Termin Details"):
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

    def __init__(self, apt_id: int, participants: list[discord.Member], slots: list[datetime]) -> None:
        super().__init__()
        self.apt_id = apt_id
        self.participants = participants
        self.slots = slots

    async def on_submit(self, interaction: discord.Interaction) -> None:
        from bot.views.creator_view import CreatorView, build_creator_initial_embed
        from bot.views.vote_view import build_vote_message

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
            for dt in self.slots:
                slot = TimeSlot(event_id=event.id, start_time=dt)
                session.add(slot)
                db_slots.append(slot)
            await session.flush()

            for member in self.participants:
                session.add(Participant(event_id=event.id, user_id=member.id))

            await session.commit()

            await session.refresh(event)
            for slot in db_slots:
                await session.refresh(slot)

        failed: list[str] = []
        for member in self.participants:
            try:
                embed, view = build_vote_message(event, db_slots, interaction.user)
                msg = await member.send(embed=embed, view=view)
                view.message = msg
            except discord.Forbidden:
                failed.append(member.display_name)

        try:
            creator_embed = build_creator_initial_embed(event, db_slots, self.participants)
            creator_view = CreatorView(event_id=event.id)
            creator_msg = await interaction.user.send(embed=creator_embed, view=creator_view)
            creator_view.message = creator_msg
        except discord.Forbidden:
            pass

        msg = (
            f"Terminanfrage **{self.event_title.value}** erstellt! "
            f"Einladungen wurden an {len(self.participants)} Teilnehmer versendet.\n"
            "Du erhältst die Status-Übersicht per DM."
        )
        if failed:
            msg += f"\nFolgende Nutzer konnten nicht per DM erreicht werden: {', '.join(failed)}"

        await interaction.response.send_message(msg, ephemeral=True)
