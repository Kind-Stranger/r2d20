import asyncio
import discord
import random
import re
import sys
import time
from env import *
from heapq import nlargest, nsmallest

def roll_hp(level, hit_dice_sides):
    if hit_dice_sides < 1:
        hit_dice_sides = 1
    min_roll = (int(hit_dice_sides) - 1) // 2 + 1
    if level > 1:
        num_dice = level - 1
        results = [random.randint(min_roll, hit_dice_sides) for _ in range(num_dice)]
        results.insert(0, hit_dice_sides)
        return results
    else:
        return [hit_dice_sides]

def genstats():
    'Roll 4d6k3 six times'
    results = []
    for _ in range(6):
        rolls = [random.randint(1,6) for n in range(4)]
        result = sum(sorted(rolls, reverse=True)[:3])
        results.append(result)
    return results

def parse_roll(die_str, results=None):
    """Parse standard dice notation
    """
    if not die_str:
        return results
    dice_re = r'^((\d+)?d(\d+)(m(\d+))?(?:(@(?:d(?:is)?)?(?:a(?:dv)?)?(?:antange)?)|([kd][hl]?)(\d+))?((?:[\+\*\-\/]\d+)+)?[\+\-\*/\^]?)'
    m = re.match(dice_re, die_str)
    if not m:  # No match
        return None
    if results:
        results.append(list(m.groups()))
        # hacky fix for multiple dice types
        p = re.search(r'\+(\d+)$', results[-2][0])
        if p:
            results[-2][0] = re.sub(r'\d+$', '', results[-2][0])
            if not results[-2][0]:
                results[-2][0] = None
            results[-2][8] = re.sub(r'\+\d+$', '', results[-2][8])
            if not results[-2][8]:
                results[-2][8] = None
            results[-1][0] = p.group(1) + results[-1][0]
            results[-1][1] = p.group(1)
    else:
        results = [list(m.groups())]
    results = parse_roll(die_str[m.end():], results)
    return results

def do_roll(parsed, dice_emojis, aprFool=False):
    ZWS = '\u200B'              # Zero Width Space
    results = []
    for p in parsed:
        num = p[1]         # No of dice to roll
        if num:
            num = int(num)
        else:
            num = 1
        sides = int(p[2])  # No of side on die
        if p[3]:
            min_score = int(p[4])
        else:
            min_score = 1
        if min_score > sides:
            min_score = int(sides)

        if p[5] in ['@','@a','@adv','@advantage']:
            if num < 2:
                num = 2
            p[6] = 'k'
            p[7] = '1'
        elif p[5] in ['@d','@dis','@disadv','@disadvantage']:
            if num < 2:
                num = 2
            p[6] = 'kl'
            p[7] = '1'

        adv = p[6]         # (dis)advantage
        if adv:
            advnum = int(p[7])
        #
        extra = p[8]
        if not extra:
            extra = ''
        if p[0][-1] in ['+','*','/','-','^']:
            sign = p[0][-1]
        else:
            sign = ''
        #
        if aprFool:
            rolls = [1 for n in range(num)]
        else:
            rolls = [random.randint(min_score,sides) for n in range(num)]
        if adv in ['k','kh']:
            keep_only = nlargest(advnum, rolls)
            discount = nsmallest(len(rolls)-advnum, rolls)
        elif adv == 'kl':
            keep_only = nsmallest(advnum, rolls)
            discount = nlargest(len(rolls)-advnum, rolls)
        elif adv in ['d', 'dh']:
            keep_only = nsmallest(len(rolls)-advnum, rolls)
            discount = nlargest(advnum, rolls)
        elif adv == 'dl':
            keep_only = nlargest(len(rolls)-advnum, rolls)
            discount = nsmallest(advnum, rolls)
        else:
            keep_only = rolls
            discount = []
        if f"d{sides}" in dice_emojis:
            # Join with zero width space
            response = ZWS.join([f"d{sides}"]*num) +\
                       "(" + '+'.join(map(str, rolls)) + f"){extra}{sign}"
        else:
            response = f"{num}d{sides}(" +\
                       '+'.join(map(str, rolls)) + f"){extra}{sign}"
        sumstr = str(sum(keep_only)) + f"{extra}{sign}"
        if discount:
            for die in discount:
                die_re = f"([\(\+\*\/\-])({die})([\+\*\/\-\)])"
                response = re.sub(die_re, r'\1~~_\2_~~\3', response, count=1)
            for die in keep_only:
                die_re = f"([\(\+\*\/\-])({die})([\+\*\/\-\)])"
                response = re.sub(die_re, r'\1**\2**\3', response, count=1)
        results.append((response, sumstr))
    return results

