from typing import List

# The below will `import discord` and override some of it's stuff
from discord_slash.dpy_overrides import *
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import (ComponentContext,
                                                   create_actionrow,
                                                   create_button,
                                                   wait_for_component)

from env import misc_emojis


class PlayerBase:
    """Base class which allows direct access to discord.Member attributes.
    Useful for keeping track of scores and such.
    """
    def __init__(self, member: discord.Member):
        self._member = member

    @property
    def member(self):
        return self._member

    def __getattr__(self, name):
        """Gives direct access to discord.Member attributes"""
        if hasattr(self.member, name):
            return getattr(self.member, name)
        else:
            raise AttributeError(f"'{self.__class__.__name__} has no attribute '{name}'")

def add_player_to_game_embed(embed, player, player_num):
    embed.add_field(name=f'**P{player_num}** {player.display_name}',
                    value='-',
                    inline=False)

async def gather_players(bot,
                         *,
                         game = None,
                         existing_players: List[discord.Member] = None,
                         max_players: int = None,
                         timeout: int = None):
    """Expects a message to already exist.
    Creates a 'JOIN' and 'START' button.  'JOIN' adds members to list until
    either max players is reached or the game owner taps 'START'.

    :raises: asyncio.TimeoutError
    """
    if not existing_players:
        existing_players = []
    #
    players = list(existing_players)
    
    for i in range(len(players)):
        add_player_to_game_embed(game.embed, players[i], i+1)
    #
    join_button = create_button(style=ButtonStyle.blue,
                                custom_id=f'join_{game.game_msg.id}',
                                label=f'{misc_emojis["plus"]} JOIN')
    start_button = create_button(style=ButtonStyle.green,
                                 custom_id=f'start_{game.game_msg.id}',
                                 label=f'{misc_emojis["play"]} START')
    action_row = create_actionrow(join_button, start_button)
    await game.game_msg.edit(embed=game.embed, components=[action_row])

    def check_join_if_not_in_game(ctx: ComponentContext):
        """Join button can only be pressed by those not already in game"""
        return join_button['custom_id'] == ctx.custom_id and \
            ctx.author not in players

    def check_start_if_game_owner(ctx: ComponentContext):
        """Start button can only be pressed by game owner"""
        return start_button['custom_id'] == ctx.custom_id and \
            ctx.author == game.game_owner

    def check_btn_press(ctx: ComponentContext):
        return check_join_if_not_in_game(ctx) or check_start_if_game_owner(ctx)

    try:
        while len(players) < max_players:
            btn_ctx: ComponentContext = \
                await wait_for_component(bot,
                                         components=action_row,
                                         check=check_btn_press,
                                         timeout=timeout)
            if join_button['custom_id'] == btn_ctx.custom_id:
                players.append(btn_ctx.author)
                add_player_to_game_embed(game.embed, players[-1], len(players))
                await btn_ctx.edit_origin(embed=game.embed)

            elif start_button['custom_id'] == btn_ctx.custom_id:
                break                      # Start the game
    finally:
        try:
            await btn_ctx.edit_origin(components=[])
        except:
            await game.game_msg.edit(components=[]) # Remove buttons
    #
    return players
