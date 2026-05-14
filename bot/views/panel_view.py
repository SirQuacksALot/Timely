import discord

from bot.database.models import AppointmentType


def build_panel(
    types: list[AppointmentType],
) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        title="Termin anfragen",
        description="Wähle einen Termintyp, um einen neuen Termin zu erstellen.",
        color=discord.Color.blurple(),
    )

    view = PanelView(types)
    return embed, view


class PanelView(discord.ui.View):
    def __init__(self, types: list[AppointmentType]) -> None:
        super().__init__(timeout=None)
        for apt in types:
            self.add_item(AppointmentTypeButton(apt))


class AppointmentTypeButton(discord.ui.Button):
    def __init__(self, apt: AppointmentType) -> None:
        super().__init__(
            label=apt.label,
            style=discord.ButtonStyle.primary,
            custom_id=f"timely:start:{apt.id}",
        )
        self.apt = apt

    async def callback(self, interaction: discord.Interaction) -> None:
        # Check creator role restriction
        if self.apt.required_creator_role_id:
            role_ids = {r.id for r in interaction.user.roles}
            if self.apt.required_creator_role_id not in role_ids:
                await interaction.response.send_message(
                    "Du hast keine Berechtigung, diesen Termintyp zu nutzen.", ephemeral=True
                )
                return

        from bot.views.event_modal import EventModal
        await interaction.response.send_modal(EventModal(self.apt))
