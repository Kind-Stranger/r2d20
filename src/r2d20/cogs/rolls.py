import logging
import random

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from bot import R2d20
from utils.enums import Advantage
from utils.roll_utils import genstats
from utils.dice import NotationParseException, create_embed_from_notation

logger = logging.getLogger(__name__)


class DiceRolls(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: R2d20 = bot

    @app_commands.command()
    @app_commands.describe(dice_notation="Dice notation (see help for more)",
                           hidden="Roll in secret?")
    async def roll(self, ctx: Interaction, dice_notation: str, hidden: bool = False):
        """Roll dice using dice notation"""
        logger.debug(
            f"Command /roll invoked with arguments: dice_notation={dice_notation}, hidden={hidden}")
        embed = create_embed_from_notation(dice_notation)
        embed.set_author(name=ctx.user.display_name,
                         icon_url=ctx.user.avatar.url)
        await ctx.response.send_message(embed=embed, ephemeral=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d100(self, ctx: Interaction, modifier: int = 0, hidden: bool = False):
        """Roll a d100"""
        await self.simple_roll(ctx, die=100, modifier=modifier, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?",
                           advantage="Roll at advantage or disadvantage")
    async def d20(self, ctx: Interaction, modifier: int = 0, advantage: Advantage = None,
                  hidden: bool = False):
        """Roll a d20"""
        await self.simple_roll(ctx, die=20, modifier=modifier, advantage=advantage, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d12(self, ctx: Interaction, modifier: int = 0, hidden: bool = False):
        """Roll a d12"""
        await self.simple_roll(ctx, die=12, modifier=modifier, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d10(self, ctx: Interaction, modifier: int = 0, hidden: bool = False):
        """Roll a d10"""
        await self.simple_roll(ctx, die=10, modifier=modifier, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d8(self, ctx: Interaction, modifier: int = 0, hidden: bool = False):
        """Roll a d8"""
        await self.simple_roll(ctx, die=8, modifier=modifier, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d6(self, ctx: Interaction, modifier: int = 0, hidden: bool = False):
        """Roll a d6"""
        await self.simple_roll(ctx, die=6, modifier=modifier, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d4(self, ctx: Interaction, modifier: int = 0, hidden: bool = False):
        """Roll a d4"""
        await self.simple_roll(ctx, die=4, modifier=modifier, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(hidden="Roll in secret?")
    async def newstats(self, ctx: Interaction, hidden: bool = False):
        """Roll a new set of character stats"""
        logger.debug(
            f"Command /newstats invoked with arguments: hidden={hidden}")
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
                isinstance(error.original, NotationParseException):
            await ctx.response.send_message(error.original.args[0])
        else:
            logger.exception(
                f"Unhandled error in command: /{ctx.command.qualified_name}")
            await ctx.response.send_message("There was a problem... I'm not surprised tbh.")

    async def simple_roll(self, ctx: Interaction, *,
                          die: int, modifier: int = 0, advantage: Advantage = None, hidden: bool = False):
        """Roll a simple die"""
        logger.debug(
            f"Command /d{die} invoked with arguments: modifier={modifier}, advantage={advantage}, hidden={hidden}")
        embed = self.create_embed_for_simple_roll(ctx, die=die, modifier=modifier, advantage=advantage)
        await ctx.response.send_message(embed=embed, ephemeral=hidden)

    def create_embed_for_simple_roll(self, ctx: Interaction, *,
                                     die: int, modifier: int, advantage: Advantage = None) -> discord.Embed:
        """Create and embed for a dice roll

        Args:
            ctx (Interaction): Discord Interaction context
            die (int): type of die (number of sides)
            modifier (int): Value tp add tp the result of the roll
            advantage (Advantage, optional): Roll at advantage/disadvantage. Defaults to Advantage.NONE.

        Returns:
            discord.Embed: Embed displaying information about the roll and result
        """
        mod_str = "" if modifier == 0 else f"{'+' if modifier >= 0 else '-'}{modifier}"
        if advantage is None or advantage == Advantage.NONE:
            roll = random.randint(1, die)
            result = roll + modifier
            result_str = f"[**{roll}**]{mod_str} = {result}"
        elif advantage == Advantage.ADVANTAGE:
            rolls = [random.randint(1, die) for _ in range(2)]
            result = max(rolls) + modifier
            result_str = f"[~~{min(rolls)}~~, **{max(rolls)}**]{mod_str} = {result}"
        elif advantage == Advantage.DISADVANTAGE:
            rolls = [random.randint(1, die) for _ in range(2)]
            result = min(rolls) + modifier
            result_str = f"[~~{max(rolls)}~~, **{min(rolls)}**]{mod_str} = {result}"
        #
        emoji = self.bot.get_cached_emoji(f'd{die}')
        result_str = f"Result: {result_str}"
        embed = discord.Embed(title=f"Rolled d{die}{mod_str}",
                              description=result_str)
        if emoji:
            embed.set_thumbnail(url=emoji.url)
        #
        embed.set_author(name=ctx.user.display_name,
                         icon_url=ctx.user.avatar.url)
        return embed


async def setup(bot: commands.Bot):
    await bot.add_cog(DiceRolls(bot))
