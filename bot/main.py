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


class TimelyBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await init_db()
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
