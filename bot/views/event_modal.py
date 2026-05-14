"""Modal for entering event details after clicking a panel button."""
import discord

from bot.database.models import AppointmentType


class EventModal(discord.ui.Modal, title="Neuen Termin erstellen"):
    event_title = discord.ui.TextInput(
        label="Titel",
        placeholder="z.B. Team-Meeting Q2",
        max_length=200,
    )
    description = discord.ui.TextInput(
        label="Beschreibung",
        placeholder="Worum geht es?",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=2000,
    )
    time_slots = discord.ui.TextInput(
        label="Zeitvorschläge",
        placeholder="2026-06-01 14:00, 2026-06-02 10:00",
        max_length=500,
    )

    def __init__(self, apt: AppointmentType) -> None:
        super().__init__()
        self.apt = apt

    async def on_submit(self, interaction: discord.Interaction) -> None:
        from bot.views.participant_picker import ParticipantPickerView

        eligible_members: list[discord.Member] | None = None
        if self.apt.restrict_invitees_to_role_id:
            role = interaction.guild.get_role(self.apt.restrict_invitees_to_role_id)
            if role:
                eligible_members = [
                    m for m in role.members
                    if m.id != interaction.user.id and not m.bot
                ]

            if not eligible_members:
                await interaction.response.send_message(
                    "Keine einladbaren Nutzer mit der erforderlichen Rolle gefunden.",
                    ephemeral=True,
                )
                return

        view = ParticipantPickerView(
            apt=self.apt,
            title=self.event_title.value,
            description=self.description.value or "",
            raw_slots=self.time_slots.value,
            creator_id=interaction.user.id,
            eligible_members=eligible_members,
        )
        await interaction.response.send_message(
            "Wähle die Teilnehmer für deinen Termin:", view=view, ephemeral=True
        )
