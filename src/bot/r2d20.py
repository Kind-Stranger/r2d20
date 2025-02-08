import logging
import os

import discord
from discord.ext import commands

from definitions import COGS_DIR, RESOURCES_DIR, TEST_GUILDS
try:
    import config
except ImportError:
    config = None

logger = logging.getLogger()


class R2d20(commands.Bot):
    def __init__(self, command_prefix, *, intents: discord.Intents):
        super().__init__(command_prefix, intents=intents)
        self.help_command = commands.DefaultHelpCommand()

    async def on_ready(self):
        """Triggered by event when bot is logged in"""
        logger.info(f"Logged in as: {self.user}\n")
        logger.info(
            f"Using Discord Python API version {discord.__version__}\n")

    async def setup_hook(self):
        """Triggered before bot is logged in"""
        logger.debug("Executing setup hook")
        if hasattr(config, 'cogs') and config.cogs:
            for cog_name in config.cogs:
                await self.load_extension(f'cogs.{cog_name}')
                logger.info(f"Extension {cog_name} loaded")
        else:
            await self.load_all_cogs()
        #
        with open(os.path.join(RESOURCES_DIR, "welcome.txt")) as f:
            self.welcome_txt = f.read().strip()
        #
        for guild_id in TEST_GUILDS:
            logger.info("Syncing to test guild")
            try:
                await self.sync_to_guild(guild_id)
            except discord.DiscordException:
                logger.error("Failed to sync command tree to guild")

    async def sync_to_guild(self, guild_id: int):
        """Sync app_copmmands to a guild"""
        guild = discord.Object(id=guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def load_all_cogs(self):
        """Load every cog we can find"""
        logger.debug("Loading all cogs")
        for filename in os.listdir(COGS_DIR):
            cog_name, ext = os.path.splitext(filename)
            if cog_name.startswith('.') or cog_name.startswith('_'):
                continue
            if ext == '.py':
                await self.load_or_reload_extension(cog_name)

    async def load_or_reload_extension(self, cog_name: str) -> bool:
        """Load an extension or relaod it if it's already loaded

        Args:
            cog_name (str): Name of the cog to re/load

        Returns:
            bool: `True` if the `Cog` was loaded successfully
        """
        action = 'reload' if cog_name in self.extensions else 'load'
        try:
            if action == 'reload':
                await self.reload_extension(f'cogs.{cog_name}')
            else:
                await self.load_extension(f'cogs.{cog_name}')
        except Exception as ex:
            logger.exception(f"Cog {action} failed: {cog_name}")
            successful = False
        else:
            logger.info(f"Cog {action} successful: {cog_name}")
            successful = True
        #
        return successful

    async def on_guild_join(self, guild: discord.Guild):
        """Triggered when bot joins a server"""
        logger.info("Joined a guild!")
        try:
            await self.sync_to_guild(guild.id)
        except discord.DiscordException:
            logger.exception("Failed to sync commands to new guild")
        if self.welcome_txt and (welcome_channel := guild.system_channel):
            try:  # Just try instead of checking permission
                await welcome_channel.send(self.welcome_txt)
            except discord.ClientException:
                pass  # Oh well
