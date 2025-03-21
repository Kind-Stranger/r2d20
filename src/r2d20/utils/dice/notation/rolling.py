import random

from .parsing import NotationParseException, ParsedDice


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

        if str(self.pd.modifier).startswith("+"):
            self._total += int(self.pd.modifier[1:])
        elif str(self.pd.modifier).startswith("-"):
            self._total -= int(self.pd.modifier[1:])
        elif str(self.pd.modifier).startswith("*"):
            self._total *= int(self.pd.modifier[1:])
        elif str(self.pd.modifier).startswith("/"):
            self._total /= int(self.pd.modifier[1:])
        #
        if str(self.pd.min_max).startswith("min") and\
           self.pd.m_score < int(self.pd.min_max[3:]):
            self._total = self.pd.m_score
        elif str(self.pd.min_max).startswith("max") and\
                self.pd.m_score > int(self.pd.min_max[3:]):
            self._total = self.pd.m_score
