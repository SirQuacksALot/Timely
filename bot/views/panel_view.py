import discord

from bot.database.models import AppointmentType


def build_panel(types: list[AppointmentType]) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        title="Termin anfragen",
        description="Wähle einen Termintyp, um einen neuen Termin zu erstellen.",
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
        from bot.views.participant_picker import ParticipantPickerView

        # Always re-fetch apt from DB to avoid detached-instance issues
        async with SessionLocal() as session:
            apt = await session.get(AppointmentType, self.apt_id)

        if apt is None:
            await interaction.response.send_message(
                "Dieser Termintyp existiert nicht mehr.", ephemeral=True
            )
            return

        # Creator role check
        if apt.required_creator_role_id:
            if apt.required_creator_role_id not in {r.id for r in interaction.user.roles}:
                await interaction.response.send_message(
                    "Du hast keine Berechtigung, diesen Termintyp zu nutzen.", ephemeral=True
                )
                return

        # Build eligible member list when a role restriction is configured
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
                await interaction.response.send_message(
                    "Keine einladbaren Nutzer mit der erforderlichen Rolle gefunden.",
                    ephemeral=True,
                )
                return

        view = ParticipantPickerView(
            apt_id=apt.id,
            creator_id=interaction.user.id,
            eligible_members=eligible_members,
        )
        await interaction.response.send_message(
            "Schritt 1/2 — Wähle die Teilnehmer für deinen Termin:",
            view=view,
            ephemeral=True,
        )
