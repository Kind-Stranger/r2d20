from dataclasses import dataclass

__all__ = ["ParsedDice"]


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
