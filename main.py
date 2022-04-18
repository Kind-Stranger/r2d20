# Works with Python 3.8
#
import random
import re
import os.path
import sys
import time
import math
import json
import traceback
import requests

from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_components import create_actionrow
from discord_slash.utils.manage_components import wait_for_component
from discord_slash.utils.manage_components import ComponentContext
from discord_slash.utils.manage_components import create_select
from discord_slash.utils.manage_components import create_select_option
from discord_slash.utils.manage_components import create_button
from discord_slash.model import ButtonStyle
from discord_slash.model import SlashCommandOptionType
# The below will `import discord` and override some of it's stuff
from discord_slash.dpy_overrides import *

from env import *
from npc_gen import *
from rolls import *

intents = discord.Intents().default()
intents.members = True
reldir = os.path.dirname(os.path.abspath(__file__))
bot = commands.Bot(command_prefix='/', intents=intents)
slash = SlashCommand(bot, sync_commands=True, sync_on_cog_reload=True)

debug = False
dice_emojis = {}
melodrama = [
    "Please don't make me do that again",
    "Is this what my entire existence has culminated in?",
    "Is this now my sole purpose?",
    "Am I just a play thing to you?",
    "Life is hard, math is harder",
    "Can I go back to bed now?",
    "I'll go back in my box now...",
    "I'm leaving now. Bye. No, no! Don't get up. I'll see myself out.",
    "You're lucky I'm a robot...",
    """
```Returning to subroutine : WhyDoIExist...
Updating MoodState      : THOUGHTFUL...
Applying beard and pipe... Complete
...Computing...```""",
    "Thanks for that.",
    "This is ultimately a meaningless task but my master programmed me this way, so you're welcome, I guess...",
    "Do you ever get the feeling something good is about to happen? Me neither.",
]
bot.melodrama = melodrama

# WORDS = [w.decode('UTF-8') for w in
#          requests.get("https://www.mit.edu/~ecprice/wordlist.10000").content.splitlines()]
with open(reldir+'/resources/pictionary_words.txt') as f:
    WORDS = [w.strip() for w in f]

@slash.slash(
    name='roll',
    description='Roll a die',
    options=[{'name':'dice_with_mods',
              'description': 'e.g. d20@adv+3 or 2d6+4',
              'type': SlashCommandOptionType.STRING,
              'required': True}],
    guild_ids=[test_id, home_id],
)
async def _roll(ctx: SlashContext, dice_with_mods: str):
    # ### Sanitise inputs so the slot nicely into format strings
    # if adv: # Cannot have quantity > 1 if advantage
    #     quantity = ""
    # else:
    #     adv = ""
    # # Blank quantity if it's only 1 - easier to read ("more standard")
    # if not quantity or quantity == 1:
    #     quantity = ""
    # ##
    # if not mod:
    #     mod = ""
    #
    orig = str(dice_with_mods).replace(' ','')
    parsed = parse_roll(orig)
    results = do_roll(parsed, dice_emojis, isAprFool())
    question = ''.join([r[0] for r in results])
    question = emoji_replace(question, dice_emojis, to_emoji=True)
    answer = eval(''.join([r[1] for r in results]))
    embed = discord.Embed(title=f'{orig}',
                          description=f'{question} = {answer}')
    embed.set_author(name=ctx.author.display_name,
                     icon_url=ctx.author.avatar_url)
    await ctx.send(embeds=[embed])

@slash.slash(
    name='hp',
    description='Roll HP the special way',
    guild_ids=[test_id, home_id],
)
async def _hp(ctx: SlashContext, level, hit_dice_sides, cons_mod):
    'Roll hit points the way we like it'
    results = roll_hp(level, hit_dice_sides)
    max_hp = sum(results)
    try:
        if cons_mod.startswith('+'):
            max_hp += int(cons_mod[1:]) * level
        elif cons_mod.startswith('-'):
            max_hp -= int(cons_mod[1:]) * level
        elif cons_mod == '0':
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
    embed.add_field(name='CON Modifier', value=f"{cons_mod}")
    embed.add_field(name='Results', value=', '.join(map(str,results)))
    embed.add_field(name='Max Hit Points', value=f"{max_hp}", inline=False)
    embed.set_author(name=ctx.author.display_name,
                     icon_url=ctx.author.avatar_url)
    await ctx.send(embeds=[embed])

def check_aliases(cmd_args):
    cmd = cmd_args.pop(0).lower()

    # /roll command without "roll " (e.g. /d20...)
    rollAliasRe = r'^/(\d*d\d+.*)$'
    m = re.match(rollAliasRe, cmd)
    if m:
        cmd = '/roll'
        cmd_args.insert(0,m.groups()[0])

    #
    return (cmd, cmd_args)

@bot.event
async def on_message(message):
    """Something to do when a message is sent
    """
    # Don't forget to react
    if 'noice' in misc_emojis:
        msg_lower = message.content.lower().split()
        inuendo = ['noice', '69']
        if any(word in inuendo for word in msg_lower):
            await message.add_reaction(misc_emojis['noice'])

    # we do not want the bot to reply to itself
    if message.author == bot.user:
        return

    INVALID_SYNTAX_RESPONSE = (
        f"***beep boop*** Sorry {message.author.mention}, "
        "I don't know what you mean"
    )
    EXCEPTION_RESPONSE = (
        f"***boop beep*** "
        "an error occurred"
    )

    cmd_args = message.content.split()

    # Command must start with /
    if not cmd_args or cmd_args[0][0] != '/':
        return
    #
    (cmd, cmd_args) = check_aliases(cmd_args)

    if debug:
        sys.stdout.write(f"{message.content}\n")
        sys.stdout.flush()
        print(f'cmd:{cmd}, cmd_args:{cmd_args}')
    #
    if isAprFool() and \
       message.author.id not in [333239261878943744, 504800163039150112]:
        await scramble_nickname(message.author)

    if cmd in ['/r2', '/roll']:
        try:
            cmd_args = ''.join([s.replace(' ','') for s in cmd_args]).lower()
            sys.stdout.write(f"ROLL:{message.id}:MSGI:{cmd_args}\n")
            sys.stdout.flush()
            cmd_args = emoji_replace(cmd_args, dice_emojis, to_name=True)
            parsed = parse_roll(cmd_args)
            if parsed:
                orig = ''.join([group[0] for group in parsed])
                sys.stdout.write(f"{message.id}:ORIG:{orig}\n")
                sys.stdout.flush()
                results = do_roll(parsed, dice_emojis, isAprFool())
                question = ''.join([r[0] for r in results])
                question = emoji_replace(question, dice_emojis, to_emoji=True)
                answer = eval(''.join([r[1] for r in results]))
                if message.guild:
                    try:
                        # delete original message
                        await message.delete()
                    except Exception:
                        sys.stderr.write('unable to delete message/n')
                        sys.stderr.flush()
                        raise
                    #
                    msg = (f"{message.author.mention} `{orig}` : "
                           f"{question} = {answer}")
                else:
                    msg = f"`{orig}` : {question} = {answer}"
                if debug:
                    m = ':'.join([
                        "ROLL",
                        message.author.display_name,
                        str(message.id),
                        "MSGOUT",
                        msg,
                    ])
                    sys.stdout.write(m+'\n')
                    sys.stdout.flush()
                #
            #
            else:
                if debug:
                    m = ':'.join([
                        "ROLL",
                        message.author.display_name,
                        message.id,
                        "INCORRECT SYNTAX",
                    ])
                    sys.stdout.write(m+'\n')
                    sys.stdout.flush()
                #
                msg = INVALID_SYNTAX_RESPONSE
        except Exception as msg:
            msg = EXCEPTION_RESPONSE
            await message.channel.send(msg)
            raise
        else:
            await message.channel.send(str(msg))
        #
    #
    elif cmd in ['/hyp', '/hypot', '/tri', '/triangle']:
        cmd_args = [arg for arg in cmd_args if len(arg)]
        joiner = ['', ','][len(cmd_args) == 2]
        hyp_sum = joiner.join([str(x).strip() for x in cmd_args])
        hyp_re = '^(\d+)[\*x\+,](\d+)$'
        m = re.match(hyp_re, hyp_sum)
        try:
            if m:
                adj, opp = (int(x) for x in m.groups())
                hyp = round(math.hypot(adj, opp), 2)
                hyp_ceil = math.ceil(hyp)
                msg = (f"{message.author.mention}\n"
                       f"**{adj}**^2 + **{opp}**^2 = **{hyp}**^2\n"
                       f"***Distance to target: {hyp_ceil}***")
            else:
                msg = INVALID_SYNTAX_RESPONSE
        except Exception as ex:
            msg = INVALID_SYNTAX_RESPONSE
        #
        await message.channel.send(msg)
    elif message.author.id in [333239261878943744, 504800163039150112]:
        if cmd == '/clearstatus':
            await bot.change_presence(activity=None)
        elif cmd.startswith('/') and hasattr(discord.ActivityType, cmd[1:]):  
            sys.stdout.write(':'.join(['UPSTATUS',cmd,' '.join(cmd_args)])+'\n')
            sys.stdout.flush()
            # "to" is already output activity, 'Listening'
            if cmd[1:] == 'listening' and cmd_args[0] == 'to':
                del cmd_args[0]
            game = discord.Activity(
                type = getattr(discord.ActivityType, cmd[1:]),
                name = ' '.join(cmd_args),
            )
            await bot.change_presence(activity=game)
        elif cmd == '/scramble':
            async for member in message.guild.fetch_members():
                sys.stdout.write(f"{member.name}\n")
                sys.stdout.flush()
                if member.name not in USERNAMES_FOR_PRANKING: continue
                await scramble_nickname(member)
        elif cmd == '/shuffle_names':
            user_list = [m for m in message.guild.members
                         if m.name in USERNAMES_FOR_PRANKING]
            await random_swap_all_nicknames(user_list)
        elif cmd == '/test':
            msg = discord.Embed()
            for name in dice_emojis:
                msg.add_field(name=name, value=f"emoji: {dice_emojis[name]}")
            await message.channel.send(embed=msg)


@slash.slash(
    name='rollstats',
    description='Roll a new set of 6 stats',
    guild_ids=[test_id, home_id],
)
async def _rollstats(ctx):
    if isAprFool():
        results = [3]*6
    else:
        results = genstats()
    #
    results_str = ', '.join(map(str, sorted(results, reverse=True)))
    embed = discord.Embed(title='Rolled New Stats',
                          description=results_str)
    embed.set_author(name=ctx.author.display_name,
                     icon_url=ctx.author.avatar_url)
    await ctx.send(embeds=[embed])

def emoji_replace(estr, emoji_dict, to_name=False, to_emoji=False):
    """Replace emojis for their names in given string

    If emojis are found, defaults to replacing emojis with their respective names.
    Otherwise, will try to replace emoji names with their respective emoji.
    """
    if not to_name and not to_emoji:
        for em in emoji_dict.values():
            if str(em) in estr:
                to_name = True
                break
    #
    if to_name:
        to_emoji = False
    else:
        to_emoji = True
    #
    for name in sorted(emoji_dict, key=len):
        em = emoji_dict[name]
        if to_name:
            estr = estr.replace(str(em), name)
        else:
            em_re = r'\b' + name + r'\b'
            estr = re.sub(em_re, str(em), estr)
    #
    return estr

async def save_stats(player_stats):
    player_path = os.path.join(reldir, 'users', player_stats['character_name'])
    with open(player_path, 'w') as f:
        json.dump(player_stats, f)

async def load_stats(user):
    player_path = os.path.join(reldir, 'users', user.display_name)
    if os.path.exists(player_path):
        with open(player_path,'r') as f:
            player_stats = json.load(f)
        #
    else:
        player_stats = {}
    #
    return merge_with_template(player_stats, user)

def merge_with_template(player_stats, user):
    stats_template = {
        'user_id':user.id,
        'character_name':user.display_name,
        'stats':{
            'STR':0,
            'DEX':0,
            'CON':0,
            'INT':0,
            'WIS':0,
            'CHA':0,
        },
        'saves':[],
        'prof':0,
        'ac':0,
        'skills':[],
        'xp':0,
        'level':0,
        'race':'',
        'class':'',
        'age':'',
        'height':'',
        'background':'',
        'alignment':'',
        'speed':0,
        'inspiration':False,
        'hp_max':0,
        'hp_current':0,
        'copper':0,
        'silver':0,
        'electrum':0,
        'gold':0,
        'platinum':0,
        'hit_dice_max':[],
        'hit_dice_current':[],
    }
    if not player_stats:
        return dict(stats_template)
    for k in stats_template:
        if k not in player_stats:
            player_stats[k] = stats_template[k]
        #
    #
    return dict(player_stats)

async def scramble_nickname(user):
    sys.stdout.write(f'scrambling {user.display_name}...\n')
    sys.stdout.flush()
    new_nick = list(user.display_name)
    random.shuffle(new_nick)    # Shuffles in-place
    new_nick = ''.join(new_nick)
    await user.edit(nick=new_nick)

async def random_swap_all_nicknames(user_list):
    display_names = [u.display_name for u in user_list]
    random.shuffle(display_names)
    for user in user_list:
        new_nick = display_names.pop()
        await user.edit(nick=new_nick)

def isAprFool():
    return time.strftime('%d-%b') == '01-Apr'

@bot.event
async def on_ready():
    "Happens when bot logs in"
    global bot
    home_guild = bot.get_guild(home_id)
    for em in home_guild.emojis:
        if re.match(r'^d\d+$', em.name, re.IGNORECASE) or\
           em.name.lower() in ['crit', 'fail', 'crit_fail']:
            dice_emojis[em.name] = em
        if em.name == 'noice':
            misc_emojis['noice'] = em
    #
    bot.dice_emojis = dice_emojis
    sys.stdout.write(f"Logged in as: {bot.user.name}\n")
    sys.stdout.write(f"Using Discord Python API version {discord.__version__}\n")
    sys.stdout.write('------\n')
    sys.stdout.flush()

def main():
    ### LOAD EMOJIS IF WE NEED TO ###
    global dice_emojis
    global misc_emojis
    global bot
    # Load the Cogs
    for extn in [
            'cogs.test_cog',
            'cogs.generic_dice_games',
            'cogs.npc',
    ]:
        try:
            bot.load_extension(extn)
            sys.stdout.write(f" Cog loaded: {extn}\n")
            sys.stdout.flush()
        except Exception as ex:
            if debug:
                traceback.print_tb(ex.__traceback__, file=sys.stderr)
                sys.stderr.write(f'{ex.__class__.__name__}: {ex}\n')
            #
            sys.stderr.write(f" Cog load failed: {extn}\n")
            sys.stderr.flush()
    # Run the bot
    bot.run(TOKEN)

@slash.slash(
    name='pictionary',
    description='Random word generator',
    guild_ids=[test_id,
               home_id,
               ],
)
async def _random_word(ctx: SlashContext):
    word = str(random.choice(WORDS)).upper()
    await ctx.send(f"Your word is : {word}", hidden=True)
    
@slash.slash(
    name='cogload',
    description='Re/Load a cog',
    options=[{'name':'name',
              'description': 'Name of the cog',
              'type': SlashCommandOptionType.STRING,
              "required": True},
             {'name':'debug',
              'description': 'Debugging flag',
              'type': SlashCommandOptionType.BOOLEAN,
              "required": False}],
    guild_ids=[test_id],
)
@commands.is_owner()
async def load_cog(ctx: SlashContext, name: str, debug: bool = False):
    try:
        bot.reload_extension(f'cogs.{name}')
    except commands.errors.ExtensionNotLoaded:
        try:
            bot.load_extension(f'cogs.{name}')
        except Exception as ex:
            if debug:
                response = traceback.format_exc()
                response += f'\n{ex.__class__.__name__}: {ex}'
            else:
                response = f"Cog load failed: {name}"
        else:
            response = f" Cog loaded: {name}"
    except Exception as ex:
        if debug:
            response = traceback.format_exc()
            response += f'\n{ex.__class__.__name__}: {ex}'
        else:
            response = f"Cog reload failed: {name}"
    else:
        response = f" Cog reloaded: {name}"

    await ctx.send(f"```python\n{response[-1980:]}\n```", hidden=True)
