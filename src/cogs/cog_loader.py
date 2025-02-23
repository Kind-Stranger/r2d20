import logging
from discord import Interaction, app_commands
from discord.ext import commands

from definitions import HOME_GUILD


class CogLoaderCog(commands.GroupCog, group_name='cog'):
    """TODO: Add description"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(name=self.qualified_name)

    @app_commands.command()
    @app_commands.guilds(HOME_GUILD)
    @commands.is_owner()
    async def reload(self, ctx: Interaction, cog_name: str):
        successful = await self.bot.load_or_reload_extension(cog_name)
        await ctx.response.send_message(
            ['Failed', 'Success'][successful],
            ephemeral=True
        )

    async def cog_app_command_error(self,
                                    ctx: Interaction,
                                    error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await ctx.response.send_message(
                "You are not allowed to use this command",
                ephemeral=True
            )
        else:
           self.logger.exception(error)
           await ctx.response.send_message("Unhandled error", ephemeral=True)


async def setup(bot):
    await bot.add_cog(CogLoaderCog(bot))
