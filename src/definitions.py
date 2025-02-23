import os.path

import discord


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
COGS_DIR = os.path.join(ROOT_DIR, "cogs")
RESOURCES_DIR = os.path.join(ROOT_DIR, "resources")
TEST_GUILDS = [discord.Object(guild_id) for guild_id in filter(None, os.environ.get('TEST_GUILDS', "").split(','))]
HOME_GUILD = discord.Object(os.environ.get('HOME_GUILD'))
EMOJIS = {
    'd20': 1333222713082253342,
    'd12': 1333222832163000423,
    'd10': 1333222846125707365,
    'd8': 1333222856552742928,
    'd6': 1333222866946097222,
    'd4': 1333222875506802819,
    'rip': 1333222980972449823,
}
