import asyncio
import logging

import discord
from discord.ext import commands

from bot.config import DISCORD_TOKEN
from bot.database.db import init_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

COGS = [
    "bot.cogs.admin",
    "bot.cogs.events",
    "bot.cogs.voting",
]


async def restore_views(bot: "TimelyBot") -> None:
    """Re-register all persistent views after a restart."""
    from sqlalchemy import select

    from bot.database.db import SessionLocal
    from bot.database.models import AppointmentType, Event, EventStatus, Panel, TimeSlot
    from bot.views.creator_view import CreatorView
    from bot.views.panel_view import PanelView
    from bot.views.vote_view import VoteView

    async with SessionLocal() as session:
        result = await session.execute(select(Panel).where(Panel.message_id.isnot(None)))
        panels = result.scalars().all()
        panel_count = 0
        for panel in panels:
            result = await session.execute(
                select(AppointmentType).where(AppointmentType.panel_id == panel.id)
            )
            types = result.scalars().all()
            if types:
                bot.add_view(PanelView(list(types)))
                panel_count += 1

        result = await session.execute(select(Event).where(Event.status == EventStatus.OPEN))
        events = result.scalars().all()
        event_count = len(events)
        for event in events:
            result = await session.execute(
                select(TimeSlot).where(TimeSlot.event_id == event.id)
            )
            slots = result.scalars().all()
            if slots:
                bot.add_view(VoteView(event_id=event.id, slots=list(slots)))
            bot.add_view(CreatorView(event_id=event.id))

    log.info("Restored %d panel view(s) and %d event view(s).", panel_count, event_count)


class TimelyBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await init_db()
        await restore_views(self)
        for cog in COGS:
            await self.load_extension(cog)
        await self.tree.sync()
        log.info("Slash commands synced.")

    async def on_ready(self) -> None:
        log.info("Timely is online as %s (ID: %s)", self.user, self.user.id)


async def main() -> None:
    async with TimelyBot() as bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
