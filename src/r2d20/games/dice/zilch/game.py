import logging

import discord

from r2d20.bot import R2d20
from .buttons import ZilchDieButton
from .players import ZilchPlayer

__all__ = ['ZilchGame']

logger = logging.getLogger(__name__)


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

        self.dice_buttons: dict[str, ZilchDieButton] = {}
        for i in range(6):
            button = ZilchDieButton(row=i//3)  # 3 buttons per row
            button.callback = self.hold
            id = str(button.custom_id or button.sku_id)
            self.dice_buttons[id] = button  # So we can retrieve it on callback
            self.add_item(button)  # Add the button to the view
        #
        self.roll_button = discord.ui.Button(style=discord.ButtonStyle.green,
                                             label='Roll',
                                             row=2)
        self.roll_button.callback = self.roll
        self.add_item(self.roll_button)

        self.bank_button = discord.ui.Button(style=discord.ButtonStyle.blurple,
                                             label='Bank',
                                             row=2)
        self.bank_button.callback = self.bank
        self.add_item(self.bank_button)
        
    @property
    def current_player(self) -> ZilchPlayer | None:
        if self._current_player_index in range(len(self.players)):
            return self.players[self._current_player_index]

    @property
    def embed(self) -> discord.Embed:
        return self._embed
    
    def is_game_over(self) -> bool:
        max_score = max(player.score for player in self.players)
        return max_score >= self.target_score

    async def roll(self, interaction: discord.Interaction):
        """Callback for the roll button.  Triggers a roll of the dice."""
        if all(die.is_locked or die.is_held for die in self.dice_buttons.values()):
            self._reset_all_dice()
        self.roll_button.disabled = True
        self.bank_button.disabled = True
        await interaction.response.edit_message(embed=self._embed, view=self)

    async def bank(self, interaction: discord.Interaction):
        """Callback for the bank button.  Banks score and passes turn to next
        player.
        """
        self.current_player.bank()
        self._end_turn()
        await interaction.response.edit_message(embed=self._embed, view=self)

    async def hold(self, interaction: discord.Interaction):
        """Callback for the die buttons"""
        id = interaction.data['custom_id']
        button = self.dice_buttons.get(str(id))
        logger.debug(f"Button pressed: {button.label}")
        button.toggle_hold()
        if any(die.is_held for die in self.dice_buttons.values()):
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

    def _reset_all_dice(self): 
        """Unlock all dice buttons."""
        for die in self.dice_buttons.values():
            die.reset()

    def _end_turn(self):
        max_score = max(player.score for player in self.players)
        if max_score >= self.target_score:
            leaders = [player for player in self.players if player.score == max_score]
            if len(leaders) == len(self.players):
                self._embed.set_footer(text="Game over! It's a tie!")
            else:
                self._embed.set_footer(text=f"Game over! {leaders[0].display_name} wins!")
            #
            self.stop()
        else:
            self._current_player_index += 1
            if self._current_player_index >= len(self.players):
                self._current_player_index = 0
            self._embed.set_footer(text=f"{self.current_player.display_name}'s turn")
        #

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
