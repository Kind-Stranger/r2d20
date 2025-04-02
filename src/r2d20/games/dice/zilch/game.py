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

    @property
    def current_player(self) -> ZilchPlayer | None:
        if self._current_player_index in range(len(self.players)):
            return self.players[self._current_player_index]

    @property
    def is_game_over(self) -> bool:
        max_score = max(player.score for player in self.players)
        return max_score >= self.target_score

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
