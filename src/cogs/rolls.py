import random

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from definitions import EMOJIS
from utils.roll_utils import genstats
from utils.dice.parsing import NotationException, create_embed_from_notation

class DiceRolls(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(dice_notation="Dice notation (see help for more)",
                           hidden="Roll in secret?")
    async def roll(self, ctx: Interaction, dice_notation: str, hidden: bool = False):
        """Roll dice using dice notation"""
        embed = create_embed_from_notation(dice_notation)
        embed.set_author(name=ctx.user.display_name,
                         icon_url=ctx.user.avatar.url)
        await ctx.response.send_message(embed=embed, ephemeral=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d20(self, ctx: Interaction, modifier: int = 0, hidden: bool = False):
        """Roll a d20"""
        embed = embed_for_simple_roll(ctx, die=20, modifier=modifier)
        await ctx.response.send_message(embed=embed, ephemeral=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d12(self, ctx: Interaction, modifier: int = 0, hidden: bool = False):
        """Roll a d12"""
        embed = embed_for_simple_roll(ctx, die=12, modifier=modifier)
        await ctx.response.send_message(embed=embed, ephemeral=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d10(self, ctx: Interaction, modifier: int = 0, hidden: bool = False):
        """Roll a d10"""
        embed = embed_for_simple_roll(ctx, die=10, modifier=modifier)
        await ctx.response.send_message(embed=embed, ephemeral=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d8(self, ctx: Interaction, modifier: int = 0, hidden: bool = False):
        """Roll a d8"""
        embed = embed_for_simple_roll(ctx, die=8, modifier=modifier)
        await ctx.response.send_message(embed=embed, ephemeral=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d6(self, ctx: Interaction, modifier: int = 0, hidden: bool = False):
        """Roll a d6"""
        embed = embed_for_simple_roll(ctx, die=6, modifier=modifier)
        await ctx.response.send_message(embed=embed, ephemeral=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d4(self, ctx: Interaction, modifier: int = 0, hidden: bool = False):
        """Roll a d4"""
        embed = embed_for_simple_roll(ctx, die=4, modifier=modifier)
        await ctx.response.send_message(embed=embed, ephemeral=hidden)

    @app_commands.command()
    @app_commands.describe(hidden="Roll in secret?")
    async def newstats(self, ctx: Interaction, hidden: bool = False):
        """Roll a new set of character stats"""
        results = genstats()
        results_str = ', '.join(map(str, results))
        embed = discord.Embed(title='Rolled New Stats',
                              description=results_str)
        embed.set_author(name=ctx.user.display_name,
                        icon_url=ctx.user.avatar.url)
        await ctx.response.send_message(embed=embed, ephemeral=hidden)

    async def cog_app_command_error(self,
                                    ctx: Interaction,
                                    error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await ctx.response.send_message("You are not allowed to use this command")
        elif isinstance(error, app_commands.CommandInvokeError) and\
             isinstance(error.original, NotationException):
            await ctx.response.send_message(error.original.args[0])
        else:
            await ctx.response.send_message("There was a problem...")
            raise


async def setup(bot):
    await bot.add_cog(DiceRolls(bot))


def embed_for_simple_roll(ctx: Interaction, die: int, modifier: int):
    result = random.randint(1, die)
    mod_str = "" if modifier == 0 else f"{'+' if modifier >= 0 else '-'}{modifier}"
    emoji = ctx.client.get_emoji(EMOJIS[f"d{die}"])
    embed = discord.Embed(title=f"Rolled d{die}{mod_str}",
                          description=f"{emoji or "Result:"} {result}")
    embed.set_author(name=ctx.user.display_name,
                     icon_url=ctx.user.avatar.url)
    return embed
