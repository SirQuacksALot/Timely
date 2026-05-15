"""Background task for cleaning up expired DMs."""
import logging
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks
from sqlalchemy import select

from bot.database.db import SessionLocal
from bot.database.models import Event, Participant

log = logging.getLogger(__name__)

_EXPIRY_DAYS = 7


async def _delete_message(bot: commands.Bot, user_id: int, message_id: int) -> None:
    """Fetch and delete a DM message, ignoring expected Discord errors."""
    user = await bot.fetch_user(user_id)
    channel = await user.create_dm()
    msg = await channel.fetch_message(message_id)
    await msg.delete()


class VotingCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cleanup_expired_dms.start()

    def cog_unload(self) -> None:
        self.cleanup_expired_dms.cancel()

    @tasks.loop(hours=1)
    async def cleanup_expired_dms(self) -> None:
        cutoff = datetime.utcnow() - timedelta(days=_EXPIRY_DAYS)

        async with SessionLocal() as session:
            # Participant DMs
            result = await session.execute(
                select(Participant)
                .join(Event)
                .where(
                    Participant.dm_message_id.isnot(None),
                    Event.created_at < cutoff,
                )
            )
            for p in result.scalars().all():
                try:
                    await _delete_message(self.bot, p.user_id, p.dm_message_id)
                except (discord.NotFound, discord.Forbidden):
                    pass  # Message already deleted or user blocked DMs
                except discord.HTTPException as e:
                    log.warning("Failed to delete participant DM %s: %s", p.dm_message_id, e)
                p.dm_message_id = None
                p.dm_channel_id = None

            # Creator DMs
            result = await session.execute(
                select(Event).where(
                    Event.creator_dm_message_id.isnot(None),
                    Event.created_at < cutoff,
                )
            )
            for e in result.scalars().all():
                try:
                    await _delete_message(self.bot, e.creator_id, e.creator_dm_message_id)
                except (discord.NotFound, discord.Forbidden):
                    pass  # Message already deleted or user blocked DMs
                except discord.HTTPException as ex:
                    log.warning("Failed to delete creator DM %s: %s", e.creator_dm_message_id, ex)
                e.creator_dm_message_id = None
                e.creator_dm_channel_id = None

            await session.commit()

    @cleanup_expired_dms.before_loop
    async def before_cleanup(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VotingCog(bot))
