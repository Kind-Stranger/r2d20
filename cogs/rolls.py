from discord.ext import commands
from discord_slash import SlashContext, cog_ext
# The below will `import discord` and override some of its stuff
from discord_slash.dpy_overrides import *
from discord_slash.model import SlashCommandOptionType

from env import GUILD_IDS
from main import emoji_replace
from utils.pranks import isAprFool
from utils.roll_utils import do_roll, genstats, parse_roll, roll_hp


class DiceRollsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(name='roll',
                       description='Roll a die',
                       options=[{'name':'dice_with_mods',
                                 'description': 'e.g. d20@adv+3 or 2d6+4',
                                 'type': SlashCommandOptionType.STRING,
                                 'required': True}],
                       guild_ids=GUILD_IDS)
    async def roll(self,
                   ctx: SlashContext,
                   dice_with_mods: str):
        """Slash command for rolling dice using dice notation"""
        diceNotationNoSpaces = str(dice_with_mods).replace(' ','')
        parsedNotation = parse_roll(diceNotationNoSpaces)
        results = do_roll(parsedNotation, self.bot.dice_emojis, isAprFool())
        question = ''.join([r[0] for r in results])
        question = emoji_replace(question, self.bot.dice_emojis, to_emoji=True)
        answer = eval(''.join([r[1] for r in results]))
        embed = discord.Embed(title=f'{diceNotationNoSpaces}',
                              description=f'{question} = {answer}')
        embed.set_author(name=ctx.author.display_name,
                         icon_url=ctx.author.avatar_url)
        await ctx.send(embeds=[embed])

    @cog_ext.cog_slash(name='rollstats',
                       description='Roll a new set of 6 stats',
                       guild_ids=GUILD_IDS)
    async def rollstats(self,
                        ctx: SlashContext):
        """Slash command for rolling a new set of six stats"""
        if isAprFool():
            results = [3]*6 # Minimum possible on April Fool's
        else:
            results = genstats()
        #
        results_str = ', '.join(map(str, sorted(results, reverse=True)))
        embed = discord.Embed(title='Rolled New Stats',
                              description=results_str)
        embed.set_author(name=ctx.author.display_name,
                         icon_url=ctx.author.avatar_url)
        await ctx.send(embeds=[embed])

    @cog_ext.cog_slash(name='hp',
                       description='Roll HP the special way',
                       options=[{'name': 'level',
                                 'description': 'Character level',
                                 'type': SlashCommandOptionType.INTEGER,
                                 'required': True},
                                {'name': 'hit_dice_sides',
                                 'description': 'Number of sides on character hit die',
                                 'type': SlashCommandOptionType.INTEGER,
                                 'required': True},
                                {'name': 'con_mod',
                                 'description': 'Constitution modifier (e.g. `+2` or `-1` or `0` etc.)',
                                 'type': SlashCommandOptionType.INTEGER,
                                 'required': True}],
                       guild_ids=GUILD_IDS)
    async def hp(self,
                 ctx: SlashContext,
                 level: int,
                 hit_dice_sides: int,
                 con_mod: str):
        """Roll hit points the way we like it"""
        results = roll_hp(level, hit_dice_sides)
        max_hp = sum(results)
        try:
            if con_mod.startswith('+'):
                max_hp += int(con_mod[1:]) * level
            elif con_mod.startswith('-'):
                max_hp -= int(con_mod[1:]) * level
            elif con_mod == '0':
                pass
            else:
                raise IOError("Invalid consitution modifier format")
        except Exception:
            await ctx.send('Invalid constitution modifier format. e.g. +2, -1, 0')
            return
        #
        embed = discord.Embed()
        embed.add_field(name='Level', value=f"{level}")
        embed.add_field(name='Hit Dice', value=f"d{hit_dice_sides}")
        embed.add_field(name='CON Modifier', value=f"{con_mod}")
        embed.add_field(name='Results', value=', '.join(map(str,results)))
        embed.add_field(name='Max Hit Points', value=f"{max_hp}", inline=False)
        embed.set_author(name=ctx.author.display_name,
                        icon_url=ctx.author.avatar_url)
        await ctx.send(embeds=[embed])
        
def setup(bot):
    bot.add_cog(DiceRollsCog(bot))
