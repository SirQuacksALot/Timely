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
            await interaction.response.send_message(S.NO_PERMISSION_GUILD, ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)


async def _type_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    panel_name = getattr(interaction.namespace, "panel", None)
    if not panel_name:
        return []
    async with SessionLocal() as session:
        db_panel = await _get_panel(session, interaction.guild_id, panel_name)
        if not db_panel:
            return []
        result = await session.execute(
            select(AppointmentType).where(AppointmentType.panel_id == db_panel.id)
        )
        types = result.scalars().all()
    return [
        app_commands.Choice(name=t.label, value=t.label)
        for t in types
        if current.lower() in t.label.lower()
    ][:25]


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

    @timely.command(name="create_panel", description="Create a new panel in the current channel")
    @_require_manage_guild()
    @app_commands.describe(name="Panel name (e.g. 'Internal' or 'Events')")
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
                    S.PANEL_ALREADY_EXISTS.format(name=name), ephemeral=True
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
            S.PANEL_CREATED.format(name=name, channel=interaction.channel.mention),
            ephemeral=True,
        )

    @timely.command(name="delete_panel", description="Delete a panel and all its buttons")
    @_require_manage_guild()
    @app_commands.describe(name="Name of the panel")
    @app_commands.autocomplete(name=_panel_autocomplete)
    async def delete_panel(self, interaction: discord.Interaction, name: str) -> None:
        async with SessionLocal() as session:
            panel = await _get_panel(session, interaction.guild_id, name)
            if panel is None:
                await interaction.response.send_message(S.PANEL_NOT_FOUND.format(name=name), ephemeral=True)
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

        await interaction.response.send_message(S.PANEL_DELETED.format(name=name), ephemeral=True)

    @timely.command(name="list_panels", description="Show all configured panels")
    @_require_manage_guild()
    async def list_panels(self, interaction: discord.Interaction) -> None:
        async with SessionLocal() as session:
            result = await session.execute(
                select(Panel).where(Panel.guild_id == interaction.guild_id)
            )
            panels = result.scalars().all()

        if not panels:
            await interaction.response.send_message(S.NO_PANELS, ephemeral=True)
            return

        embed = discord.Embed(title=S.PANELS_TITLE, color=discord.Color.blurple())
        for p in panels:
            channel = f"<#{p.channel_id}>" if p.channel_id else "—"
            posted = "✅ Posted" if p.message_id else "⏳ Not posted"
            active = "🟢 Active" if p.active else "🔴 Disabled"
            embed.add_field(
                name=f"**{p.name}**",
                value=f"Channel: {channel}\nPosted: {posted}\nStatus: {active}",
                inline=True,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Appointment Type Management ────────────────────────────────────────────

    @timely.command(name="add_type", description="Add a button to a panel")
    @_require_manage_guild()
    @app_commands.describe(
        panel="Name of the panel",
        label="Button label (e.g. 'Team Meeting')",
        creator_role="Only users with this role may use this button (optional)",
        invitee_role="Invitees must have this role (optional)",
        max_requests="Max simultaneous open requests per user (default: 1)",
    )
    @app_commands.autocomplete(panel=_panel_autocomplete)
    async def add_type(
        self,
        interaction: discord.Interaction,
        panel: str,
        label: str,
        creator_role: discord.Role | None = None,
        invitee_role: discord.Role | None = None,
        max_requests: int = 1,
    ) -> None:
        async with SessionLocal() as session:
            db_panel = await _get_panel(session, interaction.guild_id, panel)
            if db_panel is None:
                await interaction.response.send_message(
                    S.PANEL_NOT_FOUND_USE_CREATE.format(panel=panel), ephemeral=True
                )
                return

            apt = AppointmentType(
                panel_id=db_panel.id,
                guild_id=interaction.guild_id,
                label=label,
                required_creator_role_id=creator_role.id if creator_role else None,
                restrict_invitees_to_role_id=invitee_role.id if invitee_role else None,
                max_concurrent_requests=max(1, max_requests),
            )
            session.add(apt)
            await session.commit()

        parts = [S.TYPE_ADDED.format(label=label, panel=panel)]
        if creator_role:
            parts.append(S.TYPE_ADDED_CREATOR_ROLE.format(role=creator_role.mention))
        if invitee_role:
            parts.append(S.TYPE_ADDED_INVITEE_ROLE.format(role=invitee_role.mention))
        await interaction.response.send_message("\n".join(parts), ephemeral=True)

    @timely.command(name="remove_type", description="Remove a button from a panel")
    @_require_manage_guild()
    @app_commands.describe(panel="Name of the panel", label="Button label")
    @app_commands.autocomplete(panel=_panel_autocomplete)
    async def remove_type(self, interaction: discord.Interaction, panel: str, label: str) -> None:
        async with SessionLocal() as session:
            db_panel = await _get_panel(session, interaction.guild_id, panel)
            if db_panel is None:
                await interaction.response.send_message(S.PANEL_NOT_FOUND.format(name=panel), ephemeral=True)
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
                    S.TYPE_NOT_FOUND.format(label=label, panel=panel), ephemeral=True
                )
                return
            await session.delete(apt)
            await session.commit()

        await interaction.response.send_message(
            S.TYPE_REMOVED.format(label=label, panel=panel), ephemeral=True
        )

    @timely.command(name="edit_type", description="Edit an existing appointment type button")
    @_require_manage_guild()
    @app_commands.describe(
        panel="Panel containing the button",
        label="Current button label",
        new_label="New label (leave empty to keep current)",
        creator_role="Update creator role restriction (use @everyone to clear)",
        invitee_role="Update invitee role restriction (use @everyone to clear)",
        max_requests="Max simultaneous open requests per user (leave empty to keep current)",
    )
    @app_commands.autocomplete(panel=_panel_autocomplete, label=_type_autocomplete)
    async def edit_type(
        self,
        interaction: discord.Interaction,
        panel: str,
        label: str,
        new_label: str | None = None,
        creator_role: discord.Role | None = None,
        invitee_role: discord.Role | None = None,
        max_requests: int | None = None,
    ) -> None:
        async with SessionLocal() as session:
            db_panel = await _get_panel(session, interaction.guild_id, panel)
            if db_panel is None:
                await interaction.response.send_message(S.PANEL_NOT_FOUND.format(name=panel), ephemeral=True)
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
                    S.TYPE_NOT_FOUND.format(label=label, panel=panel), ephemeral=True
                )
                return

            old_label = apt.label
            label_changed = new_label and new_label != old_label

            if new_label:
                apt.label = new_label
            if creator_role is not None:
                apt.required_creator_role_id = None if creator_role.is_default() else creator_role.id
            if invitee_role is not None:
                apt.restrict_invitees_to_role_id = None if invitee_role.is_default() else invitee_role.id
            if max_requests is not None:
                apt.max_concurrent_requests = max(1, max_requests)

            await session.commit()

        parts = [S.TYPE_UPDATED.format(old=old_label)]
        if label_changed:
            parts.append(S.TYPE_LABEL_CHANGED.format(new=new_label))
        if creator_role is not None:
            if creator_role.is_default():
                parts.append(S.TYPE_ROLE_CLEARED.format(field="Creator role"))
            else:
                parts.append(S.TYPE_CREATOR_ROLE_SET.format(role=creator_role.mention))
        if invitee_role is not None:
            if invitee_role.is_default():
                parts.append(S.TYPE_ROLE_CLEARED.format(field="Invitee role"))
            else:
                parts.append(S.TYPE_INVITEE_ROLE_SET.format(role=invitee_role.mention))

        if label_changed:
            parts.append(f"\nUse `/timely refresh_panel panel:{panel}` to update the panel buttons.")

        await interaction.response.send_message("".join(parts), ephemeral=True)

    @timely.command(name="list_types", description="Show all buttons in a panel")
    @_require_manage_guild()
    @app_commands.describe(panel="Name of the panel")
    @app_commands.autocomplete(panel=_panel_autocomplete)
    async def list_types(self, interaction: discord.Interaction, panel: str) -> None:
        async with SessionLocal() as session:
            db_panel = await _get_panel(session, interaction.guild_id, panel)
            if db_panel is None:
                await interaction.response.send_message(S.PANEL_NOT_FOUND.format(name=panel), ephemeral=True)
                return

            result = await session.execute(
                select(AppointmentType).where(AppointmentType.panel_id == db_panel.id)
            )
            types = result.scalars().all()

        if not types:
            await interaction.response.send_message(S.NO_TYPES.format(panel=panel), ephemeral=True)
            return

        embed = discord.Embed(title=S.TYPES_TITLE.format(panel=panel), color=discord.Color.blurple())
        for apt in types:
            cr = f"<@&{apt.required_creator_role_id}>" if apt.required_creator_role_id else S.ROLE_ALL
            ir = f"<@&{apt.restrict_invitees_to_role_id}>" if apt.restrict_invitees_to_role_id else S.ROLE_ALL
            embed.add_field(
                name=f"**{apt.label}**",
                value=f"{S.TYPE_CREATOR_ROLE}: {cr}\n{S.TYPE_INVITEE_ROLE}: {ir}\nMax requests: {apt.max_concurrent_requests}",
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Panel Posting ──────────────────────────────────────────────────────────

    @timely.command(name="post_panel", description="Post a panel to its channel")
    @_require_manage_guild()
    @app_commands.describe(panel="Name of the panel")
    @app_commands.autocomplete(panel=_panel_autocomplete)
    async def post_panel(self, interaction: discord.Interaction, panel: str) -> None:
        await self._post_or_refresh(interaction, panel, refresh=False)

    @timely.command(name="refresh_panel", description="Delete and re-post a panel")
    @_require_manage_guild()
    @app_commands.describe(panel="Name of the panel")
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
                    S.PANEL_NOT_FOUND.format(name=panel_name), ephemeral=True
                )
                return
            if not db_panel.channel_id:
                await interaction.response.send_message(
                    S.PANEL_NO_CHANNEL.format(name=panel_name), ephemeral=True
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
                S.PANEL_NO_TYPES.format(name=panel_name), ephemeral=True
            )
            return

        embed, view = build_panel(panel_name, list(types))
        msg = await channel.send(embed=embed, view=view)

        async with SessionLocal() as session:
            db_panel = await _get_panel(session, interaction.guild_id, panel_name)
            db_panel.message_id = msg.id
            await session.commit()

        result_msg = S.PANEL_REFRESHED.format(name=panel_name) if refresh else S.PANEL_POSTED.format(name=panel_name)
        await interaction.response.send_message(result_msg, ephemeral=True)

    # ── Disable / Enable ───────────────────────────────────────────────────────

    @timely.command(name="disable", description="Disable a panel — buttons will no longer accept requests")
    @_require_manage_guild()
    @app_commands.describe(panel="Name of the panel to disable")
    @app_commands.autocomplete(panel=_panel_autocomplete)
    async def disable(self, interaction: discord.Interaction, panel: str) -> None:
        async with SessionLocal() as session:
            db_panel = await _get_panel(session, interaction.guild_id, panel)
            if db_panel is None:
                await interaction.response.send_message(S.PANEL_NOT_FOUND.format(name=panel), ephemeral=True)
                return
            if not db_panel.active:
                await interaction.response.send_message(S.PANEL_ALREADY_DISABLED.format(name=panel), ephemeral=True)
                return
            db_panel.active = False
            await session.commit()

        await interaction.response.send_message(S.PANEL_DISABLE_SUCCESS.format(name=panel), ephemeral=True)

    @timely.command(name="enable", description="Re-enable a previously disabled panel")
    @_require_manage_guild()
    @app_commands.describe(panel="Name of the panel to enable")
    @app_commands.autocomplete(panel=_panel_autocomplete)
    async def enable(self, interaction: discord.Interaction, panel: str) -> None:
        async with SessionLocal() as session:
            db_panel = await _get_panel(session, interaction.guild_id, panel)
            if db_panel is None:
                await interaction.response.send_message(S.PANEL_NOT_FOUND.format(name=panel), ephemeral=True)
                return
            if db_panel.active:
                await interaction.response.send_message(S.PANEL_ALREADY_ENABLED.format(name=panel), ephemeral=True)
                return
            db_panel.active = True
            await session.commit()

        await interaction.response.send_message(S.PANEL_ENABLE_SUCCESS.format(name=panel), ephemeral=True)

    # ── Announce ───────────────────────────────────────────────────────────────

    @timely.command(name="announce", description="Post a formatted info message in this channel")
    @_require_manage_guild()
    async def announce(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(AnnounceModal(channel=interaction.channel))

    # ── User Commands ──────────────────────────────────────────────────────────

    @timely.command(name="status", description="Show your appointment requests")
    @app_commands.describe(filter="Which requests to show (default: all)")
    @app_commands.choices(filter=[
        app_commands.Choice(name="All", value="all"),
        app_commands.Choice(name="Open", value="open"),
        app_commands.Choice(name="Confirmed", value="confirmed"),
        app_commands.Choice(name="Cancelled", value="cancelled"),
    ])
    async def status(self, interaction: discord.Interaction, filter: str = "all") -> None:
        from bot.views.creator_view import CreatorView, build_status_embed, fetch_event_data

        status_filter = {
            "open": [EventStatus.OPEN],
            "confirmed": [EventStatus.CONFIRMED],
            "cancelled": [EventStatus.CANCELLED],
            "all": [EventStatus.OPEN, EventStatus.CONFIRMED, EventStatus.CANCELLED],
        }[filter]

        async with SessionLocal() as session:
            result = await session.execute(
                select(Event).where(
                    Event.guild_id == interaction.guild_id,
                    Event.creator_id == interaction.user.id,
                    Event.status.in_(status_filter),
                ).order_by(Event.created_at.desc())
            )
            events = result.scalars().all()

            if not events:
                await interaction.response.send_message(S.STATUS_NO_EVENTS, ephemeral=True)
                return

            if len(events) == 1 and events[0].status == EventStatus.OPEN:
                event, slots, participants, votes = await fetch_event_data(session, events[0].id)
                embed = build_status_embed(event, list(slots), list(participants), list(votes), interaction.guild)
                view = CreatorView(event_id=event.id)
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                view = EventPickerView(list(events))
                await interaction.response.send_message(S.STATUS_PICK_EVENT, view=view, ephemeral=True)

    @timely.command(name="remind", description="Send a reminder DM to participants who have not yet replied")
    async def remind(self, interaction: discord.Interaction) -> None:
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
            await interaction.response.send_message(S.STATUS_NO_OPEN_EVENTS, ephemeral=True)
            return

        if len(events) > 1:
            await interaction.response.send_message(
                S.REMIND_PICK_EVENT, view=RemindPickerView(list(events)), ephemeral=True
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
        await interaction.response.send_message(S.REMIND_ALL_ANSWERED, ephemeral=True)
        return

    sent, failed = 0, []
    for p in pending:
        try:
            user = await interaction.client.fetch_user(p.user_id)
            embed, view = build_vote_message(event, list(slots), interaction.user)
            msg = await user.send(content=S.REMIND_PREFIX, embed=embed, view=view)
            view.message = msg
            sent += 1
        except discord.Forbidden:
            failed.append(str(p.user_id))

    msg = S.REMIND_SENT.format(count=sent)
    if failed:
        msg += S.REMIND_FAILED.format(ids=", ".join(failed))

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
        options = [discord.SelectOption(label=e.title[:100], value=str(e.id)) for e in events[:25]]
        super().__init__(placeholder=S.STATUS_PICK_PH, options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        await _send_reminders(interaction, int(self.values[0]))


class EventPickerView(discord.ui.View):
    def __init__(self, events: list[Event]) -> None:
        super().__init__(timeout=120)
        self.add_item(EventPickerSelect(events))


_STATUS_EMOJI = {
    EventStatus.OPEN: "🔄",
    EventStatus.CONFIRMED: "✅",
    EventStatus.CANCELLED: "❌",
}


class EventPickerSelect(discord.ui.Select):
    def __init__(self, events: list[Event]) -> None:
        options = [
            discord.SelectOption(
                label=e.title[:90],
                description=f"{_STATUS_EMOJI.get(e.status, '')} {e.status.value.capitalize()}",
                value=str(e.id),
            )
            for e in events[:25]
        ]
        super().__init__(placeholder=S.STATUS_PICK_PH, options=options)

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
