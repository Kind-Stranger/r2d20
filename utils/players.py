from typing import List

from discord_slash import SlashContext, cog_ext
# The below will `import discord` and override some of it's stuff
from discord_slash.dpy_overrides import *
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import (ComponentContext,
                                                   create_actionrow,
                                                   create_button,
                                                   wait_for_component)
from env import misc_emojis

class PlayerBase:
    def __init__(self, member: discord.Member):
        self._member = member

    @property
    def member(self):
        return self._member

    def __getattr__(self, name):
        'Gives direct access to Member attributes'
        if hasattr(self.member, name):
            return getattr(self.member, name)
        else:
            raise AttributeError(f"'{self.__class__.__name__} has no attribute '{name}'")

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
    game_msg = game.game_msg
    game_owner = game.game_owner
    embed = game.embed
    if existing_players:
        players = list(existing_players)
        player_ids = {p.id:0 for p in existing_players}
        # Add existing players to embed
        for i in range(len(players)):
            embed.add_field(name=f'**P{i+1}** {players[i].display_name}',
                            value='-',
                            inline=False)
        #
    else:
        players = []
    #
    join_button = create_button(style=ButtonStyle.blue,
                                custom_id=f'join_{game_msg.id}',
                                label=f'{misc_emojis["plus"]} JOIN')
    start_button = create_button(style=ButtonStyle.green,
                                 custom_id=f'start_{game_msg.id}',
                                 label=f'{misc_emojis["play"]} START')
    ar = create_actionrow(join_button, start_button)
    await game_msg.edit(embed=embed, components=[ar])

    def p_check(ctx: ComponentContext):
        # Only joinable by those not already joined
        # START only pressable by game_owner
        return (join_button['custom_id'] == ctx.custom_id and
                ctx.author not in players) or \
               (start_button['custom_id'] == ctx.custom_id and
                ctx.author == game_owner)

    try:
        while True:
            btn_ctx: ComponentContext = \
                await wait_for_component(bot, components=ar,
                                         check=p_check,
                                         timeout=timeout)
            player = btn_ctx.author # Convenient alias
            if join_button['custom_id'] == btn_ctx.custom_id:
                players.append(player)
                embed.add_field(
                    name=f'**P{len(players)}** {player.display_name}',
                    value='-',
                    inline=False,
                )
                await btn_ctx.edit_origin(embed=embed)

                # Max players reached - start the game!
                if len(players) == max_players:
                    break
                #

            elif start_button['custom_id'] == btn_ctx.custom_id:
                # START pressed by game owner - we can start the game
                await btn_ctx.edit_origin(components=[])
                break
    finally:
        # Clear up the buttons
        await game_msg.edit(components=[])
    #
    return players

