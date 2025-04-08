import logging
import random

import discord

from r2d20.games.players import PlayerBase

__all__ = ['ZilchGame']

logger = logging.getLogger(__name__)


class ZilchDieButton(discord.ui.Button):
    held_style = discord.ButtonStyle.grey
    unheld_style = discord.ButtonStyle.red
    
    def __init__(self, **kwargs):
        """A button representing a die in the Zilch game.
        
        Args:
            kwargs: Additional keyword arguments sent to discord.ui.Button

        NOTE: label, style and disabled properties are handled by this class.
        """
        super().__init__(style=self.unheld_style, **kwargs)
        self._is_held: bool = False
        self._is_locked: bool = False
        self.disabled = False
        self.emoji = "🎲"
        self.roll()

    @property
    def value(self) -> int:
        return self._value
    
    @property
    def is_held(self) -> bool:
        return self._is_held and not self._is_locked
    
    @property
    def is_locked(self) -> bool:
        return self._is_locked

    def roll(self) -> int:
        self._value = random.randint(1, 6)
        self._set_label()

    def toggle_hold(self) -> bool:
        if self._is_locked:
            return True
        self._is_held = not self._is_held
        self._set_style()
        return self._is_held
    
    def lock_if_held(self):
        if self._is_held:
            self._is_locked = True
            self._set_disabled()

    def _set_label(self):
        self.label = f'**[{self._value}]**'

    def _set_style(self):
        self.style = self.held_style if self._is_held else self.unheld_style
    
    def _set_disabled(self):
        self.disabled = self._is_locked


class ZilchRound:
    def __init__(self):
        self.score = 0


class ZilchPlayer(PlayerBase):
    def __init__(self, member: discord.Member):
        super().__init__(member)
        self.score = 0
        self.current_round: ZilchRound = None
        self.rounds: list[ZilchRound] = []

    def new_round(self):
        self.current_round = ZilchRound()
        self.rounds.append(self.current_round)

    def roll(self):
        self.current_round.roll()

    def bank(self):
        self.score += self.current_round.score


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

        self.roll_button = discord.ui.Button(style=discord.ButtonStyle.green,
                                             label='Roll',
                                             emoji="🎲",
                                             row=1)
        self.roll_button.interaction_check = self.roll_or_bank_check
        self.roll_button.callback = self.roll

        self.bank_button = discord.ui.Button(style=discord.ButtonStyle.green,
                                             label='Bank',
                                             row=1)
        self.bank_button.interaction_check = self.roll_or_bank_check
        self.bank_button.callback = self.bank
        
        self.dice_buttons = [ZilchDieButton(row=0) for _ in range(6)]
        for button in self.dice_buttons:
            button.interaction_check = self.hold_check
            button.callback = self.hold

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
        return any(die.is_held for die in self.dice_buttons)

    async def roll(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_player.roll()
        self.roll_button.disabled = True
        self.bank_button.disabled = True
        await interaction.response.edit_message(embed=self._embed, view=self)

    async def bank(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_player.bank()
        await interaction.response.edit_message(embed=self._embed, view=self)

    async def hold(self, interaction: discord.Interaction, button: ZilchDieButton):
        "Toggle various buttons' selected/disabled status"
        button.toggle_hold()
        if any(die.is_held for die in self.dice_buttons):
            self.roll_button.disabled = False
            self.bank_button.disabled = False
        else:
            self.roll_button.disabled = True
            self.bank_button.disabled = True
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
