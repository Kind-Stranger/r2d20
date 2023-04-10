from env import GUILD_IDS, misc_emojis
from discord.ext import commands
from discord_slash import cog_ext, SlashContext

from utils.generic_dice_games import GenericDiceGame


class BBVariantCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name='bb2',
        description="Baldur's Bones with increasing target if it's hit",
        guild_ids=GUILD_IDS,
    )
    async def _variant_bb(self, ctx: SlashContext):
        game = GenericDiceGame(self.bot,
                               ctx,
                               title = "Baldur's Bones (Variant)",
                               dice_sides = 6,
                               dice_emoji = misc_emojis['game_die'],
                               score_limit = 21,
                               init_dice = 3,
                               variant_rules=True)
        await game.play_game()

def setup(bot):
    bot.add_cog(BBVariantCog(bot))