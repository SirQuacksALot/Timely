"""DM view for participants to vote on time slots."""
from __future__ import annotations

import discord

from bot.database.models import Event, TimeSlot

_SEVEN_DAYS = 7 * 24 * 3600


def build_vote_message(
    event: Event,
    slots: list[TimeSlot],
    creator: discord.Member | discord.User,
) -> tuple[discord.Embed, VoteView]:
    embed = discord.Embed(
        title=f"Termineinladung: {event.title}",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Erstellt von", value=creator.display_name, inline=True)
    if event.description:
        embed.add_field(name="Beschreibung", value=event.description, inline=False)

    slot_lines = "\n".join(
        f"`{i+1}.` {s.start_time.strftime('%d.%m.%Y %H:%M')}" for i, s in enumerate(slots)
    )
    embed.add_field(name="Zeitvorschläge", value=slot_lines, inline=False)
    embed.set_footer(text="Bitte wähle alle Zeitfenster, die für dich passen. Diese Anfrage läuft in 7 Tagen ab.")

    view = VoteView(event_id=event.id, slots=slots)
    return embed, view


class VoteView(discord.ui.View):
    def __init__(self, event_id: int, slots: list[TimeSlot]) -> None:
        super().__init__(timeout=_SEVEN_DAYS)
        self.event_id = event_id
        self.message: discord.Message | None = None
        self.add_item(SlotSelect(event_id=event_id, slots=slots))
        self.add_item(DeclineButton(event_id=event_id))

    async def on_timeout(self) -> None:
        if self.message:
            try:
                await self.message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass


class DeclineButton(discord.ui.Button):
    def __init__(self, event_id: int) -> None:
        super().__init__(
            label="Ablehnen",
            style=discord.ButtonStyle.danger,
            row=1,
            custom_id=f"timely:decline:{event_id}",
        )
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction) -> None:
        from bot.database.db import SessionLocal
        from bot.database.models import Participant, ParticipantStatus

        async with SessionLocal() as session:
            p = await session.get(Participant, (self.event_id, interaction.user.id))
            if p:
                p.status = ParticipantStatus.DECLINED
                await session.commit()

        await interaction.response.edit_message(
            content="Du hast den Termin abgelehnt.", embed=None, view=None
        )

        from bot.views.creator_view import auto_confirm_if_complete
        await auto_confirm_if_complete(self.event_id, interaction.client)


class SlotSelect(discord.ui.Select):
    def __init__(self, event_id: int, slots: list[TimeSlot]) -> None:
        options = [
            discord.SelectOption(
                label=s.start_time.strftime("%d.%m.%Y %H:%M"),
                value=str(s.id),
            )
            for s in slots
        ]
        super().__init__(
            placeholder="Wähle alle passenden Zeitfenster...",
            min_values=0,
            max_values=len(options),
            options=options,
            custom_id=f"timely:slots:{event_id}",
            row=0,
        )
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction) -> None:
        from sqlalchemy import delete, select

        from bot.database.db import SessionLocal
        from bot.database.models import Participant, ParticipantStatus, TimeSlot, TimeSlotVote

        selected_ids = {int(v) for v in self.values}

        async with SessionLocal() as session:
            result = await session.execute(
                select(TimeSlot).where(TimeSlot.event_id == self.event_id)
            )
            all_slots = result.scalars().all()

            await session.execute(
                delete(TimeSlotVote).where(
                    TimeSlotVote.event_id == self.event_id,
                    TimeSlotVote.participant_user_id == interaction.user.id,
                )
            )

            for slot in all_slots:
                session.add(
                    TimeSlotVote(
                        time_slot_id=slot.id,
                        participant_user_id=interaction.user.id,
                        event_id=self.event_id,
                        available=slot.id in selected_ids,
                    )
                )

            p = await session.get(Participant, (self.event_id, interaction.user.id))
            if p:
                p.status = ParticipantStatus.ACCEPTED
            await session.commit()

        await interaction.response.edit_message(
            content="Deine Verfügbarkeit wurde gespeichert. Danke!", embed=None, view=None
        )

        from bot.views.creator_view import auto_confirm_if_complete
        await auto_confirm_if_complete(self.event_id, interaction.client)
