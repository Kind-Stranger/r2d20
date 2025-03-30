import logging
from typing import Literal

from discord import Interaction, app_commands
from discord.ext import commands

from bot import R2d20
from definitions import HOME_GUILD
from r2d20 import config
from utils.checks import is_owner

logger = logging.getLogger(__name__)


@app_commands.check(is_owner)
class CogLoaderCog(commands.GroupCog, group_name='cog'):
    """TODO: Add description"""

    def __init__(self, bot: R2d20):
        self.bot = bot
        self.logger = logging.getLogger(name=self.qualified_name)

    @app_commands.command()
    @app_commands.describe(name_of_cog='Name of the cog')
    async def reload(self, ctx: Interaction, name_of_cog: str):
        """Reload a cog

        Args:
            ctx (Interaction): The interaction that triggered this function
            name_of_cog (Literal['test_cog']): Name of the cog
        """
        successful = await self.bot.load_or_reload_extension(name_of_cog)
        await ctx.response.send_message(
            ['Failed', 'Success'][successful],
            ephemeral=True
        )

    async def cog_app_command_error(self,
                                    ctx: Interaction,
                                    error: app_commands.AppCommandError):
        """Exception handling for this cog

        Args:
            ctx (Interaction): The interaction that failed
            error (app_commands.AppCommandError): The error that was raised
        """
        if isinstance(error, app_commands.CheckFailure):
            self.logger.debug("Failed command check")
            await ctx.response.send_message(
                "You are not allowed to use this command",
                ephemeral=True
            )
        else:
            self.logger.exception(error)
            await ctx.response.send_message("Unhandled error", ephemeral=True)


async def setup(bot: R2d20):
    await bot.add_cog(CogLoaderCog(bot), guild=HOME_GUILD)
