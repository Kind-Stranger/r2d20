import asyncio
import random
from typing import List

from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_components import create_actionrow
from discord_slash.utils.manage_components import spread_to_rows
from discord_slash.utils.manage_components import wait_for_component
from discord_slash.utils.manage_components import ComponentContext
from discord_slash.utils.manage_components import create_button
from discord_slash.model import ButtonStyle
# The below will `import discord` and override some of its stuff
from discord_slash.dpy_overrides import *

from env import misc_emojis, HOME_ID, TEST_ID
from utils.players import gather_players
from utils.players import PlayerBase


n2w =  {1:"One",  2:"Two",  3:"Three",  4:"Four",  5:"Five",  6:"Six"}
n2ws = {1:"Ones", 2:"Twos", 3:"Threes", 4:"Fours", 5:"Fives", 6:"Sixes"}

class ZilchCog(commands.Cog):
    """The description for Zilch goes here."""

    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name='zilch',
        description='Yet another dice game. 2 players required.',
        guild_ids=[TEST_ID, HOME_ID],
    )
    async def _zilch(self, ctx: SlashContext):
        game = Zilch(self.bot, ctx)
        await game.play_game()
    
class Zilch:
    def __init__(self,
                 bot,
                 ctx: SlashContext,
                 *,
                 timeout: int = 600):
        self.bot = bot
        self.ctx = ctx
        self.timeout = int(timeout)
        self.game_msg = None
        self.game_owner = self.ctx.author
        self.players = [self.game_owner]

    async def get_players(self):
        embed = discord.Embed(title="Zilch",
                              colour=discord.Colour.random())
        embed.set_author(name=self.game_owner.display_name,
                              icon_url=self.game_owner.avatar_url)
        # Picture of dice
        embed.set_thumbnail(url='https://i.imgur.com/uCMhejd.png')
        self.game_msg = await self.ctx.send(embeds=[embed])

        # Gather players
        self.players = [ ZilchPlayer(player) for player in
                         await gather_players(
                             self.bot,
                             game_msg = self.game_msg,
                             game_owner = self.game_owner,
                             existing_players = self.players,
                             max_players = 2,
                             timeout = int(self.timeout)) ]

    async def get_buttons(self):
        game_msg = self.game_msg
        roll_btn = create_button(
            style=ButtonStyle.green,
            label='ROLL',
            custom_id=f'roll_{game_msg.id}',
        )
        bank_btn = create_button(
            style=ButtonStyle.green,
            label='BANK',
            custom_id=f'bank_{game_msg.id}',
        )
        main_row = create_actionrow(roll_btn, bank_btn)
        #
        scoreset_btns = [
            create_button(
                style=ButtonStyle.blue,
                label='⭐',
                custom_id=f's{i+1}_{game_msg.id}',
            ) for i in range(3)
        ]
        scoreset_btn_ids = [ i['custom_id'] for i in scoreset_btns ]
        scoreset_row = create_actionrow(*scoreset_btns)
        #
        dice_btns = [
            create_button(
                style=ButtonStyle.blue,
                label=f'{d_emojis[i]}{unlocked}',
                custom_id=f'd{i+1}_{game_msg.id}',
            ) for i in range(6)
        ]
        dice_btn_ids = [ i['custom_id'] for i in dice_btns ]
        dice_rows = spread_to_rows(*dice_btns, max_in_row=3)
        return main_row, scoreset_row, dice_rows

    async def play_game(self):
        try:
            unlocked = '🔓'
            locked = '🔒'
            d_emojis = [ '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣' ]
            last_turn = False
            await self.get_players()
            players = self.players   # for ease
            game_msg = self.game_msg # for more ease
            embed = game_msg.embeds[0]
            #
            all_rows = self.get_buttons()
            main_row, scoreset_row, *dice_rows = all_rows

            def player_in_game(ctx: ComponentContext):
                return ctx.author_id in [ player.id for player in players ]

            embed.add_field(name='placeholder', value='where the dice go',
                            inline=False)
            pos = 0
            try:
                while True:
                    p = players[pos] # For ease
                    p.init_dice()
                    roll_str = '\n'.join(f'{d_emojis[i]}🎲{p.dice[i].score}'
                                         for i in range(len(p.dice)))
                    embed.set_field_at(-1,
                                       name=f"{p.display_name}', you're up",
                                       value=f'{roll_str}')
                    # Disable all buttons except ROLL
                    for ar in all_rows:
                        for comp in ar['components']:
                            if comp['custom_id'] == roll_btn['custom_id']:
                                comp['disabled'] = False
                            else:
                                comp['disabled'] = True
                            #
                        #
                    #
                    await game_msg.edit(embeds=[embed],
                                        components=all_rows)
                    die_pos = []
                    while True:
                        btn_ctx: ComponentContext = \
                            await wait_for_component(self.bot,
                                                     messages=[game_msg],
                                                     components=all_rows,
                                                     check=player_in_game,
                                                     timeout=30)
                        if btn_ctx.custom_id in dice_btn_ids:
                            pass
                        elif btn_ctx.custom_id in scoreset_btn_ids:
                            pass
                        elif btn_ctx.custom_id == bank_btn['custom_id']:
                            p.bank()
                            if p.score_total >= self.score_limit:
                                last_turn = True
                            # Disable all buttons except ROLL
                            for ar in all_rows:
                                for comp in ar['components']:
                                    if comp['custom_id'] == roll_btn['custom_id']:
                                        comp['disabled'] = False
                                    else:
                                        comp['disabled'] = True
                                    #
                                #
                            # Next player
                            break
                        elif btn_ctx.custom_id == roll_btn['custom_id']:
                            # roll_btn['disabled'] = True
                            scoresets = self.check_roll(p.roll())
                            roll_str = '\n'.join(f'{d_emojis[i]}🎲{p.dice[i].score}'
                                                 for i in range(len(p.dice)))
                            embed.set_field_at(-1,
                                               name=f"{p.display_name}, you're up",
                                               value=f'{roll_str}')
                            for i in range(len(scoreset_btns)):
                                if i < len(scoresets):
                                    name, score, dp = scoresets[i]
                                    dp = [n for n in dp if n not in die_pos]
                                    die_pos.extend(dp)
                                    scoreset_btns[i]['label'] = f'{name}\n{score}'
                                    scoreset_btns[i]['disabled'] = False
                                else:
                                    scoreset_btns[i]['label'] = '⭐'
                                    scoreset_btns[i]['disabled'] = True
                                #
                            #
                            for i in range(len(dice_btns)):
                                if p.dice[i].is_locked:
                                    dice_btns[i]['disabled'] = True
                                elif p.dice[i].score in [1,5]:
                                    dice_btns[i]['disabled'] = False
                                else:
                                    dice_btns[i]['disabled'] = True
                                #
                            #
                            main_row = create_actionrow(roll_btn, bank_btn)
                            scoreset_row = create_actionrow(*scoreset_btns)
                            dice_rows = spread_to_rows(*dice_btns, max_in_row=3)
                            all_rows = [main_row, scoreset_row, *dice_rows]
                            
                            await btn_ctx.edit_origin(embeds=[embed],
                                                      components=all_rows)
                    
            finally:
                try:
                    # Try to just clean up the buttons
                    await game_msg.edit(components=[])
                except Exception:
                    pass
        except asyncio.TimeoutError:
            try:
                # Check the message is still there
                msg = await self.game_msg.channel.fetch_message(self.game_msg.id)
                embed = msg.embeds[0]
                s = misc_emojis['stop_sign']
                embed.set_footer(text=f'{s} The game has timed out {s}')
                await msg.edit(embed=embed)
            except Exception:
                pass
        except discord.errors.NotFound:
            # Deleted the message?
            pass


    def check_roll(self, rolls: List[int]):
        counts = {n:rolls.count(n) for n in range(1,7)}
        scores = []
        # Specials
        if sorted(rolls) == [1,2,3,4,5,6]:
            scores.append(("Straight", 1500, range(0, len(rolls)))) # ALL
        elif list(counts.values()).count(2) == 3:
            scores.append(("Three Pairs", 1000, range(0, len(rolls)))) # ALL
        else:
            # Sets of 3 or more
            for n in counts.keys():
                cnt = int(counts[n])
                if cnt >= 3:
                    score = 1000 if n == 1 else n*100
                    while cnt > 3:
                        score = score*2
                        cnt-=1
                    # n2w = number to word, n2ws is plurals
                    scores.append((f'{n2w[counts[n]]} {n2ws[n]}', score,
                                   [i for i,x in enumerate(rolls) if x == n]))
                #
            #
            if counts[1] == 1:
                scores.append(("Single One", 100,
                               [i for i,x in enumerate(rolls) if x == 1]))
            elif counts[1] == 2:
                scores.append(("Two Ones", 200,
                               [i for i,x in enumerate(rolls) if x == 1]))
            if counts[5] == 1:
                scores.append(("Single Five", 50,
                               [i for i,x in enumerate(rolls) if x == 5]))
            elif counts[5] == 2:
                scores.append(("Two Fives", 100,
                               [i for i,x in enumerate(rolls) if x == 5]))
            #
            if not scores and len(rolls) == 6:
                scores.append(("Nothing!", 500, range(0, len(rolls))))
            #
        #
        return scores

class ZilchPlayer(PlayerBase):
    def __init__(self, member: discord.Member):
        super().__init__(member)
        self.dice = None
        self.score_total = 0
        self.score_hist = []

    def init_dice(self):
        if self.dice:
            for die in self.dice:
                die.unlock()
        else:
            self.dice = [ ZilchDie() for _ in range(6) ]

    def roll(self):
        for die in self.dice:
            die.roll()
        return [ d.score for d in self.dice if not d.is_locked ]

    def bank(self):
        self.score_hist.append(self.score)
        self.score_total += self.score
        self.score = 0

class ZilchDie:
    def __init__(self):
        self.score = 1
        self.reset()

    def unlock(self):
        self.is_held = False
        self.is_locked = False
        
    def roll(self):
        if self.is_held:
            self.is_locked = True
        else:
            self.score = random.randint(1,6)


def setup(bot):
    bot.add_cog(ZilchCog(bot))
