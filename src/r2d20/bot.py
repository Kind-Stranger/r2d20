import logging
import os

import discord
from discord.ext import commands

from definitions import COGS_DIR, EMOJIS, HOME_GUILD, RESOURCES_DIR, TEST_GUILDS
try:
    import config
except ImportError:
    config = None
    
__all__ = ['R2d20']

logger = logging.getLogger(__name__)

TEST_GUILDS: list[discord.Object]


class R2d20(commands.Bot):
    def __init__(self, command_prefix=None, *, intents: discord.Intents):
        super().__init__(command_prefix, intents=intents)
        self.help_command = commands.DefaultHelpCommand()
        self._emoji_cache: dict[str, discord.Emoji] = {}

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
                try:
                    await self.load_extension(f'cogs.{cog_name}')
                    logger.info(f"Extension {cog_name} loaded")
                except commands.ExtensionError:
                    logger.exception(
                        f"Failed to load extension: {cog_name}")
        else:
            await self.load_all_cogs()
        #
        for guild in TEST_GUILDS:
            cmds = await self.tree.sync(guild=guild)
            logger.debug(f"Commands synced: {cmds}")
        with open(os.path.join(RESOURCES_DIR, "welcome.txt")) as f:
            self.welcome_text = f.read().strip()
        #
        await self._cache_application_emojis()

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
        cog_path = f"cogs.{cog_name}"
        action = 'reload' if cog_path in self.extensions else 'load'
        logger.debug(f"{action}ing {cog_path}")
        try:
            if action == 'reload':
                await self.reload_extension(cog_path)
            else:
                await self.load_extension(cog_path)
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
        if self.welcome_txt and (welcome_channel := guild.system_channel):
            try:  # Just try instead of checking permission
                await welcome_channel.send(self.welcome_txt)
            except discord.ClientException:
                pass  # Oh well

    async def _cache_application_emojis(self):
        logger.debug("Initalising emoji cache")
        for emoji in await self.fetch_application_emojis():
            self._cache_emoji(emoji)

    def _cache_emoji(self, emoji: discord.Emoji):
        self._emoji_cache[emoji.name] = emoji

    def get_cached_emoji(self, name: str) -> discord.Emoji | None:
        return self._emoji_cache.get(name)

    async def fetch_app_emoji_by_name(self, name: str) -> discord.Emoji | None:
        """Retrieve an application emoji by its name.

        Args:
            name (str): The name of the emoji to retrieve.

        Returns:
            discord.Emoji: The emoji object if found, otherwise None.
        """
        logger.debug(f"Fetching emoji by name: {name}")
        if name in self._emoji_cache:
            return self._emoji_cache.get(name)
        elif name in EMOJIS:
            id = EMOJIS[name]
            emoji = await self.fetch_application_emoji(id)
            self._cache_emoji(name, emoji)
            return emoji
        else:
            logger.warning(f"Emoji not found in EMOJIS: {name}")

