import logging
import os

import discord
from discord.ext import commands

from definitions import COGS_DIR, EMOJIS, RESOURCES_DIR, TEST_GUILDS
try:
    import config
except ImportError:
    config = None

__all__ = ['R2d20']

TEST_GUILDS: list[discord.Object]


class R2d20(commands.Bot):
    def __init__(self, command_prefix='/', *, intents: discord.Intents):
        super().__init__(command_prefix, intents=intents)
        self.logger = logging.getLogger(name=self.__class__.__name__)
        self.help_command = commands.DefaultHelpCommand()

    async def on_ready(self):
        """Triggered by event when bot is logged in"""
        self.logger.info(f"Logged in as: {self.user}\n")
        self.logger.info(
            f"Using Discord Python API version {discord.__version__}\n")

    async def setup_hook(self):
        """Triggered before bot is logged in"""
        self.logger.debug("Executing setup hook")
        if hasattr(config, 'cogs') and config.cogs:
            for cog_name in config.cogs:
                try:
                    await self.load_extension(f'cogs.{cog_name}')
                    self.logger.info(f"Extension {cog_name} loaded")
                except commands.ExtensionError:
                    self.logger.exception(
                        f"Failed to load extension: {cog_name}")
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
        if self.welcome_txt and (welcome_channel := guild.system_channel):
            try:  # Just try instead of checking permission
                await welcome_channel.send(self.welcome_txt)
            except discord.ClientException:
                pass  # Oh well

    async def get_app_emoji_by_name(self, name: str) -> discord.Emoji | None:
        """
        Retrieve an application emoji by its name.

        Args:
            name (str): The name of the emoji to retrieve.

        Returns:
            discord.Emoji | None: The emoji object if found, otherwise None.
        """
        self.logger.debug(f"Fetching emoji by name: {name}")
        id = EMOJIS.get(name)
        if id is None:
            self.logger.warning(f"Emoji not found in EMOJIS: {name}")
            return
        else:
            return await self.fetch_application_emoji(id)
