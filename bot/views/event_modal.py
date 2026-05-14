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
    # Comma-separated datetime strings, e.g. "2026-06-01 14:00, 2026-06-02 10:00"
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

        view = ParticipantPickerView(
            apt=self.apt,
            title=self.event_title.value,
            description=self.description.value or "",
            raw_slots=self.time_slots.value,
        )
        await interaction.response.send_message(
            "Wähle die Teilnehmer für deinen Termin:", view=view, ephemeral=True
        )
