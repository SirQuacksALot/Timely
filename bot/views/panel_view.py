import discord

from bot.database.models import AppointmentType, Panel
from bot.strings import S


def build_panel(
    panel_name: str, types: list[AppointmentType]
) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        title=S.PANEL_EMBED_TITLE.format(panel_name=panel_name),
        description=S.PANEL_EMBED_DESC,
        color=discord.Color.blurple(),
    )
    return embed, PanelView(types)


class PanelView(discord.ui.View):
    def __init__(self, types: list[AppointmentType]) -> None:
        super().__init__(timeout=None)
        for apt in types:
            self.add_item(AppointmentTypeButton(apt.id, apt.label))


class AppointmentTypeButton(discord.ui.Button):
    def __init__(self, apt_id: int, label: str) -> None:
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            custom_id=f"timely:start:{apt_id}",
        )
        self.apt_id = apt_id

    async def callback(self, interaction: discord.Interaction) -> None:
        from bot.database.db import SessionLocal
        from bot.database.models import AppointmentType
        from bot.views.participant_picker import ParticipantPickerView

        async with SessionLocal() as session:
            apt = await session.get(AppointmentType, self.apt_id)
            panel = await session.get(Panel, apt.panel_id) if apt else None

        if apt is None:
            await interaction.response.send_message(S.TYPE_GONE, ephemeral=True)
            return

        if panel is None or not panel.active:
            await interaction.response.send_message(S.PANEL_DISABLED, ephemeral=True)
            return

        if apt.required_creator_role_id:
            if apt.required_creator_role_id not in {r.id for r in interaction.user.roles}:
                await interaction.response.send_message(S.NO_PERMISSION_TYPE, ephemeral=True)
                return

        eligible_members: list[discord.Member] | None = None
        if apt.restrict_invitees_to_role_id:
            role_id = apt.restrict_invitees_to_role_id
            eligible_members = [
                m for m in interaction.guild.members
                if any(r.id == role_id for r in m.roles)
                and m.id != interaction.user.id
                and not m.bot
            ]
            if not eligible_members:
                await interaction.response.send_message(S.NO_ELIGIBLE_MEMBERS, ephemeral=True)
                return

        view = ParticipantPickerView(
            apt_id=apt.id,
            creator_id=interaction.user.id,
            eligible_members=eligible_members,
        )
        await interaction.response.send_message(S.STEP1_HEADER, view=view, ephemeral=True)
