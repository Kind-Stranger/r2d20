import random
import os

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'resources')

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
    race_subrace_table = {
        'Dwarf':   ['Mountain', 'Hill', 'Duergar'],
        'Elf':     ['Drow', 'Eladrin', 'High', 'Wood', 'Tajuru', 'Joraga', 'Mul Daya'],
        'Gnome':   ['Deep', 'Forest', 'Rock'],
        'Halfling':['Lightfoot', 'Stout', 'Ghostwise'],
        'Half-Elf':['Half-Wood', 'Half-Moon/Sun', 'Half-Drow', 'Half-Aquatic'],
        'Human':   [''],
        'Tiefling':['Variant', 'Feral', 'Abyssal'],
    }
    #
    with open(os.path.join(RESOURCE_DIR, 'accents.txt')) as f:
        accents = [line.strip() for line in f]
    #
    with open(os.path.join(RESOURCE_DIR, 'adjectives.txt')) as f:
        adjectives = [line.strip() for line in f]
    #
    with open(os.path.join(RESOURCE_DIR, 'extra_flavour.txt')) as f:
        extra_flavours = [line.strip() for line in f]
    #
    def __init__(self):
        self.race = None
        self.subrace = None
        self.age_range = None
        self.age = 0
        self.accent = None
        self.adjective = None
        self.quirk = None
        self.sex = None


# def generate_random_npc():
#     'Generate a random NPC'
#     npc = NPC()
#     npc.race = random.choice(list(npc.race_subrace_table))
#     npc.subrace = random.choice(npc.race_subrace_table[npc.race])
#     npc.age_range = random.choice(list(npc.race_age_table[npc.race]))
#     npc.age = random.randint(*npc.race_age_table[npc.race][npc.age_range])
#     npc.adjective = random.choice(npc.adjectives)
#     npc.quirk = random.choice(npc.extra_flavours)
#     npc.accent = random.choice(npc.accents)
#     npc.sex = random.choice(['Male', 'Female'])
#     return npc

