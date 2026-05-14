"""View for selecting participants after filling in event details."""
from __future__ import annotations

from datetime import datetime

import discord

from bot.database.models import AppointmentType


def _parse_slots(raw: str) -> list[datetime]:
    slots = []
    for part in raw.split(","):
        part = part.strip()
        try:
            slots.append(datetime.strptime(part, "%Y-%m-%d %H:%M"))
        except ValueError:
            pass
    return slots


class ParticipantPickerView(discord.ui.View):
    def __init__(
        self,
        apt: AppointmentType,
        title: str,
        description: str,
        raw_slots: str,
        creator_id: int,
        eligible_members: list[discord.Member] | None = None,
    ) -> None:
        super().__init__(timeout=300)
        self.apt = apt
        self.title = title
        self.description = description
        self.slots = _parse_slots(raw_slots)
        self.selected_users: list[discord.Member] = []

        if eligible_members is not None:
            # Role-restricted: show only eligible members in a regular Select
            self.add_item(RoleFilteredSelect(eligible_members))
        else:
            # No restriction: show all members, but block creator in callback
            self.add_item(OpenSelect(creator_id))

    @discord.ui.button(label="Termin erstellen & Einladungen senden", style=discord.ButtonStyle.success, row=1)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not self.selected_users:
            await interaction.response.send_message(
                "Bitte mindestens einen Teilnehmer auswählen.", ephemeral=True
            )
            return
        if not self.slots:
            await interaction.response.send_message(
                "Keine gültigen Zeitvorschläge gefunden. Format: JJJJ-MM-TT HH:MM", ephemeral=True
            )
            return

        await self._create_event_and_notify(interaction)

    async def _create_event_and_notify(self, interaction: discord.Interaction) -> None:
        from sqlalchemy import select

        from bot.database.db import SessionLocal
        from bot.database.models import Event, Participant, TimeSlot
        from bot.views.vote_view import build_vote_message

        async with SessionLocal() as session:
            event = Event(
                guild_id=interaction.guild_id,
                creator_id=interaction.user.id,
                appointment_type_id=self.apt.id,
                title=self.title,
                description=self.description,
            )
            session.add(event)
            await session.flush()

            for dt in self.slots:
                session.add(TimeSlot(event_id=event.id, start_time=dt))

            for member in self.selected_users:
                session.add(Participant(event_id=event.id, user_id=member.id))

            await session.commit()

            result = await session.execute(
                select(TimeSlot).where(TimeSlot.event_id == event.id)
            )
            db_slots = result.scalars().all()

        failed: list[str] = []
        for member in self.selected_users:
            try:
                embed, view = build_vote_message(event, db_slots, interaction.user)
                await member.send(embed=embed, view=view)
            except discord.Forbidden:
                failed.append(member.display_name)

        msg = (
            f"Termin **{self.title}** erstellt! Einladungen wurden versendet.\n"
            "Nutze `/timely status` um den Abstimmungsstand zu sehen und den finalen Slot zu bestätigen."
        )
        if failed:
            msg += f"\nFolgende Nutzer konnten nicht per DM erreicht werden: {', '.join(failed)}"

        await interaction.response.edit_message(content=msg, view=None)


class RoleFilteredSelect(discord.ui.Select):
    """Select pre-populated with only members who have the required role."""

    def __init__(self, members: list[discord.Member]) -> None:
        self._member_map = {m.id: m for m in members}
        options = [
            discord.SelectOption(label=m.display_name[:100], value=str(m.id))
            for m in members[:25]
        ]
        super().__init__(
            placeholder="Teilnehmer auswählen...",
            min_values=1,
            max_values=min(len(options), 25),
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ParticipantPickerView = self.view
        view.selected_users = [self._member_map[int(v)] for v in self.values]
        await interaction.response.defer()


class OpenSelect(discord.ui.UserSelect):
    """UserSelect for unrestricted events — blocks the creator from being selected."""

    def __init__(self, creator_id: int) -> None:
        super().__init__(
            placeholder="Teilnehmer auswählen...",
            min_values=1,
            max_values=10,
            row=0,
        )
        self.creator_id = creator_id

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ParticipantPickerView = self.view
        selected = [m for m in self.values if m.id != self.creator_id]
        creator_was_selected = len(selected) < len(self.values)

        view.selected_users = selected

        if creator_was_selected and not selected:
            await interaction.response.send_message(
                "Du kannst dich nicht selbst als Teilnehmer auswählen.", ephemeral=True
            )
            return

        if creator_was_selected:
            await interaction.response.send_message(
                "Du wurdest als Ersteller automatisch aus den Teilnehmern entfernt.", ephemeral=True
            )
            return

        await interaction.response.defer()
