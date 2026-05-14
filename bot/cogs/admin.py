import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from bot.database.db import SessionLocal
from bot.database.models import AppointmentType, Event, EventStatus, ServerConfig


def _require_manage_guild():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "Du benötigst die Berechtigung 'Server verwalten'.", ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    timely = app_commands.Group(name="timely", description="Timely Bot Commands")

    # ── Admin commands ─────────────────────────────────────────────────────────

    @timely.command(name="setup", description="Setzt diesen Channel als Panel-Channel")
    @_require_manage_guild()
    async def setup(self, interaction: discord.Interaction) -> None:
        async with SessionLocal() as session:
            config = await session.get(ServerConfig, interaction.guild_id)
            if config is None:
                config = ServerConfig(guild_id=interaction.guild_id)
                session.add(config)
            config.panel_channel_id = interaction.channel_id
            await session.commit()

        await interaction.response.send_message(
            f"Panel-Channel auf {interaction.channel.mention} gesetzt.", ephemeral=True
        )

    @timely.command(name="add_type", description="Füge einen Termintyp (Panel-Button) hinzu")
    @_require_manage_guild()
    @app_commands.describe(
        label="Button-Bezeichnung (z.B. 'Team-Meeting')",
        creator_role="Nur Nutzer mit dieser Rolle dürfen diesen Button nutzen (optional)",
        invitee_role="Nur Nutzer mit dieser Rolle können eingeladen werden (optional)",
    )
    async def add_type(
        self,
        interaction: discord.Interaction,
        label: str,
        creator_role: discord.Role | None = None,
        invitee_role: discord.Role | None = None,
    ) -> None:
        async with SessionLocal() as session:
            config = await session.get(ServerConfig, interaction.guild_id)
            if config is None:
                await interaction.response.send_message(
                    "Bitte zuerst `/timely setup` ausführen.", ephemeral=True
                )
                return

            apt = AppointmentType(
                guild_id=interaction.guild_id,
                label=label,
                required_creator_role_id=creator_role.id if creator_role else None,
                restrict_invitees_to_role_id=invitee_role.id if invitee_role else None,
            )
            session.add(apt)
            await session.commit()

        parts = [f"Termintyp **{label}** hinzugefügt."]
        if creator_role:
            parts.append(f"Ersteller-Rolle: {creator_role.mention}")
        if invitee_role:
            parts.append(f"Einladbare Rolle: {invitee_role.mention}")
        await interaction.response.send_message("\n".join(parts), ephemeral=True)

    @timely.command(name="post_panel", description="Poste das Panel mit allen Termintypen")
    @_require_manage_guild()
    async def post_panel(self, interaction: discord.Interaction) -> None:
        from bot.views.panel_view import build_panel

        async with SessionLocal() as session:
            config = await session.get(ServerConfig, interaction.guild_id)
            if config is None or not config.panel_channel_id:
                await interaction.response.send_message(
                    "Kein Panel-Channel konfiguriert. Bitte zuerst `/timely setup`.", ephemeral=True
                )
                return

            result = await session.execute(
                select(AppointmentType).where(AppointmentType.guild_id == interaction.guild_id)
            )
            types = result.scalars().all()

        if not types:
            await interaction.response.send_message(
                "Keine Termintypen vorhanden. Bitte zuerst `/timely add_type`.", ephemeral=True
            )
            return

        channel = interaction.guild.get_channel(config.panel_channel_id)
        embed, view = build_panel(list(types))
        msg = await channel.send(embed=embed, view=view)

        async with SessionLocal() as session:
            config = await session.get(ServerConfig, interaction.guild_id)
            config.panel_message_id = msg.id
            await session.commit()

        await interaction.response.send_message("Panel gepostet.", ephemeral=True)

    @timely.command(name="remove_type", description="Entferne einen Termintyp")
    @_require_manage_guild()
    @app_commands.describe(label="Bezeichnung des zu entfernenden Termintyps")
    async def remove_type(self, interaction: discord.Interaction, label: str) -> None:
        from sqlalchemy import delete

        async with SessionLocal() as session:
            result = await session.execute(
                select(AppointmentType).where(
                    AppointmentType.guild_id == interaction.guild_id,
                    AppointmentType.label == label,
                )
            )
            apt = result.scalar_one_or_none()
            if apt is None:
                await interaction.response.send_message(
                    f"Kein Termintyp mit der Bezeichnung **{label}** gefunden.", ephemeral=True
                )
                return
            await session.delete(apt)
            await session.commit()

        await interaction.response.send_message(
            f"Termintyp **{label}** entfernt. Nutze `/timely refresh_panel` um das Panel zu aktualisieren.",
            ephemeral=True,
        )

    @timely.command(name="refresh_panel", description="Panel löschen und neu posten")
    @_require_manage_guild()
    async def refresh_panel(self, interaction: discord.Interaction) -> None:
        from bot.views.panel_view import build_panel

        async with SessionLocal() as session:
            config = await session.get(ServerConfig, interaction.guild_id)
            if config is None or not config.panel_channel_id:
                await interaction.response.send_message(
                    "Kein Panel-Channel konfiguriert. Bitte zuerst `/timely setup`.", ephemeral=True
                )
                return

            result = await session.execute(
                select(AppointmentType).where(AppointmentType.guild_id == interaction.guild_id)
            )
            types = result.scalars().all()

        channel = interaction.guild.get_channel(config.panel_channel_id)

        # Delete old panel message if we have the ID
        if config.panel_message_id:
            try:
                old_msg = await channel.fetch_message(config.panel_message_id)
                await old_msg.delete()
            except discord.NotFound:
                pass

        if not types:
            await interaction.response.send_message(
                "Keine Termintypen vorhanden. Panel wurde gelöscht.", ephemeral=True
            )
            return

        embed, view = build_panel(list(types))
        msg = await channel.send(embed=embed, view=view)

        async with SessionLocal() as session:
            config = await session.get(ServerConfig, interaction.guild_id)
            config.panel_message_id = msg.id
            await session.commit()

        await interaction.response.send_message("Panel aktualisiert.", ephemeral=True)

    # ── User commands ──────────────────────────────────────────────────────────

    @timely.command(name="status", description="Zeige den Status deiner offenen Termine")
    async def status(self, interaction: discord.Interaction) -> None:
        from bot.views.creator_view import CreatorView, build_status_embed, fetch_event_data

        async with SessionLocal() as session:
            result = await session.execute(
                select(Event).where(
                    Event.guild_id == interaction.guild_id,
                    Event.creator_id == interaction.user.id,
                    Event.status == EventStatus.OPEN,
                )
            )
            events = result.scalars().all()

            if not events:
                await interaction.response.send_message(
                    "Du hast keine offenen Termine.", ephemeral=True
                )
                return

            if len(events) == 1:
                event, slots, participants, votes = await fetch_event_data(session, events[0].id)
                embed = build_status_embed(event, list(slots), list(participants), list(votes), interaction.guild)
                view = CreatorView(event_id=event.id)
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                # Multiple open events — let creator pick one
                view = EventPickerView(list(events))
                await interaction.response.send_message(
                    "Du hast mehrere offene Termine. Wähle einen aus:", view=view, ephemeral=True
                )


    @timely.command(name="remind", description="Schicke eine Erinnerungs-DM an alle, die noch nicht geantwortet haben")
    async def remind(self, interaction: discord.Interaction) -> None:
        from bot.database.models import Participant, ParticipantStatus
        from bot.views.vote_view import build_vote_message
        from bot.views.creator_view import fetch_event_data

        async with SessionLocal() as session:
            result = await session.execute(
                select(Event).where(
                    Event.guild_id == interaction.guild_id,
                    Event.creator_id == interaction.user.id,
                    Event.status == EventStatus.OPEN,
                )
            )
            events = result.scalars().all()

        if not events:
            await interaction.response.send_message("Du hast keine offenen Termine.", ephemeral=True)
            return

        if len(events) > 1:
            await interaction.response.send_message(
                "Du hast mehrere offene Termine. Wähle einen aus:",
                view=RemindPickerView(list(events)),
                ephemeral=True,
            )
            return

        await _send_reminders(interaction, events[0].id)


async def _send_reminders(interaction: discord.Interaction, event_id: int) -> None:
    from bot.database.models import Participant, ParticipantStatus
    from bot.views.vote_view import build_vote_message
    from bot.views.creator_view import fetch_event_data

    async with SessionLocal() as session:
        event, slots, participants, _ = await fetch_event_data(session, event_id)

    pending = [p for p in participants if p.status == ParticipantStatus.PENDING]

    if not pending:
        await interaction.response.send_message(
            "Alle Teilnehmer haben bereits geantwortet.", ephemeral=True
        )
        return

    sent, failed = 0, []
    for p in pending:
        try:
            user = await interaction.client.fetch_user(p.user_id)
            embed, view = build_vote_message(event, list(slots), interaction.user)
            await user.send(content="Erinnerung: Du hast noch nicht auf diese Termineinladung geantwortet.", embed=embed, view=view)
            sent += 1
        except discord.Forbidden:
            failed.append(str(p.user_id))

    msg = f"Erinnerung an **{sent}** Teilnehmer gesendet."
    if failed:
        msg += f"\nFolgende Nutzer konnten nicht erreicht werden: {', '.join(failed)}"

    if not interaction.response.is_done():
        await interaction.response.send_message(msg, ephemeral=True)
    else:
        await interaction.followup.send(msg, ephemeral=True)


class RemindPickerView(discord.ui.View):
    def __init__(self, events: list[Event]) -> None:
        super().__init__(timeout=120)
        self.add_item(RemindPickerSelect(events))


class RemindPickerSelect(discord.ui.Select):
    def __init__(self, events: list[Event]) -> None:
        options = [
            discord.SelectOption(label=e.title[:100], value=str(e.id))
            for e in events[:25]
        ]
        super().__init__(placeholder="Termin auswählen...", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        await _send_reminders(interaction, int(self.values[0]))


class EventPickerView(discord.ui.View):
    def __init__(self, events: list[Event]) -> None:
        super().__init__(timeout=120)
        self.add_item(EventPickerSelect(events))


class EventPickerSelect(discord.ui.Select):
    def __init__(self, events: list[Event]) -> None:
        options = [
            discord.SelectOption(label=e.title[:100], value=str(e.id))
            for e in events[:25]
        ]
        super().__init__(placeholder="Termin auswählen...", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        from bot.views.creator_view import CreatorView, build_status_embed, fetch_event_data

        event_id = int(self.values[0])
        async with SessionLocal() as session:
            event, slots, participants, votes = await fetch_event_data(session, event_id)

        embed = build_status_embed(event, list(slots), list(participants), list(votes), interaction.guild)
        view = CreatorView(event_id=event_id)
        await interaction.response.edit_message(content=None, embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
