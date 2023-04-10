from env import GUILD_IDS, misc_emojis
from discord.ext import commands
from discord_slash import cog_ext, SlashContext

from utils.generic_dice_games import GenericDiceGame


class KoboldsKnucklesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name='kk',
        description="Play a game of Kobold's Knuckles",
        guild_ids=GUILD_IDS,
    )
    async def _kobolds_knuckles(self, ctx: SlashContext):
        game = GenericDiceGame(self.bot,
                               ctx,
                               title = "Kobold's Knuckles",
                               dice_sides = 4,
                               dice_emoji = self.bot.dice_emojis['d4'],
                               score_limit = 10,
                               init_dice = 1,
                               init_dice_sides = 6,
                               init_dice_emoji = misc_emojis['game_die'])
        await game.play_game()

def setup(bot):
    bot.add_cog(KoboldsKnucklesCog(bot))