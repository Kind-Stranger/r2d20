import logging
import random

import discord

from r2d20.games.players import PlayerBase

__all__ = ['ZilchGame']

logger = logging.getLogger(__name__)


class ZilchRound:
    pass


class ZilchPlayer(PlayerBase):
    def __init__(self, member: discord.Member):
        super().__init__(member)
        self.score = 0
        self.rounds: list[ZilchRound] = []


class HoldButton(discord.ui.Button):
    selectedStyle = discord.ButtonStyle.primary
    deselectedStyle = discord.ButtonStyle.secondary

    def __init__(self, *, label=None):
        super().__init__()
        self.label = label
        self.style = self.deselectedStyle
        self.row = 2

    @property
    def selected(self):
        return self.style == self.selectedStyle


class ZilchGame(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, *,
                 members: list[discord.Member], **kwargs):
        super().__init__(**kwargs)
        self.orig_interaction = interaction
        self.players = [ZilchPlayer(member) for member in members]
        self.target_score = 10_000

        self._current_player_index: int = 0
        self._player_marker = "👈"
        self._embed = self._init_embed()

        roll_button = discord.ui.Button(style=discord.ButtonStyle.green,
                                        label='Roll',
                                        emoji="🎲",
                                        row=1)
        roll_button.interaction_check = self.roll_or_bank_check
        roll_button.callback = self.roll
        self._roll_button = roll_button
        bank_button = discord.ui.Button(style=discord.ButtonStyle.green,
                                        label='Bank',
                                        row=1)
        bank_button.interaction_check = self.roll_or_bank_check
        bank_button.callback = self.bank
        self._bank_button = bank_button
        
        self._hold_buttons: list[HoldButton]

    @property
    def current_player(self) -> ZilchPlayer | None:
        if self._current_player_index in range(len(self.players)):
            return self.players[self._current_player_index]

    @property
    def embed(self) -> discord.Embed:
        return self._embed
    
    @property
    def is_game_over(self) -> bool:
        max_score = max(player.score for player in self.players)
        return max_score >= self.target_score

    async def roll_or_bank_check(self, interaction: discord.Interaction):
        return any(button.selected for button in self._hold_buttons)

    async def roll(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_player.roll()
        self._roll_button.disabled = True
        self._bank_button.disabled = True
        await interaction.response.edit_message(embed=self._embed, view=self)

    async def bank(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_player.bank()
        await interaction.response.edit_message(embed=self._embed, view=self)

    async def hold(self, interaction: discord.Interaction, button: HoldButton):
        "Toggle various buttons' selected/disabled status"
        button.style == button.deselectedStyle if button.selected else button.selectedStyle
        if any(button.selected for button in self._hold_buttons):
            self._roll_button.disabled = False
            self._bank_button.disabled = False
        else:
            self._roll_button.disabled = True
            self._bank_button.disabled = True
        #
        await interaction.response.edit_message(view=self)

    def _init_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Zilch",
                              description=f'Target : **{self.target_score}**')
        first = True
        for player in self.players:
            field = self._create_player_embed_field(player, first)
            first = False
            embed.add_field(**field)
        #
        return embed

    def _create_player_embed_field(self, player: ZilchPlayer, mark_player):
        score = player.score if player.score <= self.target_score else 'BUST!'
        name = f'{player.display_name} - Score: {score}'
        if mark_player:
            name += f' {self._player_marker}'
        value = self._visualise_results(player.rounds)
        inline = False
        return {'name': name, 'value': value, 'inline': inline}

    async def interaction_check(self, interaction: discord.Interaction):
        allowed = interaction.user.id == self.current_player.id
        if not allowed:
            logger.debug(
                f"Interaction was not allowed: It is not {interaction.user.display_name}'s turn")
            await interaction.response.send_message("It's not your turn", ephemeral=True, delete_after=5.0)
        #
        return allowed

    async def on_timeout(self):
        """Remove the view from the message."""
        logger.debug("Game timed out.")
        self.stop()
        self.clear_items()
        self._embed.set_footer(text="Game timed out.")
        try:
            await self.orig_interaction.edit_original_response(embed=self._embed, view=None)
        except discord.DiscordException:
            logger.error('Problem showing game timed out')

    async def on_error(self, interaction: discord.Interaction, error, item):
        self.stop()
        self.clear_items()
        self._embed.set_footer(text=f'An error occurred')
        await interaction.edit_original_response(embed=self._embed, view=None)
