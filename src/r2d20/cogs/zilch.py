import time

import discord
from discord import app_commands
from discord.ext import commands

from r2d20.bot import R2d20
from r2d20.definitions import TEST_GUILDS
from r2d20.games import zilch
from r2d20.games.lobby import LobbyView


class ZilchCog(commands.Cog):
    def __init__(self, bot: R2d20):
        self.bot = bot

    @app_commands.command(description="A dice game for two players")
    async def run_game(self, interaction: discord.Interaction):
        lobby = LobbyView(interaction,
                          lobby_title=f"{interaction.user.display_name}'s Zilch Lobby",
                          max_players=2)
        await interaction.response.send_message(embed=lobby.embed, view=lobby)
        await lobby.wait()
        time.sleep(1)
        game = zilch.ZilchGame(self.bot, interaction, members=lobby.members)
        await interaction.edit_original_response(embed=game.embed, view=game)
        await game.wait()


async def setup(bot: R2d20):
    await bot.add_cog(ZilchCog(bot), guilds=TEST_GUILDS)
