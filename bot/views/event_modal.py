"""Step 3 of event creation: fill in title and description, then create the event."""
from __future__ import annotations

from datetime import datetime

import discord

from bot.database.db import SessionLocal
from bot.database.models import Event, Participant, TimeSlot
from bot.strings import S


class EventModal(discord.ui.Modal):
    event_title = discord.ui.TextInput(
        label=S.MODAL_FIELD_TITLE,
        placeholder=S.MODAL_FIELD_TITLE_PH,
        max_length=200,
    )
    description = discord.ui.TextInput(
        label=S.MODAL_FIELD_DESC,
        placeholder=S.MODAL_FIELD_DESC_PH,
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=2000,
    )

    def __init__(self, apt_id: int, participants: list[discord.Member], slots: list[datetime]) -> None:
        super().__init__(title=S.MODAL_TITLE)
        self.apt_id = apt_id
        self.participants = participants
        self.slots = slots

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        from bot.views.creator_view import CreatorView, build_creator_initial_embed
        from bot.views.vote_view import build_vote_message

        async with SessionLocal() as session:
            from bot.database.models import AppointmentType
            apt = await session.get(AppointmentType, self.apt_id)
            prefix = apt.title_prefix.strip() + " " if apt and apt.title_prefix else ""
            final_title = f"{prefix}{self.event_title.value}"

            event = Event(
                guild_id=interaction.guild_id,
                creator_id=interaction.user.id,
                appointment_type_id=self.apt_id,
                title=final_title,
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

        # DM participants and collect sent message IDs
        failed: list[str] = []
        sent: dict[int, discord.Message] = {}
        for member in self.participants:
            try:
                embed, view = build_vote_message(event, db_slots, interaction.user)
                msg = await member.send(embed=embed, view=view)
                sent[member.id] = msg
            except discord.Forbidden:
                failed.append(member.display_name)

        # DM creator
        creator_msg: discord.Message | None = None
        try:
            creator_embed = build_creator_initial_embed(event, db_slots, self.participants)
            creator_view = CreatorView(event_id=event.id)
            creator_msg = await interaction.user.send(embed=creator_embed, view=creator_view)
        except discord.Forbidden:
            pass

        # Persist message IDs for cleanup-on-restart
        async with SessionLocal() as session:
            for user_id, msg in sent.items():
                p = await session.get(Participant, (event.id, user_id))
                if p:
                    p.dm_message_id = msg.id
                    p.dm_channel_id = msg.channel.id
            if creator_msg:
                ev = await session.get(Event, event.id)
                if ev:
                    ev.creator_dm_message_id = creator_msg.id
                    ev.creator_dm_channel_id = creator_msg.channel.id
            await session.commit()

        reply = S.EVENT_CREATED.format(title=self.event_title.value, count=len(self.participants))
        if failed:
            reply += S.EVENT_CREATED_DM_FAILED.format(names=", ".join(failed))
        await interaction.followup.send(reply, ephemeral=True)
