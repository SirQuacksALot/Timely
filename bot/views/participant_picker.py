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
    ) -> None:
        super().__init__(timeout=300)
        self.apt = apt
        self.title = title
        self.description = description
        self.slots = _parse_slots(raw_slots)
        self.selected_users: list[discord.Member] = []

        self.add_item(ParticipantSelect(apt))

    @discord.ui.button(label="Termin erstellen & Einladungen senden", style=discord.ButtonStyle.success, row=1)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not self.selected_users:
            await interaction.response.send_message("Bitte mindestens einen Teilnehmer auswählen.", ephemeral=True)
            return
        if not self.slots:
            await interaction.response.send_message("Keine gültigen Zeitvorschläge gefunden.", ephemeral=True)
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

        # DM all participants
        failed: list[str] = []
        for member in self.selected_users:
            try:
                embed, view = build_vote_message(event, db_slots, interaction.user)
                await member.send(embed=embed, view=view)
            except discord.Forbidden:
                failed.append(member.display_name)

        msg = f"Termin **{self.title}** erstellt! Einladungen wurden versendet.\nNutze `/timely status` um den Abstimmungsstand zu sehen und den finalen Slot zu bestätigen."
        if failed:
            msg += f"\nFolgende Nutzer konnten nicht per DM erreicht werden: {', '.join(failed)}"

        await interaction.response.edit_message(content=msg, view=None)


class ParticipantSelect(discord.ui.UserSelect):
    def __init__(self, apt: AppointmentType) -> None:
        super().__init__(
            placeholder="Teilnehmer auswählen...",
            min_values=1,
            max_values=10,
            row=0,
        )
        self.apt = apt

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ParticipantPickerView = self.view

        # Filter by invitee role restriction if set
        if self.apt.restrict_invitees_to_role_id:
            allowed = [
                m for m in self.values
                if any(r.id == self.apt.restrict_invitees_to_role_id for r in m.roles)
            ]
            rejected = [m for m in self.values if m not in allowed]
            if rejected:
                names = ", ".join(m.display_name for m in rejected)
                await interaction.response.send_message(
                    f"Folgende Nutzer haben nicht die benötigte Rolle und wurden entfernt: {names}",
                    ephemeral=True,
                )
                view.selected_users = allowed
                return
        else:
            view.selected_users = list(self.values)

        await interaction.response.defer()
