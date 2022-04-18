import sys
import asyncio
import random
import time

from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_components import create_actionrow
from discord_slash.utils.manage_components import wait_for_component
from discord_slash.utils.manage_components import ComponentContext
from discord_slash.utils.manage_components import create_button
from discord_slash.model import ButtonStyle
# The below will `import discord` and override some of its stuff
from discord_slash.dpy_overrides import *

from env import misc_emojis, test_id, home_id
from utils.players import gather_players
from utils.players import PlayerBase
from utils.num2words import num2words

class LiarsDiceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name='liarsdice',
        description="Liar's Dice/Perudo",
        guild_ids=[test_id, home_id],
    ):
    async def liarsdice(self, ctx: SlashContext):
        game = LiarsDiceGame(self.bot, ctx)
        await game.play()

class LiarsDiceGame:
    def __init__(self,
                 bot: commands.Bot,
                 ctx: SlashContext,
                 max_players: int = 8,
                 timeout: int = 600):
        self.bot = bot
        self.ctx = ctx
        self.game_owner = ctx.author
        self.players = [self.game_owner]
        self.max_players = int(max_players)
        #
        self.timeout = int(timeout)
        if self.timeout < 0:
            self.timeout *= -1
        #
        self.game_msg = None

    def init_embed(self):
        embed = discord.Embed(title=str("Liar's Dice"),
                              colour=discord.Colour.random())
        embed.set_author(name=self.game_owner.display_name,
                              icon_url=self.game_owner.avatar_url)
        # Game Image
        embed.set_thumbnail(url='https://is3-ssl.mzstatic.com/image/thumb/Purple62/v4/d2/1d/f8/d21df8ea-77d3-1699-29ee-1aa1234fce32/source/512x512bb.jpg')
        self.game_msg = await self.ctx.send(embeds=[embed])
        return (self.game_msg, embed)

    def get_players(self, game_msg: discord.Message):
        self.players = [ LiarsDicePlayer(player) for player in
                         await gather_players(
                             self.bot,
                             game_msg = self.game_msg,
                             game_owner = self.game_owner,
                             existing_players = self.players,
                             max_players = int(self.max_players),
                             timeout = int(self.timeout)) ]
        return self.players

    def play(self):
        em = misc_emojis
        try:
            game_msg, embed = init_embed()
            players = self.get_players(game_msg)
            bet_btn = self.get_bet_button()
            challenge_btn = self.get_pass_button()
            player_index = 0

            while 1:
                # Hidden msaage for each player's rolls
                for p in players:
                    if not p.dice: # Out of the game
                        continue
                    rolls = p.roll()
                    roll_str = ''.join(f'{game_die}{r}' for r in rolls)
                    await p.dm_channel.send(content=roll_str)
                #
                challenge_btn['disabled'] = True
                max_bet = None
                max_better = None
                while 1:
                    p = players[player_index]
                    if not p.dice or p.has_passed: # Out of the game/round
                        continue
                    if max_bet:
                        quant = num2words(max_bet[0])
                        val = num2words(max_bet[1], plural=max_bet[0]>1)
                        foot_text = f'{max_better} bet {quant} {val}.\n'
                    else:
                        foot_text = ''
                    #
                    p_name = f'{player_index+1} {p.display_name}'
                    foot_text +=  f"{p_name}, make a bet!")
                    embed.set_footer(text=foot_text)
                    #
                    if not max_bet:
                        min_q = 1
                    else:
                        min_q = max_bet[0]
                    #
                    max_q = sum(len(p.dice) for p in players)
                    quantity_select = self.get_quantity_select(min_q, max_q))
                    value_select = self.get_value_select()
                    actionrow = create_actionrow(quantity_select,
                                                 value_select,
                                                 bet_btn,
                                                 challenge_btn)
                    
                    await game_msg.edit(embeds=[embed],
                                        components=[actionrow])

                    def is_current_player(ctx: ComponentContext):
                        return ctx.author_id = p.id

                    quant = 0
                    val = 0
                    while 1:
                        btn_ctx: ComponentContext = \
                            await wait_for_component(self.bot,
                                                     messages=[game_msg],
                                                     components=[actionrow],
                                                     check=current_player,
                                                     timeout=int(self.timeout))
                        if quantity_select['custom_id'] == btn_ctx.custom_id:
                            quant = int(ctx.selected_options[0])
                            update = False
                            if quant > 1:
                                old_vs_id = str(value_select['custom_id'])
                                value_select = self.get_value_select(plural=True)
                                value_select['custom_id'] = old_vs_id
                                update = True
                            if quant and val:
                                bet_btn['disabled'] = False
                                update = True
                            #
                            if update:
                                await game_msg.edit(embeds=[embed],
                                                    components=[actionrow])
                            #
                        elif value_select['custom_id'] == btn_ctx.custom_id:
                            val = int(ctx.selected_options[0])
                            if quant and val:
                                bet_btn['disabled'] = False
                                await game_msg.edit(embeds=[embed],
                                                    components=[actionrow])
                                
                        elif bet_btn['custom_id'] == btn_ctx.custom_id:
                            max_bet = (quant, val)
                            max_better = p
                            player_index = self.get_next_player_index(
                                players, player_index)
                            challenge_btn['disabled'] = False
                            await game_msg.edit(embeds=[embed],
                                                components=[actionrow])
                            break
                        elif challenge_btn['custom_id'] == btn_ctx.custom_id:
                            break
                        #


        except asyncio.TimeoutError:
            if self.game_msg and self.game_msg.embeds:
                embed = self.game_msg.embeds[0]
                s = misc_emojis['stop_sign']
                embed.set_footer(text=f'{s} The game has timed out {s}')
                await self.game_msg.edit(embed=embed)
            else:
                sys.stderr.write('No game_msg')
            #
            sys.stderr.flush()
        #
        except discord.errors.NotFound:
            # Deleted the ctx?
            pass
    
    def get_quantity_select(self, min_q: int, max_q: int):
        # Ensure min is not greater than max
        if min_q > max_q:
            min_q = max_q
        # Can't have more than 25 options in a select
        if max_q > min_q + 25:
            max_q = min_q + 25
        # Create the select
        return create_select(
            placeholder = 'Choose number of dice...',
            min_values = 1,
            max_values = 1,
            options = [ create_select_option(label=num2words(n),
                                             value=str(n))
                        for n in range(min_q, max_q + 1) ],
        )

    def get_value_select(self, plural=False):
        return create_select(
            placeholder = 'Choose dice value...',
            min_values = 1,
            max_values = 1,
            options = [ create_select_option(label=num2words(n, plural=plural),
                                             value=str(n),
                                             emoji=misc_emojis[str(n)])
                        for n in range(1,7) ],
        )

    def get_bet_button(self):
        return create_button(
            style=ButtonStyle.green,
            label='BET!',
        )

    def get_pass_button(self):
        return create_button(
            style=ButtonStyle.red,
            label='Pass',
        )
        
    def get_next_player_index(self, players, player_index):
        next_player_index = int(player_index) + 1
        while 1:
            if next_player_index > len(players):
                next_player_index = 0
            #
            if next_player_index == player_index:
                return None
            elif len(players[next_player_index].dice) == 0:
                next_player_index += 1
            else:
                return next_player_index

class LiarsDicePlayer(PlayerBase):
    def __init__(self, member: dicord.Member):
        super().__init__(member)
        self.dice = [1] * 5
        
    def roll(self):
        self.dice = [ random.randint(6) for d in self.dice ]
        return self.dice

    def lose_dice(self):
        del self.dice[0]

def setup(bot):
    bot.add_cog(GenericDiceGameCog(bot))
