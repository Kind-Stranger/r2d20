import sys
import asyncio
import random
import time

from typing import Union

from discord_slash import SlashContext
from discord_slash.utils.manage_components import create_actionrow
from discord_slash.utils.manage_components import wait_for_component
from discord_slash.utils.manage_components import ComponentContext
from discord_slash.utils.manage_components import create_button
from discord_slash.model import ButtonStyle
# The below will `import discord` and override some of its stuff
from discord_slash.dpy_overrides import *

from env import misc_emojis
from utils.players import gather_players
from utils.players import PlayerBase


class GenericDiceGame:
    """Template for a generic dice game where the objective is to score as close
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
    def __init__(self,
                 bot,
                 ctx: SlashContext,
                 *,
                 title: Union[None, str] = None,
                 dice_sides: int = 0,
                 dice_emoji: Union[None, str, discord.Emoji] = None,
                 init_dice: int = 0,
                 init_dice_sides: int = 0,
                 init_dice_emoji: Union[None, str, discord.Emoji] = None,
                 score_limit: int = 0,
                 how_to_play: Union[None, str] = None,
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
        self.how_clicked = False


    async def get_players(self):
        self.embed = discord.Embed(title=str(self.title),
                              colour=discord.Colour.random())
        self.embed.set_author(name=self.game_owner.display_name,
                              icon_url=self.game_owner.avatar_url)
        # Picture of dice
        self.embed.set_thumbnail(url='https://i.imgur.com/uCMhejd.png')
        self.game_msg = await self.ctx.send(embed=self.embed)

        # Gather players
        self.players = [ GenericDicePlayer(member) for member in
                         await gather_players(self.bot,
                                              game = self,
                                              existing_players = self.players,
                                              max_players = int(self.max_players),
                                              timeout = int(self.timeout)) ]

    async def play_game(self):
        try:
            await self.setup_game()
            try:
                await self.game_msg.edit(components=[self.actionrow])
                for player_index in range(len(self.players)):
                    if player_index > 0:
                        await self.pause_for(secs=2)
                    #
                    await self.take_player_turn(player_index)
                #
                await self.output_game_result()
            finally:
                try:
                    # Remove the buttons
                    await self.game_msg.edit(components=[])
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

    async def setup_game(self):
        await self.get_players()
        self.roll_init_dice()
        self.embed.add_field(name='Target',
                             value=str(self.score_limit),
                             inline=False)
        await self.init_buttons()

    async def take_player_turn(self, player_index):
        player = self.players[player_index]
        field = self.embed.fields[player_index]
        result_str = ' : '.join([f'{self.init_dice_emoji}{roll}'
                                    for roll in player.rolls])
        self.embed.set_footer(text=f"{player.display_name}, you're up!")
        await self.game_msg.edit(embeds=[self.embed],
                                    components=[self.actionrow])

        while 1:
            # Users must be in the game to press a button
            btn_ctx: ComponentContext = \
                await wait_for_component(self.bot,
                                         messages=[self.game_msg],
                                         components=[self.actionrow],
                                         check=self.is_player_in_game,
                                         timeout=int(self.timeout))
            if self.how_btn['custom_id'] == btn_ctx.custom_id:
                # HOW TO PLAY pressed
                q = misc_emojis['question']
                self.embed.add_field(name=f'{q} ***How To Play*** {q}',
                                value=str(self.how_to_play),
                                inline=False)
                how_clicked = True
                self.how_btn['disabled'] = True
                await self.update_actionrow()
                await btn_ctx.edit_origin(embeds=[self.embed],
                                            components=[self.actionrow])
            elif self.roll_btn['custom_id'] == btn_ctx.custom_id and \
                    btn_ctx.author_id == player.id:
                # ROLL pressed
                roll = player.roll(int(self.dice_sides))
                self.embed.set_footer(text=f'{player.display_name} rolled {roll}')
                
                result_str = f'{result_str} : {self.dice_emoji}{roll}'
                score = int(player.score)
                if player.score > self.score_limit:
                    status = 'BUST!'
                elif player.score == self.score_limit:
                    status = '!!'
                else:
                    status = ''
                #
                field.value = f'{result_str}\n**Score: {player.score}{status}**\n'
                self.embed.set_field_at(player_index,
                                        name=field.name,
                                        value=field.value,
                                        inline=field.inline)
                await btn_ctx.edit_origin(embeds=[self.embed])
                if player.score >= self.score_limit:
                    if self.variant_rules and \
                        player.score == self.score_limit:
                        all_scores = sorted(player.score for player in self.players)
                        while self.score_limit in all_scores:
                            self.score_limit += 1
                        #
                        if how_clicked:
                            field_pos = -2
                        else:
                            field_pos = -1
                        self.embed.set_field_at(field_pos,
                                            name='Target',
                                            value=str(self.score_limit),
                                            inline=False)
                    break
            elif self.stand_btn['custom_id'] == btn_ctx.custom_id and \
                    btn_ctx.author_id == player.id:
                # STAND pressed
                self.embed.set_footer(text=f'{player.display_name} stands on {player.score}')
                await btn_ctx.edit_origin(embeds=[self.embed])
                break

    def is_player_in_game(self, ctx: ComponentContext):
        return ctx.author_id in [ player.id for player in self.players ]

    async def init_buttons(self):
        self.roll_btn = create_button(
            style=ButtonStyle.green,
            label='ROLL',
            emoji=self.dice_emoji,
            custom_id=f'roll_{self.game_msg.id}',
        )
        self.stand_btn = create_button(
            style=ButtonStyle.red,
            label='STAND',
            emoji=misc_emojis['stop_sign'],
            custom_id=f'stand_{self.game_msg.id}',
        )
        self.how_btn = create_button(
            style=ButtonStyle.gray,
            label='HOW TO PLAY',
            emoji=misc_emojis['question'],
            custom_id=f'how_{self.game_msg.id}',
        )
        self.buttons = [self.roll_btn, self.stand_btn, self.how_btn]
        await self.update_actionrow()

    async def update_actionrow(self):
        self.actionrow = create_actionrow(*self.buttons)

    def roll_init_dice(self):
        """Roll initial dice for all players"""
        if not self.init_dice:
            return
        for pos in range(len(self.players)):
            player = self.players[pos]
            for _ in range(int(self.init_dice)):
                player.roll(int(self.init_dice_sides))
            #
            field = self.embed.fields[pos]
            result_str = ' : '.join([f'{self.init_dice_emoji}{roll}'
                                     for roll in player.rolls])
            field.value = f'{result_str}\n**Score: {player.score}**\n'
            self.embed.set_field_at(pos,
                                    name=field.name,
                                    value=field.value,
                                    inline=field.inline)
                                    
    async def pause_for(self, secs: int):
        await self.disable_all_buttons()
        time.sleep(2)
        await self.enable_all_buttons()
        await self.game_msg.edit(components=[self.actionrow])

    async def disable_all_buttons(self):
        for button in self.buttons:
            button['disabled'] = True
        await self.update_actionrow()

    async def enable_all_buttons(self):
        for button in self.buttons:
            if button != self.how_btn or not self.how_clicked:
                button['disabled'] = False
        await self.update_actionrow()

    async def update_embed(self):
        await self.game_msg.edit(embeds=[self.embed])

    async def output_game_result(self):
        not_bust_players = [ player for player in self.players if player.score <= self.score_limit ]
        if not_bust_players:
            max_score = max([player.score for player in not_bust_players])
            winners=[ player.display_name for player in self.players 
                        if player.score == max_score ]
            if len(winners) > 1:
                win = f'{" and ".join(winners)} tied on {max_score}!'
            elif len(winners) == 1:
                win = f'{winners[0]} wins!'
            #
        else:
            win = 'No winners!!'
        #
        self.embed.set_footer(text=win)
        await self.game_msg.edit(embeds=[self.embed], components=[])


class GenericDicePlayer(PlayerBase):
    def __init__(self, member: discord.Member):
        super().__init__(member)
        self.score = 0
        self.rolls = []

    def roll(self, sides):
        roll = int(random.randint(1, sides))
        self.rolls.append(int(roll))
        self.score += roll
        return roll

