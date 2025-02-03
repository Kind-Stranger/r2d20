import logging
import os

import discord

from bot.r2d20 import R2d20

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(funcName)s: %(message)s',
    level=logging.DEBUG
)

intents = discord.Intents().default()
intents.members = True
bot = R2d20(command_prefix='/', intents=intents)


def main():
    bot.run(os.getenv('TOKEN'))
