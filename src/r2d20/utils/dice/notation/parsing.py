import logging
import random
import re

import discord

from . import ParsedDice

__all__ = [
    'DiceNotationParser',
    'NotationParseException',
    'ParsedDiceRoller',
    'create_embed_from_notation'
]

logger = logging.getLogger()

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


class NotationParseException(Exception):
    pass


class DiceNotationParser:
    def __init__(self, notation: str):
        """Parser of dice notation

        Args:
            notation (str): dice notation
        """
        self.orig_notation: str = str(notation)
        self.parsed: list[ParsedDice] = []
        self.rolled: list[ParsedDiceRoller] = []
        self.results: list[int] = []
        self.total: int = 0

    def process(self):
        """Process the dice notation"""
        self._parse()
        logger.debug(f"Parsed: {self.parsed}")
        self._calculate_results()
        logger.debug(f"Rolled: {self.rolled}")
        logger.debug(f"Results: {self.results}")

    def _parse(self):
        """Parse dice notation and add to parsed list

        Raises:
            NotationException: Invalid dice notation
        """
        notation = self.orig_notation.replace(' ', '').lower()
        pos = 0
        while pos < len(notation):
            match = re.search(NOTATION_PATTERN, notation[pos:])
            if match is None:
                raise NotationParseException(
                    f"Invalid dice notation: {self.orig_notation}")
            groupdict = {}
            for name, value in match.groupdict().items():
                if value is None:
                    continue
                val = int(value) if re.match(r'^\d+', value) else value
                groupdict[name] = val
            pd = ParsedDice(match.group(0), **groupdict)
            pos += len(match.group(0))
            self.parsed.append(pd)

    def _calculate_results(self):
        """Roll the parsed dice and append to results and set total"""
        for parsed_dice in self.parsed:
            roller = ParsedDiceRoller(parsed_dice)
            self.rolled.append(roller)
            self.results.append(roller.total)
        self.total = sum(self.results)


def create_embed_from_notation(notation: str) -> discord.Embed:
    parser = DiceNotationParser(notation)
    parser.process()
    with_results = [insert_result(dice.pd.notation, dice.raw_results, dice.results)
                    for dice in parser.rolled]
    with_results = f'{"".join(with_results)} = {parser.total}'
    embed = discord.Embed(title=str(parser.total), description=with_results)
    return embed


def insert_result(notation: str,
                  raw_results: list[int],
                  results: list[int]) -> str:
    match = re.match(r'^\d*d(\d+|f)', notation)
    results_copy = results.copy()
    decorated = []
    for raw in raw_results:
        if raw in results_copy:
            results_copy.remove(raw)
            decorated.append(f"**{raw}**")
        else:
            decorated.append(f"~~{raw}~~")

    decorated = str(decorated).replace("'", '')
    return f"{notation[:match.end()]}{decorated}{notation[match.end():]}"


class ParsedDiceRoller:
    def __init__(self, parsed_dice: ParsedDice):
        """Validate and roll parsed dice

        Args:
            parsed_dice (ParsedDice): parsed dice
        """
        self.pd = parsed_dice
        self._raw_results: list[int] = []
        self._results: list[int] = []
        self._total: int = 0
        self.validate()
        self.roll()

    def __repr__(self):
        return f'<ParsedDiceRoller raw_results={self.raw_results}, results={self.results}, total={self.total}>'

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
        """Check the limitations on the parsed dice

        Raises:
            NotationException: too many dice or sides
        """
        if self.pd.num_dice > 100:
            raise NotationParseException("Can't roll this many dice")
        if isinstance(self.pd.dice_type, int) and self.pd.dice_type > 1000:
            raise NotationParseException("Can't roll dice this big")

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
        elif (self.pd.keep_drop == 'k' and self.pd.high_low in ['h', None]):
            drop_lowest = len(sorted_results) - self.pd.kd_num_dice
            self._results = sorted_results[drop_lowest:]
        elif (self.pd.keep_drop == 'k' and self.pd.high_low == 'l'):
            self._results = sorted_results[:self.pd.kd_num_dice]
        elif (self.pd.keep_drop == 'd' and self.pd.high_low == 'h'):
            drop_highest = len(sorted_results) - self.pd.kd_num_dice
            self._results = sorted_results[:drop_highest]
        elif (self.pd.keep_drop == 'd' and self.pd.high_low in ['l', None]):
            self._results = sorted_results[self.pd.kd_num_dice:]
        else:
            self._results = self._raw_results
        #
        self._total = sum(self._results)

        if (self.pd.min_max == "min" and self._total < self.pd.m_score) or\
           (self.pd.min_max == "max" and self._total > self.pd.m_score):
            self._total = self.pd.m_score

        if str(self.pd.modifier).startswith("+"):
            self._total += int(self.pd.modifier[1:])
        elif str(self.pd.modifier).startswith("-"):
            self._total -= int(self.pd.modifier[1:])
        elif str(self.pd.modifier).startswith("*"):
            self._total *= int(self.pd.modifier[1:])
        elif str(self.pd.modifier).startswith("/"):
            self._total /= int(self.pd.modifier[1:])
