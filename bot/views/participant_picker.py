"""Step 1 of event creation: select participants, then open the slot picker."""
from __future__ import annotations

import discord

from bot.strings import S


class ParticipantPickerView(discord.ui.View):
    def __init__(
        self,
        apt_id: int,
        creator_id: int,
        eligible_members: list[discord.Member] | None,
    ) -> None:
        super().__init__(timeout=300)
        self.apt_id = apt_id
        self.creator_id = creator_id
        self.selected_users: list[discord.Member] = []

        if eligible_members is not None:
            self.add_item(RoleFilteredSelect(eligible_members))
        else:
            self.add_item(OpenSelect(creator_id))

    @discord.ui.button(label=S.PROCEED_BUTTON, style=discord.ButtonStyle.primary, row=1)
    async def proceed(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not self.selected_users:
            await interaction.response.send_message(S.MIN_ONE_PARTICIPANT, ephemeral=True)
            return

        from bot.views.slot_picker import SlotPickerView, _picker_content
        view = SlotPickerView(apt_id=self.apt_id, participants=self.selected_users)
        await interaction.response.edit_message(content=_picker_content([]), view=view)


class RoleFilteredSelect(discord.ui.Select):
    def __init__(self, members: list[discord.Member]) -> None:
        self._member_map = {m.id: m for m in members}
        options = [
            discord.SelectOption(label=m.display_name[:100], value=str(m.id))
            for m in members[:25]
        ]
        super().__init__(
            placeholder=S.SELECT_PARTICIPANTS,
            min_values=1,
            max_values=min(len(options), 25),
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ParticipantPickerView = self.view
        view.selected_users = [self._member_map[int(v)] for v in self.values]
        await interaction.response.defer()


class OpenSelect(discord.ui.UserSelect):
    def __init__(self, creator_id: int) -> None:
        super().__init__(
            placeholder=S.SELECT_PARTICIPANTS,
            min_values=1,
            max_values=10,
            row=0,
        )
        self.creator_id = creator_id

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ParticipantPickerView = self.view
        selected = [m for m in self.values if m.id != self.creator_id]
        creator_excluded = len(selected) < len(self.values)
        view.selected_users = selected

        if creator_excluded and not selected:
            await interaction.response.send_message(S.CREATOR_SELF_SELECT, ephemeral=True)
            return
        if creator_excluded:
            await interaction.response.send_message(S.CREATOR_AUTO_REMOVED, ephemeral=True)
            return

        await interaction.response.defer()
