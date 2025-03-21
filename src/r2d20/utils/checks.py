import logging

from discord import Interaction

logger = logging.getLogger(__name__)


async def is_owner(ctx: Interaction):
    """Check if the user activating the command is the bot's owner"""
    logger.debug("Invoked owner check")
    return await ctx.client.is_owner(ctx.user)
