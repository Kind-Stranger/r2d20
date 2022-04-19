# Works with Python 3.8
#
import math
import re
import sys
import traceback

from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
# The below will `import discord` and override some of it's stuff
from discord_slash.dpy_overrides import *
from discord_slash.model import SlashCommandOptionType

from env import *
from utils.roll_utils import *
from utils.pranks import *

intents = discord.Intents().default()
intents.members = True
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





def check_aliases(cmd_args):
    """Check for /roll command without "roll " (e.g. /d20...)
    """
    rollAliasRe = r'^/(\d*d\d+.*)$'
    cmd = cmd_args.pop(0).lower()
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
       message.author.id not in MY_USER_IDS:
        await scramble_nickname(message.author)
    #
    if cmd in ['/hyp', '/hypot', '/tri', '/triangle']:
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
    #
    elif message.author.id in MY_USER_IDS:
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


@bot.event
async def on_ready():
    "Happens when bot logs in"
    global bot
    home_guild = bot.get_guild(HOME_ID)
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
            'cogs.generic_dice_games',
            'cogs.npc',
            'cogs.rolls'
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

@slash.slash(name='cogload',
             description='Re/Load a cog',
             options=[{'name':'name',
                       'description': 'Name of the cog',
                       'type': SlashCommandOptionType.STRING,
                       "required": True},
                      {'name':'debug',
                       'description': 'Debugging flag',
                       'type': SlashCommandOptionType.BOOLEAN,
                       "required": False}],
             guild_ids=[TEST_ID])
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
