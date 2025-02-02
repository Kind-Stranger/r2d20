import random
import re

from dataclasses import dataclass

NOTATION_PATTERN = r'''(?x)^
    (?P<num_dice>\d+)?          # Number of dice                (optional)
    d (?P<dice_type>\d+|f)      # "d" with dice type           (mandatory)
    (                           # (Start keep/drop group group) (optional)
        (?P<advantage>@adv|@dis)    # Advangage/disadvantage flag
        |(?P<keep_drop>[kd])        # Keep or drop dice
        (?P<high_low>[hl])?         # "h"ighest or "l"owest (highest if omitted)
        (?P<kd_num_dice>\d+)        # number of dice to keep/drop
    )?                          # (End optional keep/drop group)
    (?:(?P<min_max>min|max)
         (?P<m_score>\d+))?     # min/max score                 (optional)
    (?P<modifier>(?:[*/+-]\d+(?!d))+)? # Modifier               (optional)
    (?P<more>[*/+-])?           # Pssibly more dice
'''


@dataclass
class ParsedDice:
    """Data class for holding results of name groups match by
    notation pattern
    """
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


class ParsedDiceRoller:

    def __init__(self, parsed_dice: ParsedDice):
        """Validate and roll parsed dice

        Args:
            parsed_dice (ParsedDice): parsed dice
        """
        self.pd = parsed_dice
        self._raw_results: list[int] = None
        self._results: list[int] = None
        self._total: int = 0
        self.validate()
        self.roll()

    @property
    def raw_results(self) -> list[int]:
        """Raw dice rolls"""
        return self._raw_results

    @property
    def results(self) -> list[int]:
        """Individual die results after keep/drop applied"""
        return self._results

    @property
    def total(self) -> int:
        """Total value of these dice with all parameters applied"""
        return self._total

    def validate(self):
        """Check the limitations on the parsed dice"""
        if self.pd.num_dice > 100:
            raise ValueError("Can't roll this many dice")
        if self.pd.dice_type > 1000:
            raise ValueError("Can't roll dice this big")

    def roll(self):
        """Roll the parsed dice, applying the other parameeters and
        setting the total"""
        num_dice = self.pd.num_dice
        if self.pd.advantage:
            num_dice = 2
        #
        if self.pd.dice_type == "f":
            self._raw_results = [
                random.choice([-1, 0, 1]) for _ in range(num_dice)
            ]
        else:
            self._raw_results = [
                random.randint(1, self.pd.dice_type)
                for _ in range(num_dice)
            ]
        #
        sorted_results = sorted(self._raw_results)
        if self.pd.advantage == '@adv':
            self._results = sorted_results[-1:]
        elif self.pd.advantage == '@dis':
            self._results = sorted_results[:1]
        elif (self.pd.keep_drop == 'k' and self.pd.high_low in ['h', None]) or\
             (self.pd.keep_drop == 'd' and self.pd.high_low in ['l', None]):
            drop_lowest = len(sorted_results) - self.pd.kd_num_dice
            self._results = sorted_results[drop_lowest:]
        elif self.pd.keep_drop:
            self._results = sorted_results[:self.pd.kd_num_dice]
        else:
            self._results = self._raw_results
        #
        self._total = sum(self._results)

        if str(self.pd.modifier).startswith("+"):
            self._total += int(self.pd.modifier[1:])
        elif str(self.pd.modifier).startswith("-"):
            self._total += int(self.pd.modifier[1:])
        elif str(self.pd.modifier).startswith("*"):
            self._total += int(self.pd.modifier[1:])
        elif str(self.pd.modifier).startswith("/"):
            self._total += int(self.pd.modifier[1:])
        #
        if str(self.pd.min_max).startswith("min") and\
           self.pd.m_score < int(self.pd.min_max[3:]):
            self._total = self.pd.m_score
        elif str(self.pd.min_max).startswith("max") and\
                self.pd.m_score > int(self.pd.min_max[3:]):
            self._total = self.pd.m_score


class DiceNotationParser:
    def __init__(self, notation: str):
        """Parser of dice notation

        Args:
            notation (str): dice notation
        """        
        self.orig_notation: str = str(notation)
        self._parsed: list[ParsedDice] = None
        self._rolled: list[ParsedDiceRoller] = None
        self.results: list[int] = None
        self.total: int = 0

    def process(self):
        """Process the dice notation"""
        self._parse()
        self._calculate_results()

    def _parse(self):
        """Parse dice notation and add to parsed list"""
        notation = self.orig_notation.replace(' ', '').lower()
        pos = 0
        while pos < len(notation):
            match = re.search(NOTATION_PATTERN, notation[pos:])
            if match is None:
                raise ValueError(f"Invalid dice notation: {self.orig_notation}")
            groupdict = {}
            for name, value in match.groupdict().items():
                if value is None:
                    continue
                val = int(value) if re.match(r'^\d+', value) else value
                groupdict[name] = val
            pd = ParsedDice(match.group(0), **groupdict)
            pos += len(match.group(0))
            self._parsed.append(pd)

    def _calculate_results(self):
        """Roll the parsed dice and append to results and set total"""
        for parsed_dice in self._parsed:
            roller = ParsedDiceRoller(parsed_dice)
            self._rolled.append(roller)
            self.results.append(roller.total)
        self.total = sum(self.results)
