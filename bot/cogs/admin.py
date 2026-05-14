import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from bot.database.db import SessionLocal
from bot.database.models import AppointmentType, Event, EventStatus, Panel, ServerConfig
from bot.strings import S


def _require_manage_guild():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "Du benötigst die Berechtigung 'Server verwalten'.", ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)


async def _panel_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Panel).where(Panel.guild_id == interaction.guild_id)
        )
        panels = result.scalars().all()
    return [
        app_commands.Choice(name=p.name, value=p.name)
        for p in panels
        if current.lower() in p.name.lower()
    ][:25]


async def _get_panel(session, guild_id: int, name: str) -> Panel | None:
    result = await session.execute(
        select(Panel).where(Panel.guild_id == guild_id, Panel.name == name)
    )
    return result.scalar_one_or_none()


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    timely = app_commands.Group(name="timely", description="Timely Bot Commands")

    # ── Panel Management ───────────────────────────────────────────────────────

    @timely.command(name="create_panel", description="Erstelle ein neues Panel im aktuellen Channel")
    @_require_manage_guild()
    @app_commands.describe(name="Name des Panels (z.B. 'Intern' oder 'Events')")
    async def create_panel(self, interaction: discord.Interaction, name: str) -> None:
        async with SessionLocal() as session:
            config = await session.get(ServerConfig, interaction.guild_id)
            if config is None:
                config = ServerConfig(guild_id=interaction.guild_id)
                session.add(config)
                await session.flush()

            existing = await _get_panel(session, interaction.guild_id, name)
            if existing:
                await interaction.response.send_message(
                    f"Ein Panel mit dem Namen **{name}** existiert bereits.", ephemeral=True
                )
                return

            panel = Panel(
                guild_id=interaction.guild_id,
                name=name,
                channel_id=interaction.channel_id,
            )
            session.add(panel)
            await session.commit()

        await interaction.response.send_message(
            f"Panel **{name}** in {interaction.channel.mention} erstellt.\n"
            f"Füge Buttons hinzu mit `/timely add_type panel:{name} label:...`",
            ephemeral=True,
        )

    @timely.command(name="delete_panel", description="Panel und alle zugehörigen Buttons löschen")
    @_require_manage_guild()
    @app_commands.describe(name="Name des Panels")
    @app_commands.autocomplete(name=_panel_autocomplete)
    async def delete_panel(self, interaction: discord.Interaction, name: str) -> None:
        async with SessionLocal() as session:
            panel = await _get_panel(session, interaction.guild_id, name)
            if panel is None:
                await interaction.response.send_message(
                    f"Panel **{name}** nicht gefunden.", ephemeral=True
                )
                return

            channel_id = panel.channel_id
            message_id = panel.message_id
            await session.delete(panel)
            await session.commit()

        if channel_id and message_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                try:
                    msg = await channel.fetch_message(message_id)
                    await msg.delete()
                except discord.NotFound:
                    pass

        await interaction.response.send_message(
            f"Panel **{name}** und alle zugehörigen Buttons wurden gelöscht.", ephemeral=True
        )

    @timely.command(name="list_panels", description="Zeige alle konfigurierten Panels")
    @_require_manage_guild()
    async def list_panels(self, interaction: discord.Interaction) -> None:
        async with SessionLocal() as session:
            result = await session.execute(
                select(Panel).where(Panel.guild_id == interaction.guild_id)
            )
            panels = result.scalars().all()

        if not panels:
            await interaction.response.send_message("Keine Panels konfiguriert.", ephemeral=True)
            return

        embed = discord.Embed(title="Konfigurierte Panels", color=discord.Color.blurple())
        for p in panels:
            channel = f"<#{p.channel_id}>" if p.channel_id else "—"
            posted = "✅ Gepostet" if p.message_id else "⏳ Nicht gepostet"
            embed.add_field(
                name=f"**{p.name}**",
                value=f"Channel: {channel}\nStatus: {posted}",
                inline=True,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Appointment Type Management ────────────────────────────────────────────

    @timely.command(name="add_type", description="Füge einen Button zu einem Panel hinzu")
    @_require_manage_guild()
    @app_commands.describe(
        panel="Name des Panels",
        label="Button-Bezeichnung (z.B. 'Team-Meeting')",
        nur_ersteller_mit_rolle="Nur Nutzer mit dieser Rolle dürfen diesen Button nutzen (optional)",
        nur_diese_rolle_einladen="Eingeladene Teilnehmer müssen diese Rolle haben (optional)",
    )
    @app_commands.autocomplete(panel=_panel_autocomplete)
    async def add_type(
        self,
        interaction: discord.Interaction,
        panel: str,
        label: str,
        nur_ersteller_mit_rolle: discord.Role | None = None,
        nur_diese_rolle_einladen: discord.Role | None = None,
    ) -> None:
        async with SessionLocal() as session:
            db_panel = await _get_panel(session, interaction.guild_id, panel)
            if db_panel is None:
                await interaction.response.send_message(
                    f"Panel **{panel}** nicht gefunden. Erstelle es zuerst mit `/timely create_panel`.",
                    ephemeral=True,
                )
                return

            apt = AppointmentType(
                panel_id=db_panel.id,
                guild_id=interaction.guild_id,
                label=label,
                required_creator_role_id=nur_ersteller_mit_rolle.id if nur_ersteller_mit_rolle else None,
                restrict_invitees_to_role_id=nur_diese_rolle_einladen.id if nur_diese_rolle_einladen else None,
            )
            session.add(apt)
            await session.commit()

        parts = [f"Button **{label}** zu Panel **{panel}** hinzugefügt."]
        if nur_ersteller_mit_rolle:
            parts.append(f"Ersteller-Rolle: {nur_ersteller_mit_rolle.mention}")
        if nur_diese_rolle_einladen:
            parts.append(f"Einladbare Rolle: {nur_diese_rolle_einladen.mention}")
        await interaction.response.send_message("\n".join(parts), ephemeral=True)

    @timely.command(name="remove_type", description="Entferne einen Button aus einem Panel")
    @_require_manage_guild()
    @app_commands.describe(panel="Name des Panels", label="Bezeichnung des Buttons")
    @app_commands.autocomplete(panel=_panel_autocomplete)
    async def remove_type(self, interaction: discord.Interaction, panel: str, label: str) -> None:
        async with SessionLocal() as session:
            db_panel = await _get_panel(session, interaction.guild_id, panel)
            if db_panel is None:
                await interaction.response.send_message(f"Panel **{panel}** nicht gefunden.", ephemeral=True)
                return

            result = await session.execute(
                select(AppointmentType).where(
                    AppointmentType.panel_id == db_panel.id,
                    AppointmentType.label == label,
                )
            )
            apt = result.scalar_one_or_none()
            if apt is None:
                await interaction.response.send_message(
                    f"Kein Button **{label}** in Panel **{panel}** gefunden.", ephemeral=True
                )
                return
            await session.delete(apt)
            await session.commit()

        await interaction.response.send_message(
            f"Button **{label}** aus Panel **{panel}** entfernt. "
            f"Nutze `/timely refresh_panel panel:{panel}` um das Panel zu aktualisieren.",
            ephemeral=True,
        )

    @timely.command(name="list_types", description="Zeige alle Buttons eines Panels")
    @_require_manage_guild()
    @app_commands.describe(panel="Name des Panels")
    @app_commands.autocomplete(panel=_panel_autocomplete)
    async def list_types(self, interaction: discord.Interaction, panel: str) -> None:
        async with SessionLocal() as session:
            db_panel = await _get_panel(session, interaction.guild_id, panel)
            if db_panel is None:
                await interaction.response.send_message(f"Panel **{panel}** nicht gefunden.", ephemeral=True)
                return

            result = await session.execute(
                select(AppointmentType).where(AppointmentType.panel_id == db_panel.id)
            )
            types = result.scalars().all()

        if not types:
            await interaction.response.send_message(
                f"Panel **{panel}** hat noch keine Buttons.", ephemeral=True
            )
            return

        embed = discord.Embed(title=f"Buttons in Panel '{panel}'", color=discord.Color.blurple())
        for apt in types:
            creator_role = f"<@&{apt.required_creator_role_id}>" if apt.required_creator_role_id else "Alle"
            invitee_role = f"<@&{apt.restrict_invitees_to_role_id}>" if apt.restrict_invitees_to_role_id else "Alle"
            embed.add_field(
                name=f"**{apt.label}**",
                value=f"Button nutzbar für: {creator_role}\nEinladbar: {invitee_role}",
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Panel Posting ──────────────────────────────────────────────────────────

    @timely.command(name="post_panel", description="Panel in seinem Channel posten")
    @_require_manage_guild()
    @app_commands.describe(panel="Name des Panels")
    @app_commands.autocomplete(panel=_panel_autocomplete)
    async def post_panel(self, interaction: discord.Interaction, panel: str) -> None:
        await self._post_or_refresh(interaction, panel, refresh=False)

    @timely.command(name="refresh_panel", description="Panel löschen und neu posten")
    @_require_manage_guild()
    @app_commands.describe(panel="Name des Panels")
    @app_commands.autocomplete(panel=_panel_autocomplete)
    async def refresh_panel(self, interaction: discord.Interaction, panel: str) -> None:
        await self._post_or_refresh(interaction, panel, refresh=True)

    async def _post_or_refresh(
        self, interaction: discord.Interaction, panel_name: str, refresh: bool
    ) -> None:
        from bot.views.panel_view import build_panel

        async with SessionLocal() as session:
            db_panel = await _get_panel(session, interaction.guild_id, panel_name)
            if db_panel is None:
                await interaction.response.send_message(
                    f"Panel **{panel_name}** nicht gefunden.", ephemeral=True
                )
                return
            if not db_panel.channel_id:
                await interaction.response.send_message(
                    f"Panel **{panel_name}** hat keinen Channel.", ephemeral=True
                )
                return

            result = await session.execute(
                select(AppointmentType).where(AppointmentType.panel_id == db_panel.id)
            )
            types = result.scalars().all()

        channel = interaction.guild.get_channel(db_panel.channel_id)

        if refresh and db_panel.message_id:
            try:
                old_msg = await channel.fetch_message(db_panel.message_id)
                await old_msg.delete()
            except discord.NotFound:
                pass

        if not types:
            await interaction.response.send_message(
                f"Panel **{panel_name}** hat keine Buttons. Füge welche hinzu mit `/timely add_type`.",
                ephemeral=True,
            )
            return

        embed, view = build_panel(panel_name, list(types))
        msg = await channel.send(embed=embed, view=view)

        async with SessionLocal() as session:
            db_panel = await _get_panel(session, interaction.guild_id, panel_name)
            db_panel.message_id = msg.id
            await session.commit()

        action = "aktualisiert" if refresh else "gepostet"
        await interaction.response.send_message(f"Panel **{panel_name}** {action}.", ephemeral=True)

    # ── Announce ───────────────────────────────────────────────────────────────

    @timely.command(name="announce", description="Post a formatted info message in this channel")
    @_require_manage_guild()
    async def announce(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(AnnounceModal(channel=interaction.channel))

    # ── User Commands ──────────────────────────────────────────────────────────

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
                view = EventPickerView(list(events))
                await interaction.response.send_message(
                    "Du hast mehrere offene Termine. Wähle einen aus:", view=view, ephemeral=True
                )

    @timely.command(name="remind", description="Sende Erinnerungs-DM an alle ausstehenden Teilnehmer")
    async def remind(self, interaction: discord.Interaction) -> None:
        from bot.views.creator_view import fetch_event_data
        from bot.views.vote_view import build_vote_message

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
    from bot.views.creator_view import fetch_event_data
    from bot.views.vote_view import build_vote_message

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
            msg = await user.send(
                content="Erinnerung: Du hast noch nicht auf diese Terminanfrage geantwortet.",
                embed=embed,
                view=view,
            )
            view.message = msg
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


class AnnounceModal(discord.ui.Modal):
    announce_title = discord.ui.TextInput(
        label=S.ANNOUNCE_FIELD_TITLE,
        placeholder=S.ANNOUNCE_FIELD_TITLE_PH,
        max_length=200,
    )
    body = discord.ui.TextInput(
        label=S.ANNOUNCE_FIELD_BODY,
        placeholder=S.ANNOUNCE_FIELD_BODY_PH,
        style=discord.TextStyle.paragraph,
        max_length=2000,
    )

    def __init__(self, channel: discord.TextChannel) -> None:
        super().__init__(title=S.ANNOUNCE_MODAL_TITLE)
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title=self.announce_title.value,
            description=self.body.value,
            color=discord.Color.blurple(),
        )
        await self.channel.send(embed=embed)
        await interaction.response.send_message(
            S.ANNOUNCE_SENT.format(channel=self.channel.mention), ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
