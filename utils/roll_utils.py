import random
import re
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
    """Roll 4d6dl1 six times
    """
    results = []
    for _ in range(6):
        rolls = [random.randint(1,6) for n in range(4)]
        result = sum(sorted(rolls, reverse=True)[:-1])
        results.append(result)
    return results

def parse_roll(die_str, results=None):
    """Parse dice notation

    Dice syntax `AdBmCkD+E...`
    All uppercase letters are numeric variables 
    All lowercase letters are fixed
      (i.e. if you are specifying a minimum `mC`,
       the letter `m` must be provided followed by a number replacing `C`)
    where:
      `A`   number of dice                      (OPTIONAL - defaults to 1)
      `dB`  number of sides `B` on dice         (MANDATORY)
      `mC`  minimum result `C` for each die     (OPTIONAL)
      `kD`  number of dice `D` to keep/drop     (OPTIONAL)
            `k` can be replaced by:
              - `kh` keep highest (same as `k`)
              - `kl` keep lowest
              - `dh` drop highest
              - `dl` drop lowest
            specials (replace `kD` with the following):
              - `@adv` (advantage) keep highest 1 (defaults to 2 dice `A`)
              - `@dis` (disadvantage) keep lowest 1 (defaults to 2 dice `A`)
      `+E`  add `E` to the final result         (OPTIONAL)
            `+` can be replaced by:
              - `-` subtract `E` from final result
              - `*` multiply final result by `E`
              - `/` divide final result by `E`

    It is possible to roll more than 2 dice with advantage/disadvantage. Only
      the highest/lowest single result will be kept.
    
    The sequence can be repeated any number of times. e.g.:
      `d20@adv+5+2d4+1`
        Rolls two 20-sided dice
        Keeps the highest single result
        Adds 5
        Adds the results from two four-sided dice
        Adds 1
    """
    if not die_str:
        return results
    dice_re = r'^((\d+)?d(\d+)(?:m(\d+))?(?:(@(?:d(?:is)?)?(?:a(?:dv)?)?(?:antange)?)|([kd][hl]?)(\d+))?((?:[\+\*\-\/]\d+)+)?[\+\-\*/\^]?)'
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
            min_score = int(p[3])
        else:
            min_score = 1
        if min_score > sides:
            min_score = int(sides)

        if p[4] in ['@','@a','@adv','@advantage']:
            if num < 2:
                num = 2
            p[5] = 'k'
            p[6] = '1'
        elif p[4] in ['@d','@dis','@disadv','@disadvantage']:
            if num < 2:
                num = 2
            p[5] = 'kl'
            p[6] = '1'

        adv = p[5]         # (dis)advantage
        if adv:
            advnum = int(p[6])
        #
        extra = p[7]
        if not extra:
            extra = ''
        if p[0][-1] in ['+','*','/','-','^']:
            sign = p[0][-1]
        else:
            sign = ''
        #
        if aprFool:  # Always rolls a 1 on April Fool's
            rolls = [1 for n in range(num)]
        else:
            rolls = [random.randint(min_score,sides) for n in range(num)]

        if adv in ['k','kh']:
            keep_only = nlargest(advnum, rolls)
            not_kept = nsmallest(len(rolls)-advnum, rolls)
        elif adv == 'kl':
            keep_only = nsmallest(advnum, rolls)
            not_kept = nlargest(len(rolls)-advnum, rolls)
        elif adv in ['d', 'dh']:
            keep_only = nsmallest(len(rolls)-advnum, rolls)
            not_kept = nlargest(advnum, rolls)
        elif adv == 'dl':
            keep_only = nlargest(len(rolls)-advnum, rolls)
            not_kept = nsmallest(advnum, rolls)
        else:
            keep_only = rolls
            not_kept = []
        if f"d{sides}" in dice_emojis:
            # Join with zero width space
            response = ZWS.join([f"d{sides}"]*num) +\
                       "(" + '+'.join(map(str, rolls)) + f"){extra}{sign}"
        else:
            response = f"{num}d{sides}(" +\
                       '+'.join(map(str, rolls)) + f"){extra}{sign}"
        sumstr = str(sum(keep_only)) + f"{extra}{sign}"
        if not_kept:
            for die in not_kept:
                die_re = f"([\(\+\*\/\-])({die})([\+\*\/\-\)])"
                response = re.sub(die_re, r'\1~~_\2_~~\3', response, count=1)
            for die in keep_only:
                die_re = f"([\(\+\*\/\-])({die})([\+\*\/\-\)])"
                response = re.sub(die_re, r'\1**\2**\3', response, count=1)
        results.append((response, sumstr))
    return results

