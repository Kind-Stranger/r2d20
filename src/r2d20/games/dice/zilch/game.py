import logging
import random

import discord

from r2d20.bot import R2d20
from r2d20.games.players import PlayerBase

__all__ = ['ZilchGame']

logger = logging.getLogger(__name__)


class ZilchDieButton(discord.ui.Button):
    """A button representing a die in the Zilch game.

    NOTE:
        The button's label, style and disabled properties are handled by
        this class and will be overridden if passed to the parent class.
    
    Args:
        **kwargs: Additional keyword arguments sent to discord.ui.Button

    Attributes:
        held_style (discord.ButtonStyle): Style when the die is held.
        unheld_style (discord.ButtonStyle): Style when the die is not held.
        value (int): The current value of the die.
        is_held (bool): Whether the die is currently held.
        is_locked (bool): Whether the die is locked and cannot be rolled again.
    
    """
    held_style = discord.ButtonStyle.red
    unheld_style = discord.ButtonStyle.grey
    
    def __init__(self, **kwargs):
        super().__init__(style=self.unheld_style, emoji="🎲", **kwargs)
        self._is_held: bool = False
        self._is_locked: bool = False
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
        """Roll this die and set button label according to result"""
        self._value = random.randint(1, 6)
        self._set_label()

    def toggle_hold(self) -> bool:
        """Toggle held flag and styles"""
        if self._is_locked:
            return True
        self._is_held = not self._is_held
        self._set_style()
        return self._is_held
    
    def lock_if_held(self):
        """Lock the die if it is currently held"""
        if self._is_held:
            self._is_locked = True
            self._set_disabled()

    def _set_label(self):
        """Sets the label based on the current dice value"""
        self.label = f'[{self._value}]'

    def _set_style(self):
        """Sets the style of the button based on whether it is cuurently held"""
        self.style = self.held_style if self._is_held else self.unheld_style
    
    def _set_disabled(self):
        """Sets the button to disabled if it has been locked"""
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
    def __init__(self, bot: R2d20, interaction: discord.Interaction, *,
                 members: list[discord.Member], **kwargs):
        super().__init__(**kwargs)
        self.orig_interaction = interaction
        self.players = [ZilchPlayer(member) for member in members]
        self.target_score = 10_000

        self._current_player_index: int = 0
        self._player_marker = "👈"
        self._embed = self._init_embed()

        self._dice_buttons: dict[str, ZilchDieButton] = {}
        for i in range(6):
            button = ZilchDieButton(row=i // 3)  # 3 buttons per row
            button.callback = self.hold
            self.add_die_button(button)

        self.roll_button = discord.ui.Button(style=discord.ButtonStyle.green,
                                             label='Roll',
                                             row=2)
        self.roll_button.interaction_check = self.is_any_die_held
        self.roll_button.callback = self.roll
        self.add_item(self.roll_button)

        self.bank_button = discord.ui.Button(style=discord.ButtonStyle.blurple,
                                             label='Bank',
                                             row=2)
        self.bank_button.interaction_check = self.is_any_die_held
        self.bank_button.callback = self.bank
        self.add_item(self.bank_button)
        
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

    async def is_any_die_held(self, interaction: discord.Interaction):
        return any(die.is_held for die in self.dice_buttons)

    async def roll(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_player.roll()
        self.roll_button.disabled = True
        self.bank_button.disabled = True
        await interaction.response.edit_message(embed=self._embed, view=self)

    async def bank(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_player.bank()
        await interaction.response.edit_message(embed=self._embed, view=self)

    async def hold(self, interaction: discord.Interaction):#, button: ZilchDieButton):
        "Toggle various buttons' selected/disabled status"
        button_id = interaction.data['custom_id']
        button = self.get_die_button(button_id)
        button.toggle_hold()
        if any(die.is_held for die in self._dice_buttons.values()):
            self.roll_button.disabled = False
            self.bank_button.disabled = False
        else:
            self.roll_button.disabled = True
            self.bank_button.disabled = True
        #
        await interaction.response.edit_message(view=self)

    def add_die_button(self, button: ZilchDieButton):
        """Add an item to the view."""
        id = str(button.custom_id or button.sku_id)
        self._dice_buttons[id] = button
        self.add_item(button)

    def get_die_button(self, id: str) -> ZilchDieButton:
        """Get a button by its ID."""
        return self._dice_buttons.get(str(id))

    def _init_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Zilch",
                              description=f'Target : **{self.target_score}**')
        # first = True
        # for player in self.players:
        #     field = self._create_player_embed_field(player, first)
        #     first = False
        #     embed.add_field(**field)
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
