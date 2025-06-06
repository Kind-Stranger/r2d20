import logging

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from bot import R2d20
from definitions import HOME_GUILD
from utils.checks import is_owner

logger = logging.getLogger(__name__)


@app_commands.check(is_owner)
class BotAdminCog(commands.GroupCog, group_name='bot'):
    def __init__(self, bot: R2d20):
        self.bot = bot

    @app_commands.command()
    async def sync_guild(self, ctx: Interaction, guild_id: str = None):
        """Sync the command tree to the guild"""
        await ctx.response.send_message("Syncing...", ephemeral=True)
        guild = discord.Object(guild_id) if guild_id else ctx.guild
        # self.bot.tree.clear_commands(guild=guild)
        await self.bot.tree.sync(guild=guild)
        await ctx.edit_original_response(content="Synced")

    @app_commands.command()
    async def clear_guild(self, ctx: Interaction, guild_id: str = None):
        """Sync the command tree to the guild"""
        await ctx.response.send_message("Syncing...", ephemeral=True)
        guild = discord.Object(guild_id) if guild_id else ctx.guild
        self.bot.tree.clear_commands(guild=guild)
        await self.bot.tree.sync(guild=guild)
        await ctx.edit_original_response(content="Synced")

    @app_commands.command()
    async def sync_global(self, ctx: Interaction):
        """Sync the command tree"""
        await ctx.response.send_message("Syncing...", ephemeral=True)
        await self.bot.tree.sync()
        await ctx.edit_original_response(content="Synced")

    @app_commands.command()
    async def log_level(self, ctx: Interaction, level: str):
        """Set the bot's log level"""
        level = level.upper()
        for _logger in logging.root.manager.loggerDict.values():
            if isinstance(_logger, logging.Logger):
                _logger.setLevel(level)
        logger.info(f"Set log level to {level}")
        await ctx.response.send_message(f"Set log level to {level}")

    async def cog_app_command_error(self,
                                ctx: Interaction,
                                error: app_commands.AppCommandError):
        """Exception handling for this cog

        Args:
            ctx (Interaction): The interaction that failed
            error (app_commands.AppCommandError): The error that was raised
        """
        if isinstance(error, app_commands.CheckFailure):
            logger.debug("Failed command check")
            await ctx.response.send_message(
                "You are not allowed to use this command",
                ephemeral=True
            )
        else:
            logger.exception(error)
            if ctx.response.is_done():
                await ctx.response.edit_message(content="Unhandled error")
            else:
                await ctx.response.send_message("Unhandled error", ephemeral=True)


async def setup(bot: R2d20):
    await bot.add_cog(BotAdminCog(bot), guild=HOME_GUILD)
