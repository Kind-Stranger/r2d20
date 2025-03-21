import logging
import os

import discord

from .bot import R2d20


def run_bot():
    discord.utils.setup_logging(level=logging.DEBUG)
    intents = discord.Intents().default()
    intents.members = True
    bot = R2d20(intents=intents)
    bot.run(os.getenv('TOKEN'))


if __name__ == '__main__':
    run_bot()
