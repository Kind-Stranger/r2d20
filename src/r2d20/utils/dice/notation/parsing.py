import logging
import re
from dataclasses import dataclass

import discord

from .rolling import ParsedDiceRoller

__all__ = [
    'NotationParseException',
    'DiceNotationParser',
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
        self._calculate_results()

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
