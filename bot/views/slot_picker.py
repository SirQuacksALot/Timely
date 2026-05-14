"""Step 2 of event creation: select time slots via dropdowns."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import discord

_DAYS_AHEAD = 21
_WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def _next_dates() -> list[date]:
    today = datetime.now().date()
    return [today + timedelta(days=i) for i in range(1, _DAYS_AHEAD + 1)]


def _format_slots(slots: list[datetime]) -> str:
    if not slots:
        return ""
    lines = "\n".join(f"• {s.strftime('%d.%m.%Y %H:%M')}" for s in slots)
    return f"**Hinzugefügte Slots:**\n{lines}\n\n"


def _picker_content(slots: list[datetime]) -> str:
    return (
        f"**Schritt 2/3 — Zeitvorschläge**\n\n"
        f"{_format_slots(slots)}"
        "Wähle Datum, Stunde und Minute, dann klicke **+ Slot hinzufügen**."
    )


class SlotPickerView(discord.ui.View):
    def __init__(self, apt_id: int, participants: list[discord.Member]) -> None:
        super().__init__(timeout=300)
        self.apt_id = apt_id
        self.participants = participants
        self.slots: list[datetime] = []

        dates = _next_dates()
        self.selected_date: date = dates[0]
        self.selected_hour: int = 10
        self.selected_minute: int = 0

        self._rebuild(dates)

    def _rebuild(self, dates: list[date] | None = None) -> None:
        self.clear_items()
        if dates is None:
            dates = _next_dates()

        self.add_item(_DateSelect(dates, self.selected_date))
        self.add_item(_HourSelect(self.selected_hour))
        self.add_item(_MinuteSelect(self.selected_minute))

        has_slots = bool(self.slots)
        self.add_item(_AddButton())
        self.add_item(_RemoveLastButton(disabled=not has_slots))
        self.add_item(_ProceedButton(disabled=not has_slots))


class _DateSelect(discord.ui.Select):
    def __init__(self, dates: list[date], selected: date) -> None:
        options = [
            discord.SelectOption(
                label=f"{_WEEKDAYS[d.weekday()]} {d.strftime('%d.%m.')}",
                value=d.isoformat(),
                default=(d == selected),
            )
            for d in dates
        ]
        super().__init__(placeholder="Datum wählen", options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: SlotPickerView = self.view
        view.selected_date = date.fromisoformat(self.values[0])
        view._rebuild()
        await interaction.response.edit_message(content=_picker_content(view.slots), view=view)


class _HourSelect(discord.ui.Select):
    def __init__(self, selected: int) -> None:
        options = [
            discord.SelectOption(
                label=f"{h:02d}:xx",
                value=str(h),
                default=(h == selected),
            )
            for h in range(24)
        ]
        super().__init__(placeholder="Stunde wählen", options=options, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: SlotPickerView = self.view
        view.selected_hour = int(self.values[0])
        view._rebuild()
        await interaction.response.edit_message(content=_picker_content(view.slots), view=view)


class _MinuteSelect(discord.ui.Select):
    def __init__(self, selected: int) -> None:
        options = [
            discord.SelectOption(
                label=f":{m:02d}",
                value=str(m),
                default=(m == selected),
            )
            for m in [0, 15, 30, 45]
        ]
        super().__init__(placeholder="Minute wählen", options=options, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: SlotPickerView = self.view
        view.selected_minute = int(self.values[0])
        view._rebuild()
        await interaction.response.edit_message(content=_picker_content(view.slots), view=view)


class _AddButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(label="+ Slot hinzufügen", style=discord.ButtonStyle.primary, row=3)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: SlotPickerView = self.view
        dt = datetime(
            view.selected_date.year,
            view.selected_date.month,
            view.selected_date.day,
            view.selected_hour,
            view.selected_minute,
        )
        if dt in view.slots:
            await interaction.response.send_message(
                "Dieser Slot wurde bereits hinzugefügt.", ephemeral=True
            )
            return

        view.slots.append(dt)
        view.slots.sort()
        view._rebuild()
        await interaction.response.edit_message(content=_picker_content(view.slots), view=view)


class _RemoveLastButton(discord.ui.Button):
    def __init__(self, disabled: bool) -> None:
        super().__init__(
            label="Letzten entfernen",
            style=discord.ButtonStyle.secondary,
            row=3,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: SlotPickerView = self.view
        if view.slots:
            view.slots.pop()
        view._rebuild()
        await interaction.response.edit_message(content=_picker_content(view.slots), view=view)


class _ProceedButton(discord.ui.Button):
    def __init__(self, disabled: bool) -> None:
        super().__init__(
            label="Weiter →",
            style=discord.ButtonStyle.success,
            row=3,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from bot.views.event_modal import EventModal

        view: SlotPickerView = self.view
        await interaction.response.send_modal(
            EventModal(apt_id=view.apt_id, participants=view.participants, slots=view.slots)
        )
