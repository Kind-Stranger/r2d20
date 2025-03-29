import time

import discord
from discord import app_commands
from discord.ext import commands

from r2d20.bot import R2d20
from r2d20.definitions import TEST_GUILDS
from r2d20.games import bones
from r2d20.games.lobby import LobbyView


class BonesCog(commands.GroupCog, name='bones'):
    def __init__(self, bot: R2d20):
        self.bot = bot
        for name in bones.rulesets:
            ruleset: bones.BonesRules = bones.rulesets[name]
            command = app_commands.Command(name=name, description=ruleset.description,
                                           parent=self, callback=self.run_game)
            self.app_command.add_command(command)

    async def run_game(self, interaction: discord.Interaction):
        ruleset_name = interaction.command.name
        ruleset: bones.BonesRules = bones.rulesets[ruleset_name]
        lobby = LobbyView(interaction, lobby_title=f"{interaction.user.display_name}'s {ruleset.title} Lobby")
        await interaction.response.send_message(embed=lobby.embed, view=lobby)
        await lobby.wait()
        time.sleep(1)
        game = bones.BonesGame(self.bot, lobby=lobby, ruleset_name=ruleset_name)
        await interaction.edit_original_response(embed=game.embed, view=game)
        await game.wait()


async def setup(bot: R2d20):
    await bot.add_cog(BonesCog(bot), guilds=TEST_GUILDS)
