"""Status view and confirm flow for the event creator."""
from __future__ import annotations

import discord
from sqlalchemy import select

from bot.database.db import SessionLocal
from bot.database.models import (
    Event,
    EventStatus,
    Participant,
    ParticipantStatus,
    TimeSlot,
    TimeSlotVote,
)
from bot.strings import S

_SEVEN_DAYS = 7 * 24 * 3600

_STATUS_ICON = {
    ParticipantStatus.PENDING: "⏳",
    ParticipantStatus.ACCEPTED: "✅",
    ParticipantStatus.DECLINED: "❌",
}


def build_creator_initial_embed(
    event: Event,
    slots: list[TimeSlot],
    participants: list[discord.Member],
) -> discord.Embed:
    embed = discord.Embed(
        title=S.CREATOR_INITIAL_TITLE.format(title=event.title),
        color=discord.Color.blurple(),
    )
    if event.description:
        embed.description = event.description

    slot_lines = "\n".join(f"• {s.start_time.strftime('%d.%m.%Y %H:%M')}" for s in slots)
    embed.add_field(name=S.CREATOR_INITIAL_SLOTS, value=slot_lines or "—", inline=False)

    participant_lines = "\n".join(f"⏳ {m.display_name}" for m in participants)
    embed.add_field(name=S.CREATOR_INITIAL_MEMBERS, value=participant_lines or "—", inline=False)
    embed.set_footer(text=S.CREATOR_INITIAL_FOOTER)
    return embed


def _vote_counts(slots: list[TimeSlot], votes: list[TimeSlotVote]) -> dict[int, int]:
    counts = {s.id: 0 for s in slots}
    for v in votes:
        if v.available:
            counts[v.time_slot_id] += 1
    return counts


def build_status_embed(
    event: Event,
    slots: list[TimeSlot],
    participants: list[Participant],
    votes: list[TimeSlotVote],
    guild: discord.Guild,
) -> discord.Embed:
    total = len(participants) + 1  # +1 for creator
    pending = sum(1 for p in participants if p.status == ParticipantStatus.PENDING)
    color = discord.Color.green() if event.status == EventStatus.CONFIRMED else discord.Color.blurple()

    embed = discord.Embed(title=S.CREATOR_STATUS_TITLE.format(title=event.title), color=color)
    if event.description:
        embed.description = event.description

    status_label = S.CREATOR_STATUS_CONFIRMED if event.status == EventStatus.CONFIRMED else S.CREATOR_STATUS_OPEN
    responded = total - pending
    embed.add_field(name=S.CREATOR_FIELD_STATUS, value=status_label, inline=True)
    embed.add_field(name=S.CREATOR_FIELD_ANSWERS, value=f"{responded}/{total}", inline=True)
    if pending:
        embed.add_field(name=S.CREATOR_FIELD_PENDING, value=str(pending), inline=True)

    counts = _vote_counts(slots, votes)
    for slot_id in counts:
        counts[slot_id] += 1  # Creator always available

    sorted_slots = sorted(slots, key=lambda s: counts[s.id], reverse=True)
    slot_lines = []
    for s in sorted_slots:
        n = counts[s.id]
        icon = "✅" if n == total else ("⚠️" if n > 0 else "❌")
        confirmed = S.CREATOR_SLOT_CONFIRMED if event.confirmed_slot_id == s.id else ""
        slot_lines.append(f"{icon} {s.start_time.strftime('%d.%m.%Y %H:%M')} — {n}/{total}{confirmed}")
    embed.add_field(name=S.CREATOR_FIELD_SLOTS, value="\n".join(slot_lines) or "—", inline=False)

    participant_lines = [S.CREATOR_AUTO_AVAILABLE]
    for p in participants:
        member = guild.get_member(p.user_id)
        name = member.display_name if member else f"<{p.user_id}>"
        participant_lines.append(f"{_STATUS_ICON[p.status]} {name}")
    embed.add_field(name=S.CREATOR_FIELD_MEMBERS, value="\n".join(participant_lines), inline=False)

    return embed


async def fetch_event_data(
    session, event_id: int
) -> tuple[Event, list[TimeSlot], list[Participant], list[TimeSlotVote]]:
    event = await session.get(Event, event_id)
    result = await session.execute(select(TimeSlot).where(TimeSlot.event_id == event_id))
    slots = result.scalars().all()
    result = await session.execute(select(Participant).where(Participant.event_id == event_id))
    participants = result.scalars().all()
    result = await session.execute(select(TimeSlotVote).where(TimeSlotVote.event_id == event_id))
    votes = result.scalars().all()
    return event, slots, participants, votes


async def auto_confirm_if_complete(event_id: int, client: discord.Client) -> None:
    from bot.ical import build_ics

    async with SessionLocal() as session:
        event, slots, participants, votes = await fetch_event_data(session, event_id)

        if event.status != EventStatus.OPEN:
            return

        if any(p.status == ParticipantStatus.PENDING for p in participants):
            return

        counts: dict[int, int] = {s.id: 1 for s in slots}
        for v in votes:
            if v.available:
                counts[v.time_slot_id] += 1

        best_slot = max(slots, key=lambda s: (counts[s.id], -s.start_time.timestamp()))
        event.status = EventStatus.CONFIRMED
        event.confirmed_slot_id = best_slot.id
        await session.commit()

        accepted_ids = [p.user_id for p in participants if p.status == ParticipantStatus.ACCEPTED]
        notify_ids = list({*accepted_ids, event.creator_id})
        event_title = event.title
        event_description = event.description or ""
        best_time = best_slot.start_time
        total = len(participants) + 1
        best_count = counts[best_slot.id]

    final_time = best_time.strftime("%d.%m.%Y um %H:%M Uhr")
    embed = discord.Embed(
        title=S.CONFIRM_EMBED_TITLE.format(title=event_title),
        description=S.CONFIRM_EMBED_DESC.format(time=final_time),
        color=discord.Color.green(),
    )
    if best_count < total:
        embed.add_field(
            name=S.CONFIRM_FIELD_HINT,
            value=S.CONFIRM_NO_PERFECT_SLOT.format(count=best_count, total=total),
            inline=False,
        )
    embed.set_footer(text=S.CONFIRM_FOOTER)

    for user_id in notify_ids:
        try:
            user = await client.fetch_user(user_id)
            ics = build_ics(title=event_title, description=event_description, start=best_time)
            await user.send(embed=embed, file=discord.File(ics, filename="termin.ics"))
        except discord.Forbidden:
            pass


class CreatorView(discord.ui.View):
    def __init__(self, event_id: int) -> None:
        super().__init__(timeout=_SEVEN_DAYS)
        self.event_id = event_id
        self.message: discord.Message | None = None

    async def on_timeout(self) -> None:
        if self.message:
            try:
                await self.message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

    @discord.ui.button(label=S.CREATOR_CANCEL_BUTTON, style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        async with SessionLocal() as session:
            event, _, participants, _ = await fetch_event_data(session, self.event_id)

        if not event or event.creator_id != interaction.user.id:
            await interaction.response.send_message(S.NO_ACCESS, ephemeral=True)
            return
        if event.status != EventStatus.OPEN:
            await interaction.response.send_message(S.ALREADY_DONE, ephemeral=True)
            return

        async with SessionLocal() as session:
            event = await session.get(Event, self.event_id)
            event.status = EventStatus.CANCELLED
            await session.commit()
            event_title = event.title

        embed = discord.Embed(
            title=S.CANCEL_EMBED_TITLE.format(title=event_title),
            description=S.CANCEL_EMBED_DESC,
            color=discord.Color.red(),
        )
        for p in participants:
            try:
                user = await interaction.client.fetch_user(p.user_id)
                await user.send(embed=embed)
            except discord.Forbidden:
                pass

        await interaction.response.edit_message(
            content=S.CANCEL_CONFIRMED.format(title=event_title),
            embed=None,
            view=None,
        )


class ConfirmSlotView(discord.ui.View):
    def __init__(self, event_id: int, slots: list[TimeSlot]) -> None:
        super().__init__(timeout=300)
        self.add_item(ConfirmSlotSelect(event_id=event_id, slots=slots))


class ConfirmSlotSelect(discord.ui.Select):
    def __init__(self, event_id: int, slots: list[TimeSlot]) -> None:
        options = [
            discord.SelectOption(
                label=s.start_time.strftime("%d.%m.%Y %H:%M"),
                value=str(s.id),
            )
            for s in slots
        ]
        super().__init__(placeholder=S.DATE_PLACEHOLDER, options=options)
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction) -> None:
        slot_id = int(self.values[0])

        async with SessionLocal() as session:
            event, _, participants, _ = await fetch_event_data(session, self.event_id)
            slot = await session.get(TimeSlot, slot_id)
            event.status = EventStatus.CONFIRMED
            event.confirmed_slot_id = slot_id
            await session.commit()

            notify_ids = list({
                *(p.user_id for p in participants if p.status == ParticipantStatus.ACCEPTED),
                event.creator_id,
            })
            event_title = event.title
            event_description = event.description or ""

        from bot.ical import build_ics

        final_time = slot.start_time.strftime("%d.%m.%Y um %H:%M Uhr")
        embed = discord.Embed(
            title=S.CONFIRM_EMBED_TITLE.format(title=event_title),
            description=S.CONFIRM_EMBED_DESC.format(time=final_time),
            color=discord.Color.green(),
        )
        embed.set_footer(text=S.CONFIRM_FOOTER)

        for user_id in notify_ids:
            try:
                user = await interaction.client.fetch_user(user_id)
                ics = build_ics(title=event_title, description=event_description, start=slot.start_time)
                await user.send(embed=embed, file=discord.File(ics, filename="termin.ics"))
            except discord.Forbidden:
                pass

        await interaction.response.edit_message(
            content=S.CONFIRM_SUCCESS.format(title=event_title, time=final_time),
            view=None,
        )
