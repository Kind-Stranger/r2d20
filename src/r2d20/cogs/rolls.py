import logging
import random

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from bot import R2d20
from utils.enums import Advantage
from utils.dice import NotationParseException, create_embed_from_notation

logger = logging.getLogger(__name__)


class DiceRolls(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: R2d20 = bot

    @app_commands.command()
    @app_commands.describe(dice_notation="Dice notation (see help for more)",
                           hidden="Roll in secret?")
    async def roll(self, interaction: Interaction, dice_notation: str, hidden: bool = False):
        """Roll dice using dice notation"""
        logger.debug(
            f"Command /roll invoked with arguments: dice_notation={dice_notation}, hidden={hidden}")
        embed = create_embed_from_notation(dice_notation)
        embed.set_author(name=interaction.user.display_name,
                         icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=hidden)

    @app_commands.command()
    @app_commands.describe(quantity="Number of dice to roll",
                           modifier="How much to add to the roll",
                           hidden="Roll in secret?",
                           advantage="Roll at advantage or disadvantage")
    async def d20(self, interaction: Interaction, quantity: int = 1, modifier: int = 0, advantage: Advantage = None,
                  hidden: bool = False):
        """Roll a d20"""
        await self.simple_roll(interaction, 20, quantity, modifier, advantage, hidden)

    @app_commands.command()
    @app_commands.describe(quantity="Number of dice to roll",
                           modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d100(self, interaction: Interaction, quantity: int = 1, modifier: int = 0, hidden: bool = False):
        """Roll a d100"""
        await self.simple_roll(interaction, 100, quantity, modifier, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(quantity="Number of dice to roll",
                           modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d12(self, interaction: Interaction, quantity: int = 1, modifier: int = 0, hidden: bool = False):
        """Roll a d12"""
        await self.simple_roll(interaction, 12, quantity, modifier, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(quantity="Number of dice to roll",
                           modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d10(self, interaction: Interaction, quantity: int = 1, modifier: int = 0, hidden: bool = False):
        """Roll a d10"""
        await self.simple_roll(interaction, 10, quantity, modifier, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(quantity="Number of dice to roll",
                           modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d8(self, interaction: Interaction, quantity: int = 1, modifier: int = 0, hidden: bool = False):
        """Roll a d8"""
        await self.simple_roll(interaction, 8, quantity, modifier, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(quantity="Number of dice to roll",
                           modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d6(self, interaction: Interaction, quantity: int = 1, modifier: int = 0, hidden: bool = False):
        """Roll a d6"""
        await self.simple_roll(interaction, 6, quantity, modifier, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(quantity="Number of dice to roll",
                           modifier="How much to add to the roll",
                           hidden="Roll in secret?")
    async def d4(self, interaction: Interaction, quantity: int = 1, modifier: int = 0, hidden: bool = False):
        """Roll a d4"""
        await self.simple_roll(interaction, 4, quantity, modifier, hidden=hidden)

    @app_commands.command()
    @app_commands.describe(hidden="Roll in secret?")
    async def newstats(self, interaction: Interaction, hidden: bool = False):
        """Roll a new set of character stats"""
        logger.debug(
            f"Command /newstats invoked with arguments: hidden={hidden}")
        results = self.genstats()
        results_str = ', '.join(map(str, results))
        embed = discord.Embed(title='Rolled New Stats',
                              description=results_str)
        embed.set_author(name=interaction.user.display_name,
                         icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=hidden)

    async def cog_app_command_error(self, interaction: Interaction,
                                    error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("You are not allowed to use this command")
        elif isinstance(error, app_commands.CommandInvokeError) and\
                isinstance(error.original, NotationParseException):
            await interaction.response.send_message(error.original.args[0])
        else:
            logger.exception(
                f"Unhandled error in command: /{interaction.command.qualified_name}")
            await interaction.response.send_message("There was a problem... I'm not surprised tbh.")

    async def simple_roll(self, interaction: Interaction, die: int,
                          quantity: int = 1, modifier: int = 0, advantage: Advantage = None, hidden: bool = False):
        """Roll a simple die"""
        logger.debug(
            f"Command /d{die} invoked with arguments: quantity={quantity}, modifier={modifier}, advantage={advantage}, hidden={hidden}")
        embed = self.create_embed_for_simple_roll(interaction, die,
                                                  quantity, modifier, advantage)
        await interaction.response.send_message(embed=embed, ephemeral=hidden)

    def create_embed_for_simple_roll(self, interaction: Interaction, die: int,
                                     quantity: int, modifier: int, advantage: Advantage = None) -> discord.Embed:
        """Create and embed for a dice roll

        Args:
            interaction (Interaction): Discord Interaction context
            die (int): type of die (number of sides)
            quantity (int): number of dice to roll
            modifier (int): Value to add tp the result of the roll
            advantage (Advantage, optional): Roll at advantage/disadvantage. Defaults to None.

        Returns:
            discord.Embed: Embed displaying information about the roll and result
        """
        mod_str = "" if modifier == 0 else f"{'+' if modifier >= 0 else '-'}{modifier}"
        if advantage is None or advantage == Advantage.NONE:
            quantity = 1 if quantity < 1 else quantity
            roll = sum([random.randint(1, die) for _ in range(quantity)])
            result = roll + modifier
            result_str = f"[**{roll}**]{mod_str} = {result}"
        elif advantage == Advantage.ADVANTAGE:
            quantity = 2 if quantity < 2 else quantity
            rolls = [random.randint(1, die) for _ in range(2)]
            result = max(rolls) + modifier
            result_str = f"[~~{min(rolls)}~~, **{max(rolls)}**]{mod_str} = {result}"
        elif advantage == Advantage.DISADVANTAGE:
            quantity = 2 if quantity < 2 else quantity
            rolls = [random.randint(1, die) for _ in range(quantity)]
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
        embed.set_author(name=interaction.user.display_name,
                         icon_url=interaction.user.avatar.url)
        return embed

    def genstats(self):
        """Generate raw stats for a new D&D Character"""
        results = []
        for _ in range(6):
            rolls = [random.randint(1, 6) for _ in range(4)]
            result = sum(sorted(rolls, reverse=True)[:-1])
            results.append(result)
        return sorted(results)


async def setup(bot: commands.Bot):
    await bot.add_cog(DiceRolls(bot))
