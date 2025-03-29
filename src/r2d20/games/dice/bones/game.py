import logging
import random

from typing import TYPE_CHECKING

import discord

from r2d20.bot import R2d20
from r2d20.games.lobby import LobbyView
from r2d20.games.players import PlayerBase
from .rules import rulesets
from .rules import BonesRules

__all__ = ['BonesGame']


logger = logging.getLogger(__name__)


class BonesPlayer(PlayerBase):
    """Keeps score in the dice game for a discord.Member"""
    def __init__(self, member: discord.Member, *,
                 init_dice: int = 0, init_dice_sides: int = 0, **kwargs):
        super().__init__(member)
        self.score: int = 0
        self.rolls: list[tuple[int, int]] = []
        for _ in range(init_dice):
            self.roll(init_dice_sides)

    def roll(self, sides):
        roll = int(random.randint(1, sides))
        self.rolls.append((sides, int(roll)))
        self.score += roll
        return roll


class BonesGame(discord.ui.View):
    def __init__(self, bot: R2d20, *, lobby: LobbyView, ruleset_name: str, **kwargs):
        super().__init__(**kwargs)
        self.bot = bot
        self.lobby = lobby
        self.orig_interaction = lobby.interaction
        if ruleset_name not in rulesets:
            raise ValueError(f"Ruleset {ruleset_name} not found")
        self.ruleset: BonesRules = rulesets[ruleset_name]
        self.target_score = int(self.ruleset.target_score)
        self.players = [BonesPlayer(member, **self.ruleset.asdict()) for member in self.lobby.members]

        self._current_player_index: int = 0
        self._player_marker = "👈"
        self._embed: discord.Embed = self._init_embed()

    @property
    def current_player(self) -> BonesPlayer | None:
        if self._current_player_index in range(len(self.players)):
            return self.players[self._current_player_index]
        
    @property
    def embed(self) -> discord.Embed:
        return self._embed

    @property
    def is_game_over(self) -> bool:
        return self.current_player is None

    @discord.ui.button(label='Roll', style=discord.ButtonStyle.green)
    async def roll(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_player.roll(self.ruleset.dice_sides)
        if self.current_player.score >= self.target_score:
            self._turn_end()
        else:
            self._update_results()
            self._embed.description = f'Target: **{self.target_score}**'
        #
        view = None if self.is_finished() else self
        await interaction.response.edit_message(embed=self._embed, view=view)

    @discord.ui.button(label='Stand', style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._turn_end()
        view = None if self.is_finished() else self
        await interaction.response.edit_message(embed=self._embed, view=view)
    
    async def interaction_check(self, interaction: discord.Interaction):
        allowed = interaction.user.id == self.current_player.id
        if not allowed:
            logger.debug(f"Interaction was not allowed: It is not {interaction.user.display_name}'s turn")
            await interaction.response.send_message("It's not your turn", ephemeral=True, delete_after=5.0)
        #
        return allowed        

    def _init_embed(self) -> discord.Embed:
        embed = discord.Embed(title=self.ruleset.title,
                              description=f'Target: **{self.target_score}**')
        first = True
        for player in self.players:
            field = self._create_player_embed_field(player, first)
            first = False
            embed.add_field(**field)
        #
        return embed

    def _turn_end(self):
        self._update_results(mark_player=False)
        
        if self.current_player.score == self.target_score and\
           self.ruleset.variant_rules is True:
            self._incriment_target()
        #
        self._current_player_index += 1
        if self.is_game_over:
            self._update_embed_for_game_complete()
            self.stop()
            self.clear_items()
            return
        
        # The game continues
        self._update_results(mark_player=True)
        self._embed.description = f"{self.current_player}'s turn"

    def _update_results(self, mark_player=True):
        field = self._create_player_embed_field(self.current_player, mark_player)
        self._embed.set_field_at(self._current_player_index, **field)

    def _create_player_embed_field(self, player: BonesPlayer, mark_player):
        score = player.score if player.score <= self.target_score else 'BUST!'
        name = f'{player.display_name} - Score: {score}'
        if mark_player:
            name += f' {self._player_marker}'
        value = self._visualise_results(player.rolls)
        inline = False
        return {'name': name, 'value': value, 'inline': inline}

    def _visualise_results(self, rolls: list[tuple[int, int]]) -> str:
        results = []
        for die, roll in rolls:
            die_name = f'd{die}'
            emoji = self.bot.get_cached_emoji(die_name)
            result = f'{emoji if emoji else (die_name)}{roll}'
            results.append(result)
        #
        return ' '.join(results)

    def _update_embed_for_game_complete(self):
        self._embed.set_footer(text="Game Over")
        scores_not_bust = [p.score for p in self.players if p.score <= self.target_score]
        if scores_not_bust:
            max_score = max(scores_not_bust)
            winners = [player for player in self.players if player.score == max_score]
            if len(winners) == 1:
                self._embed.description = f'{winners[0]} is the winner!'
            else:
                self._embed.description = f'{" and ".join(winners)} tied!'
        else:
            self._embed.description = f'Skill issue - No one won'

    def _incriment_target(self):
         self.target_score += 1
         self._embed.description = f'Target: **{self.target_score}**'

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
