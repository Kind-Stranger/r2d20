import sys
import asyncio
import random
import time

from typing import Union

from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_components import create_actionrow
from discord_slash.utils.manage_components import wait_for_component
from discord_slash.utils.manage_components import ComponentContext
from discord_slash.utils.manage_components import create_button
from discord_slash.model import ButtonStyle
# The below will `import discord` and override some of its stuff
from discord_slash.dpy_overrides import *

from env import GUILD_IDS, misc_emojis
from utils.players import gather_players
from utils.players import PlayerBase

class GenericDiceGameCog(commands.Cog):
    """
    Template for a generic dice game where the objective is to score as close
    to the target as possible without going over it ("bust").

    Args:
        bot              : The discord bot object used to run the game
        title       (str): The name of the game
        dice_sides  (int): No. of sides on dice used to play the game
        dice_emoji       : Emoji used for playing the game
        score_limit (int): Score over which players 'bust'
        init_dice   (int): (optional) No. of dice rolled at start of game
        init_dice_sides(int): (optional) No. of sides on `init_dice`
                               *Reqd. if `init_dice` is non-zero AND
                               `init_dice_sides` is different to `dice_sides`**
        init_dice_emoji  : (optional) Emoji used to represent `init_dice`
                            *Reqd. if `init_dice` is non-zero AND
                            `init_dice_sides` is different to `dice_sides`*
        how_to_play (str): (optional) User instructions for the game
        timeout     (int): Seconds before game times out (0 means no timeout)
    """

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
        
    @cog_ext.cog_slash(
        name='kk2',
        description="Kobold's Knuckles with increasing target if it's hit",
        guild_ids=GUILD_IDS,
    )
    async def _variant_kk(self, ctx: SlashContext):
        game = GenericDiceGame(self.bot,
                               ctx,
                               title = "Kobold's Knuckles (Variant)",
                               dice_sides = 4,
                               dice_emoji = self.bot.dice_emojis['d4'],
                               score_limit = 10,
                               init_dice = 1,
                               init_dice_sides = 6,
                               init_dice_emoji = misc_emojis['game_die'],
                               variant_rules=True)
        await game.play_game()
        
    @cog_ext.cog_slash(
        name='bb',
        description="Play a game of Baldur's Bones",
        guild_ids=GUILD_IDS,
    )
    async def _baldurs_bones(self, ctx: SlashContext):
        game = GenericDiceGame(self.bot,
                               ctx,
                               title = "Baldur's Bones",
                               dice_sides = 6,
                               dice_emoji = misc_emojis['game_die'],
                               score_limit = 21,
                               init_dice = 3)
        await game.play_game()

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

class GenericDiceGame:
    def __init__(self,
                 bot,
                 ctx: SlashContext,
                 *,
                 title: str = None,
                 dice_sides: int = 0,
                 dice_emoji: Union[str, discord.Emoji] = None,
                 init_dice: int = 0,
                 init_dice_sides: int = 0,
                 init_dice_emoji: Union[str, discord.Emoji] = None,
                 score_limit: int = 0,
                 how_to_play: str = None,
                 timeout: int = 600,
                 max_players: int = 10,
                 variant_rules=False):
        self.ctx = ctx
        self.bot = bot
        self.title = title
        self.dice_sides = int(dice_sides)
        self.dice_emoji = dice_emoji
        if not dice_emoji:
            self.dice_emoji = ''
        #
        self.init_dice = int(init_dice)
        if self.init_dice < 0:
            self.init_dice = 0
        #
        self.init_dice_sides = int(init_dice_sides)
        self.init_dice_emoji = init_dice_emoji
        if init_dice > 0:
            if init_dice_sides == 0:
                self.init_dice_sides = self.dice_sides
            #
            if self.init_dice_emoji == None:
                self.init_dice_emoji = self.dice_emoji
            #
        #
        self.score_limit = int(score_limit)
        self.how_to_play = how_to_play
        if self.how_to_play == None:
            if init_dice > 0:
                how_to_play = (
                    f'• Each player rolls {init_dice}'
                    f' {init_dice_sides}-sided dice.\n'
                )
            else:
                how_to_play = ""
            #
            how_to_play += (
                'Play proceeds clockwise around the table, with the host of'
                ' the game going last.\n'
                '• On their turn, a player can choose to "stand" or "roll".'
                ' If the player stands, the next player can take a turn.'
                ' A player who rolls takes an additional'
                f' {dice_sides}-sided die and rolls it. If the total of'
                f' their dice exceeds {score_limit}, they "bust" and are'
                ' out of the game. Otherwise, they can keep rolling additional'
                f' {dice_sides}-sided dice until they either stand or'
                ' bust.\n'
                '• After everyone has had a turn, the highest point total'
                ' (excluding players who busted) wins the game and takes the'
                'pot.'
            )
            self.how_to_play = how_to_play
        #
        self.timeout = int(timeout)
        if self.timeout < 0:
            self.timeout *= -1
        #
        self.max_players = int(max_players)
        self.variant_rules = bool(variant_rules)
        self.game_msg = None
        self.game_owner = self.ctx.author
        self.players = [self.game_owner]


    async def get_players(self):
        embed = discord.Embed(title=str(self.title),
                              colour=discord.Colour.random())
        embed.set_author(name=self.game_owner.display_name,
                              icon_url=self.game_owner.avatar_url)
        # Picture of dice
        embed.set_thumbnail(url='https://i.imgur.com/uCMhejd.png')
        self.game_msg = await self.ctx.send(embeds=[embed])

        # Gather players
        self.players = [ GenericDicePlayer(player) for player in
                         await gather_players(
                             self.bot,
                             game_msg = self.game_msg,
                             game_owner = self.game_owner,
                             existing_players = self.players,
                             max_players = int(self.max_players),
                             timeout = int(self.timeout)) ]

    async def play_game(self):
        try:
            await self.get_players()
            embed = self.game_msg.embeds[0]
            game_msg = self.game_msg
            # Roll init_dice
            if self.init_dice:
                self.roll_init_dice()
                await game_msg.edit(embeds=[embed])
                #
            #
            embed.add_field(name='Target',
                            value=str(self.score_limit),
                            inline=False)

            roll_btn = create_button(
                style=ButtonStyle.green,
                label='ROLL',
                emoji=self.dice_emoji,
                custom_id=f'roll_{game_msg.id}',
            )
            stand_btn = create_button(
                style=ButtonStyle.red,
                label='STAND',
                emoji=misc_emojis['stop_sign'],
                custom_id=f'stand_{game_msg.id}',
            )
            how_btn = create_button(
                style=ButtonStyle.gray,
                label='HOW TO PLAY',
                emoji=misc_emojis['question'],
                custom_id=f'how_{game_msg.id}',
            )

            actionrow = create_actionrow(roll_btn, stand_btn, how_btn)

            how_clicked = False
            def player_in_game(ctx: ComponentContext):
                return ctx.author_id in [ player.id for player in self.players ]

            try:
                for pos in range(len(self.players)):
                    if pos>0:
                        # Take a quick breather between players
                        roll_btn['disabled'] = True
                        stand_btn['disabled'] = True
                        how_btn['disabled'] = True
                        actionrow = create_actionrow(roll_btn,
                                                     stand_btn,
                                                     how_btn)
                        await game_msg.edit(components=[actionrow])
                        time.sleep(2)

                        roll_btn['disabled'] = False
                        stand_btn['disabled'] = False
                        if not how_clicked:
                            how_btn['disabled'] = False
                        #
                        actionrow = create_actionrow(roll_btn,
                                                     stand_btn,
                                                     how_btn)
                        await game_msg.edit(components=[actionrow])
                    #
                    p = self.players[pos]
                    result_str = ' : '.join([f'{self.init_dice_emoji}{roll}'
                                                 for roll in p.rolls])
                    field = embed.fields[pos]
                    embed.set_footer(text=f"{p.display_name}, you're up!")
                    await game_msg.edit(embeds=[embed],
                                        components=[actionrow])

                    while 1:
                        # Users must be in the game to plress a button
                        btn_ctx: ComponentContext = \
                            await wait_for_component(self.bot,
                                                     messages=[game_msg],
                                                     components=[actionrow],
                                                     check=player_in_game,
                                                     timeout=int(self.timeout))
                        if how_btn['custom_id'] == btn_ctx.custom_id:
                            # HOW TO PLAY pressed
                            q = misc_emojis['question']
                            embed.add_field(name=f'{q} ***How To Play*** {q}',
                                            value=str(self.how_to_play),
                                            inline=False)
                            how_clicked = True
                            how_btn['disabled'] = True
                            actionrow = create_actionrow(roll_btn,
                                                         stand_btn,
                                                         how_btn)
                            await btn_ctx.edit_origin(embeds=[embed],
                                                      components=[actionrow])
                        elif roll_btn['custom_id'] == btn_ctx.custom_id and \
                             btn_ctx.author_id == p.id:
                            # ROLL pressed
                            roll = p.roll(int(self.dice_sides))
                            embed.set_footer(text=f'{p.display_name} rolled {roll}')
                            
                            result_str = f'{result_str} : {self.dice_emoji}{roll}'
                            score = int(p.score)
                            if p.score > self.score_limit:
                                score = f'{score} BUST!'
                            elif p.score == self.score_limit:
                                score = f'{score}!!'
                            #
                            field.value = f'{result_str}\n**Score: {score}**\n'
                            embed.set_field_at(pos,
                                               name=field.name,
                                               value=field.value,
                                               inline=field.inline)
                            await btn_ctx.edit_origin(embeds=[embed])
                            if p.score >= self.score_limit:
                                if self.variant_rules and \
                                   p.score == self.score_limit:
                                    all_scores = sorted(p.score for p in self.players)
                                    while self.score_limit in all_scores:
                                        self.score_limit += 1
                                    #
                                    if how_clicked:
                                        field_pos = -2
                                    else:
                                        field_pos = -1
                                    embed.set_field_at(field_pos,
                                                       name='Target',
                                                       value=str(self.score_limit),
                                                       inline=False)
                                break
                        elif stand_btn['custom_id'] == btn_ctx.custom_id and \
                             btn_ctx.author_id == p.id:
                            # STAND pressed
                            embed.set_footer(text=f'{p.display_name} stands on {p.score}')
                            await btn_ctx.edit_origin(embeds=[embed])
                            break
                            #
                        #
                    #
                #
                not_bust = [p for p in self.players if p.score <= self.score_limit]
                if not_bust:
                    max_score = max([p.score for p in not_bust])
                    winners=[p.display_name for p in self.players 
                             if p.score == max_score]
                    if len(winners) > 1:
                        win = f'{" and ".join(winners)} tied on {max_score}!'
                    elif len(winners) == 1:
                        win = f'{winners[0]} wins!'
                    #
                else:
                    win = 'No winners!!'
                #
                embed.set_footer(text=win)
                await game_msg.edit(embeds=[embed], components=[])
            finally:
                try:
                    # Remove the buttons
                    await game_msg.edit(components=[])
                except Exception:
                    pass
            if random.randint(1,100) == 1:
                await self.ctx.channel.send(random.choice(self.bot.melodrama))
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

    def roll_init_dice(self):
        """Roll initial dice for each player"""
        embed = self.game_msg.embeds[0]
        for pos in range(len(self.players)):
            player = self.players[pos]
            for _ in range(int(self.init_dice)):
                player.roll(int(self.init_dice_sides))
            #
            field = embed.fields[pos]
            result_str = ' : '.join([f'{self.init_dice_emoji}{roll}'
                                        for roll in player.rolls])
            field.value = f'{result_str}\n**Score: {player.score}**\n'
            embed.set_field_at(pos,
                               name=field.name,
                               value=field.value,
                               inline=field.inline)
        #


class GenericDicePlayer(PlayerBase):
    def __init__(self, member: discord.Member):
        super().__init__(member)
        self.score = 0
        self.rolls = []

    def roll(self, sides):
        roll = int(random.randint(1,sides))
        self.rolls.append(int(roll))
        self.score += roll
        return roll

def setup(bot):
    bot.add_cog(GenericDiceGameCog(bot))
