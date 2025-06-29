import logging

from discord import app_commands, Interaction
from discord.ext import commands

from r2d20.bot import R2d20
from r2d20.definitions import HOME_GUILD, TEST_GUILDS
from r2d20.utils.connectivity import LLMSessionHandler

logger = logging.getLogger(__name__)


class LlamaCog(commands.Cog):
    def __init__(self, bot: R2d20):
        self.bot = bot

    @app_commands.command()
    async def ai(self, interaction: Interaction, prompt: str):
        await interaction.response.defer(thinking=True)
        res = self.bot.ai_session.send_prompt(prompt, stream=False)
        # res = prompt_ai(prompt)
        await interaction.edit_original_response(content=res)

    async def cog_app_command_error(self,
                                    ctx: Interaction,
                                    error: app_commands.AppCommandError):
        if ctx.response.is_done():
            await ctx.edit_original_response(content="There was a problem...")
        else:
            await ctx.response.send_message("There was a problem...")
        #
        logger.exception(error)


async def setup(bot: R2d20):
    bot.ai_session = LLMSessionHandler()
    bot.ai_session.init_session()
    logger.info("AI session initialized")
    await bot.add_cog(LlamaCog(bot), guilds=TEST_GUILDS)
