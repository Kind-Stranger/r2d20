import random
import re

from dataclasses import dataclass

NOTATION_PATTERN = r'''(?x)^
    (?P<num_dice>\d{1,3})?      # Number of dice                (optional)
    d (?P<dice_type>\d+|f)      # "d" with dice type           (mandatory)
    (                           # (Start keep/drop group group) (optional)
        (?P<advantage>@adv|@dis)    # Advangage/disadvantage flag
        |(?P<keep_drop>[kd]         # Keep or drop dice
        (?P<high_low>[hl])?         # "h"ighest or "l"owest (highest if omitted)
        (?P<kd_num_dice>\d+))       # number of dice to keep/drop
    )?                          # (End optional keep/drop group)
    (?:(?P<min_max>min|max)
         (?P<m_score>\d+))?     # min/max score                 (optional)
    (?P<modifier>(?:[*/+-]\d+)+)? # Modifier                    (optional)
    (?P<more>[*/+-])?
'''


@dataclass
class ParsedDice:
    notation: str  # The matched portion of the notation
    dice_type: int | str  # str only used for fudge/fate dice
    num_dice: int = 1
    advantage: str = None
    keep_drop: str = None
    high_low: str = None
    kd_num_dice: int = 0
    modifier: str = None
    min_max: str = None
    m_score: int = 0
    more: str = None

    _raw_results = None
    _results = None
    _total = 0

    @property
    def raw_results(self) -> list:
        return self._raw_results

    @property
    def results(self) -> list:
        return self._results

    @property
    def total(self) -> int:
        return self._total

    def roll(self) -> list:
        if self.advantage:
            self.num_dice = 2
        #
        if self.dice_type == "f":
            self._raw_results = [random.choice(
                [-1, 0, 1]) for _ in self.num_dice]
        else:
            self._raw_results = [random.randint(1, self.dice_type)
                                 for _ in self.num_dice]
        #
        sorted_results = sorted(self._raw_results)
        if self.advantage == 'adv':
            self._results = sorted_results[-1:]
        elif self.advantage == 'dis':
            self._results = sorted_results[:1]
        elif (self.keep_drop == 'k' and self.high_low == 'h') or\
             (self.keep_drop == 'd' and self.high_low == 'l'):
            drop_lowest = len(sorted_results) - self.kd_num_dice
            self._results = sorted_results[drop_lowest:]
        elif self.keep_drop:
            self._results = sorted_results[:self.kd_num_dice]
        else:
            self._results = self._raw_results
        #
        self._total = sum(self._results)

        if str(self.modifier).startswith("+"):
            self._total += int(self.modifier[1:])
        elif str(self.modifier).startswith("-"):
            self._total += int(self.modifier[1:])
        elif str(self.modifier).startswith("*"):
            self._total += int(self.modifier[1:])
        elif str(self.modifier).startswith("/"):
            self._total += int(self.modifier[1:])
        #
        if str(self.min_max).startswith("min") and\
           self.m_score < int(self.min_max[3:]):
            self._total = self.m_score
        elif str(self.min_max).startswith("max") and\
                self.m_score > int(self.min_max[3:]):
            self._total = self.m_score


class DiceNotationParser:
    def __init__(self, notation: str):
        self.notation = str(notation)
        self.results = []
        self._parsed: list[ParsedDice] = []
        self._rolled = []
        self.total = 0

    def process(self):
        self._parse()
        self._calculate_results()

    def _parse(self):
        notation = self.notation.replace(' ', '').lower()
        match = re.search(NOTATION_PATTERN, notation)
        if match is None:
            raise ValueError("Invalid dice notation: "+self.notation)
        groupdict = {}
        for name, value in match.groupdict().items():
            if value is None:
                continue
            val = int(value) if re.match(r'^\d+', value) else value
            groupdict[name] = val
        pd = ParsedDice(match.group(0), **groupdict)
        self._parsed.append(pd)

    def _calculate_results(self):
        for parsed in self._parsed:
            for dice in range(parsed.num_dice):
                dice.roll()
                self.results.append(dice)
