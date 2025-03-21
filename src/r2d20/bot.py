import logging
import os

import discord
from discord.ext import commands

from .utils.definitions import COGS_DIR, RESOURCES_DIR
try:
    import config
except ImportError:
    config = None

__all__ = ['bot', 'R2d20']


class R2d20(commands.Bot):
    def __init__(self, command_prefix='/', *, intents: discord.Intents):
        super().__init__(command_prefix, intents=intents)
        self.logger = logging.getLogger(name=self.__class__.__name__)
        self.help_command = commands.DefaultHelpCommand()

    async def on_ready(self):
        """Triggered by event when bot is logged in"""
        # for guild in TEST_GUILDS:
        #     self.logger.info("Syncing to test guild")
        #     try:
        #         self.tree.clear_commands(guild=guild)
        #         self.tree.copy_global_to(guild=guild)
        #         await self.tree.sync(guild=guild)
        #     except discord.DiscordException:
        #         self.logger.error("Failed to sync command tree to guild")
        # await self.tree.sync()
        self.logger.info(f"Logged in as: {self.user}\n")
        self.logger.info(
            f"Using Discord Python API version {discord.__version__}\n")

    async def setup_hook(self):
        """Triggered before bot is logged in"""
        self.logger.debug("Executing setup hook")

        if hasattr(config, 'cogs') and config.cogs:
            for cog_name in config.cogs:
                await self.load_extension(f'cogs.{cog_name}')
                self.logger.info(f"Extension {cog_name} loaded")
        else:
            await self.load_all_cogs()
        #
        with open(os.path.join(RESOURCES_DIR, "welcome.txt")) as f:
            self.welcome_txt = f.read().strip()
        #

    async def load_all_cogs(self):
        """Load every cog we can find"""
        self.logger.debug("Loading all cogs")
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
        cog_path = f"cogs.{cog_name}"
        action = 'reload' if cog_path in self.extensions else 'load'
        self.logger.debug(f"{action}ing {cog_path}")
        try:
            if action == 'reload':
                await self.reload_extension(cog_path)
            else:
                await self.load_extension(cog_path)
        except Exception as ex:
            self.logger.exception(f"Cog {action} failed: {cog_name}")
            successful = False
        else:
            self.logger.info(f"Cog {action} successful: {cog_name}")
            successful = True
        #
        return successful

    async def on_guild_join(self, guild: discord.Guild):
        """Triggered when bot joins a server"""
        self.logger.info("Joined a guild!")
        try:
            await self.sync_to_guild(guild.id)
        except discord.DiscordException:
            self.logger.exception("Failed to sync commands to new guild")
        if self.welcome_txt and (welcome_channel := guild.system_channel):
            try:  # Just try instead of checking permission
                await welcome_channel.send(self.welcome_txt)
            except discord.ClientException:
                pass  # Oh well
