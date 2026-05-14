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

_STATUS_ICON = {
    ParticipantStatus.PENDING: "⏳",
    ParticipantStatus.ACCEPTED: "✅",
    ParticipantStatus.DECLINED: "❌",
}


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
    total = len(participants)
    pending = sum(1 for p in participants if p.status == ParticipantStatus.PENDING)
    color = discord.Color.green() if event.status == EventStatus.CONFIRMED else discord.Color.blurple()

    embed = discord.Embed(title=f"📅 {event.title}", color=color)
    if event.description:
        embed.description = event.description

    status_label = "✅ Bestätigt" if event.status == EventStatus.CONFIRMED else "🔄 Offen"
    responded = total - pending
    embed.add_field(name="Status", value=status_label, inline=True)
    embed.add_field(name="Antworten", value=f"{responded}/{total}", inline=True)
    if pending:
        embed.add_field(name="Ausstehend", value=str(pending), inline=True)

    counts = _vote_counts(slots, votes)
    sorted_slots = sorted(slots, key=lambda s: counts[s.id], reverse=True)
    slot_lines = []
    for s in sorted_slots:
        n = counts[s.id]
        icon = "✅" if n == total else ("⚠️" if n > 0 else "❌")
        confirmed = " ← bestätigt" if event.confirmed_slot_id == s.id else ""
        slot_lines.append(f"{icon} {s.start_time.strftime('%d.%m.%Y %H:%M')} — {n}/{total}{confirmed}")
    embed.add_field(name="Zeitvorschläge", value="\n".join(slot_lines) or "—", inline=False)

    participant_lines = []
    for p in participants:
        member = guild.get_member(p.user_id)
        name = member.display_name if member else f"<{p.user_id}>"
        participant_lines.append(f"{_STATUS_ICON[p.status]} {name}")
    embed.add_field(name="Teilnehmer", value="\n".join(participant_lines) or "—", inline=False)

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


class CreatorView(discord.ui.View):
    def __init__(self, event_id: int) -> None:
        super().__init__(timeout=None)
        self.event_id = event_id

    @discord.ui.button(label="Termin bestätigen", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        async with SessionLocal() as session:
            event, slots, _, _ = await fetch_event_data(session, self.event_id)

        if not event or event.creator_id != interaction.user.id:
            await interaction.response.send_message("Kein Zugriff.", ephemeral=True)
            return
        if event.status != EventStatus.OPEN:
            await interaction.response.send_message("Dieser Termin ist bereits bestätigt.", ephemeral=True)
            return

        await interaction.response.send_message(
            "Wähle den finalen Zeitslot:",
            view=ConfirmSlotView(event_id=self.event_id, slots=list(slots)),
            ephemeral=True,
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
        super().__init__(placeholder="Finalen Slot wählen...", options=options)
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction) -> None:
        slot_id = int(self.values[0])

        async with SessionLocal() as session:
            event, _, participants, _ = await fetch_event_data(session, self.event_id)
            slot = await session.get(TimeSlot, slot_id)

            event.status = EventStatus.CONFIRMED
            event.confirmed_slot_id = slot_id
            await session.commit()

            accepted_ids = [
                p.user_id for p in participants if p.status == ParticipantStatus.ACCEPTED
            ]
            event_title = event.title

        from bot.ical import build_ics

        final_time = slot.start_time.strftime("%d.%m.%Y um %H:%M Uhr")
        embed = discord.Embed(
            title=f"📅 Termin bestätigt: {event_title}",
            description=f"Der finale Termin steht fest:\n**{final_time}**",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Die .ics Datei im Anhang kannst du direkt in deinen Kalender importieren.")

        failed: list[str] = []
        for user_id in accepted_ids:
            try:
                user = await interaction.client.fetch_user(user_id)
                ics = build_ics(
                    title=event_title,
                    description=event.description or "",
                    start=slot.start_time,
                )
                await user.send(
                    embed=embed,
                    file=discord.File(ics, filename="termin.ics"),
                )
            except discord.Forbidden:
                failed.append(str(user_id))

        msg = f"Termin **{event_title}** auf **{final_time}** bestätigt. Alle Teilnehmer wurden informiert."
        if failed:
            msg += f"\nFolgende Nutzer konnten nicht per DM erreicht werden: {', '.join(failed)}"
        await interaction.response.edit_message(content=msg, view=None)
