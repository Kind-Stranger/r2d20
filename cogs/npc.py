import random
import os.path
import sys

from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_components import create_actionrow
from discord_slash.utils.manage_components import wait_for_component
from discord_slash.utils.manage_components import ComponentContext
from discord_slash.utils.manage_components import create_button
from discord_slash.model import ButtonStyle
from discord_slash.model import SlashCommandOptionType
# The below will `import discord` and override some of its stuff
from discord_slash.dpy_overrides import *

from env import test_id, home_id

ROOT_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCE_DIR=os.path.join(ROOT_DIR, 'resources')

class NPCCog(commands.Cog):
    """NPC Generation Tools"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name='npc',
        description="A quick NPC flavour generator",
        guild_ids=[test_id, home_id],
    )
    async def random_npc(self, ctx: SlashContext):
        npc = NPC.generate_random_npc()
        msg = (f"{npc.sex.title()} {npc.age} year old {npc.adjective}"
               f" {npc.race} who {npc.quirk}.")
        sys.stdout.write(f"NPC:{ctx.author.display_name}:{msg}\n")
        sys.stdout.flush()
        await ctx.reply(msg, hidden=True)

    @cog_ext.cog_slash(
        name='adj',
        description="Add an adjective for the NPC generator",
        options=[{"name": "adjective",
                  "description": "An adjective to describe this NPC",
                  "type": SlashCommandOptionType.STRING,
                  "required": True}],
        guild_ids=[test_id, home_id],
    )
    async def add_adjective(self, ctx: SlashContext, adj: str = None):
        sys.stdout.write(f"ADJ:{ctx.author.display_name}:{adj}\n")
        sys.stdout.flush()
        if not adj or not str(adj).strip():
            response = "`adj` parameter missing."
        else:
            with open(os.path.join(RESOURCE_DIR,'adjectives.txt'), 'a') as f:
                f.write(str(adj).strip()+'\n')
            #
            response = 'I added the adjective for you.'
            if random.randint(1,10) == 1:
                response = response+'\n'+random.choice(bot.melodrama)
            #
        #
        await ctx.reply(response, hidden=True)

    @cog_ext.cog_slash(
        name='quirk',
        description="Add a quirk for the NPC generator",
        options=[{"name": "quirk",
                  "description": "Interesting NPC quirk",
                  "type": SlashCommandOptionType.STRING,
                  "required": True}],
        guild_ids=[test_id, home_id],
    )
    async def add_quirk(self, ctx: SlashContext, quirk: str = None):
        sys.stdout.write(f"QUIRK:{ctx.author.display_name}:{quirk}\n")
        sys.stdout.flush()
        if not quirk or not str(quirk).strip():
            response = "`quirk` parameter missing."
        else:
            with open(os.path.join(RESOURCE_DIR,'extra_flavour.txt'), 'a') as f:
                f.write(adj+'\n')
            #
            response = 'I added the quirk for you.'
            if random.randint(1,10) == 1:
                response = response+'\n'+random.choice(bot.melodrama)
            #
        #
        await ctx.reply(response)

    @cog_ext.cog_slash(
        name='memoryadd',
        description="Create a memory to recall",
        options=[{"name": "memory",
                  "description": "Remember that time when...",
                  "type": SlashCommandOptionType.STRING,
                  "required": True}],
        guild_ids=[test_id, home_id],
    )
    async def add_memory(self, ctx: SlashContext, memory: str = None):
        sys.stdout.write(f"MEM:{ctx.author.display_name}:{memory}\n")
        sys.stdout.flush()
        if not memory or not str(memory).strip():
            response = "`memory` parameter missing."
        else:
            with open(os.path.join(RESOURCE_DIR,'memories.txt'), 'a') as f:
                f.write(str(memory).strip()+'\n')
            #
            response = 'I added the memory for you.'
            if random.randint(1,10) == 1:
                response = response+'\n'+random.choice(bot.melodrama)
            #
        #
        await ctx.reply(response, hidden=True)

    @cog_ext.cog_slash(
        name='memoryrecall',
        description="Remember that time when...",
        guild_ids=[test_id, home_id],
    )
    async def recall_memory(self, ctx: SlashContext):
        with open(os.path.join(RESOURCE_DIR,'memories.txt'), 'r') as f:
            memories = [line.strip() for line in f]
        #
        response = f'Remember that time when... {random.choice(memories)}'
        await ctx.reply(response, hidden=True)
###

class NPC:
    race_age_table = {
        'Dragonborn':{
            'child':(1,15),'young':(16,20),'adult':(21,50),'elderly':(51,80)},
        'Dwarf':{
            'child':(6,18),'young':(19,50),'adult':(50,199),'elderly':(200,350)},
        'Elf':{
            'child':(6,99),'young':(100,450),'adult':(451,650),'elderly':(651,750)},
        'Gnome':{
            'child':(6,20),'young':(20,40),'adult':(41,200),'elderly':(201,400)},
        'Half-Elf':{
            'child':(6,20),'young':(21,50),'adult':(51, 150),'elderly':(151,180)},
        'Halfling':{
            'child':(6,20),'young':(21,40),'adult':(41,150),'elderly':(151,250)},
        'Half-Orc':{
            'child':(1,14),'young':(15,45),'adult':(46,60),'elderly':(61,75)},
        'Human':{
            'child':(6,18),'young':(19,30),'adult':(31,65),'elderly':(65, 90)},
        'Tiefling':{
            'child':(6,18),'young':(19,40),'adult':(41,70),'elderly':(71,100)},
    }
    valid_age_ranges = race_age_table['Human'].keys()
    race_subrace_table = {
        'Dwarf':   ['Mountain', 'Hill', 'Duergar'],
        'Elf':     ['Drow', 'Eladrin', 'High', 'Wood', 'Tajuru', 'Joraga', 'Mul Daya'],
        'Gnome':   ['Deep', 'Forest', 'Rock'],
        'Halfling':['Lightfoot', 'Stout', 'Ghostwise'],
        'Half-Elf':['Half-Wood', 'Half-Moon/Sun', 'Half-Drow'],
        'Human':   [''],
        'Tiefling':['Variant', 'Feral', 'Abyssal'],
    }
    with open(os.path.join(RESOURCE_DIR, 'accents.txt')) as f:
        accents = [line.strip() for line in f]
    #
    with open(os.path.join(RESOURCE_DIR, 'adjectives.txt')) as f:
        adjectives = [line.strip() for line in f]
    #
    with open(os.path.join(RESOURCE_DIR, 'extra_flavour.txt')) as f:
        quirks = [line.strip() for line in f]

    def __init__(self, *,
                 race: str = None,
                 subrace: str = None,
                 main_class: str = None,
                 sub_class: str = None,
                 age_group: str = None,
                 age: int = 0,
                 accent: str = None,
                 adjective: str = None,
                 quirk: str = None,
                 sex: str = None,
    ):
        self.race = str(race) if race else None
        self.main_class = str(main_class) if main_class else None
        self.sub_class = str(sub_class) if sub_class else None
        self.age_group = str(age_group) if age_group else None
        self.age = int(age) if age else 0
        self.accent = str(accent) if accent else None
        self.adjective = str(adjective) if adjective else None
        self.quirk = str(quirk) if quirk else None
        self.sex = str(sex) if sex else None

    @classmethod
    def generate_random_npc(cls,
                            race: str = None,
                            subrace: str = None,
                            age_group: str = None):
        if not race:
            race = random.choice(list(cls.race_subrace_table))
        if not subrace and race in cls.race_subrace_table:
            subrace = random.choice(list(cls.race_subrace_table[race]))
        if not age_group or age_group not in cls.valid_age_groups:
            age_group = random.choice(['young','adult','elderly'])
            
        return cls(
            race=race,
            subrace=subrace,
            age_group=age_group,
            age=random.randint(*cls.race_age_table[race][age_group]),
            adjective=random.choice(cls.adjectives),
            quirk=random.choice(cls.quirks),
            accent=random.choice(cls.accents),
            sex=random.choice(['male','female']),
        )

def setup(bot):
    bot.add_cog(NPCCog(bot))
