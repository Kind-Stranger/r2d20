from dataclasses import dataclass, asdict

import discord

__all__ = ['BonesRules', 'rulesets']

INSTRUCTION_TEMPLATE = """• All players roll {init_dice} {init_dice_sides}-sided dice.
• Play proceeds clockwise around the table, with the host of the game going last.
• On their turn, a player can choose to "stand" or "roll".
    If the player stands, the next player can take a turn.
    A player who rolls takes an additional {dice_sides}-sided die and rolls it.
• If the total of their dice exceeds {score_limit}, they "bust" and are out of the game.
    Otherwise, they can keep rolling additional {dice_sides}-sided dice until they either stand or bust.
• After everyone has had a turn, the highest point total (excluding players who busted)
    wins the game and takes the pot.
"""

VARIANT_INSTRUCTION_TEMPLATE = INSTRUCTION_TEMPLATE +\
    """• If the target score is reached exactly, the target score increases by 1.
"""


@dataclass
class BonesRules:
    title: str = None
    description: str = None
    dice_sides: int = 0
    init_dice: int = 0
    init_dice_sides: int = 0
    init_dice_emoji: str | discord.Emoji = None
    target_score: int = 0
    variant_rules: bool = False
    instructions: str = None

    asdict = asdict


baldurs_bones_rules = BonesRules(
    title="Baldur's Bones",
    description='A game for d6 enjoyers',
    dice_sides=6,
    target_score=21,
    init_dice=3,
    init_dice_sides=6,
    instructions=INSTRUCTION_TEMPLATE.format(
        init_dice=3,
        init_dice_sides=6,
        dice_sides=6,
        score_limit=21,
    ),
)

variant_bones_rules = BonesRules(
    title="Baldur's Bones (variant)",
    description='A game for d6 enjoyers. The target score increases when met',
    init_dice=3,
    init_dice_sides=6,
    dice_sides=6,
    target_score=21,
    variant_rules=True,
    instructions=VARIANT_INSTRUCTION_TEMPLATE.format(
        init_dice=3,
        init_dice_sides=6,
        dice_sides=6,
        score_limit=21,
    ),
)

kobolds_knuckles_rules = BonesRules(
    title="Kobold's Knuckles",
    description='A game for d4 enjoyers',
    init_dice=1,
    init_dice_sides=6,
    dice_sides=4,
    target_score=10,
)

variant_knuckles_rules = BonesRules(
    title="Kobold's Knuckles (variant)",
    description='A game for d4 enjoyers. The target score increases when met',
    init_dice=1,
    init_dice_sides=6,
    dice_sides=4,
    target_score=10,
    variant_rules=True,
    instructions=INSTRUCTION_TEMPLATE.format(
        init_dice=1,
        init_dice_sides=4,
        dice_sides=4,
        score_limit=10,
    ),
)

rulesets: dict[str, BonesRules] = {
    'baldurs_bones': baldurs_bones_rules,
    'variant_bones': variant_bones_rules,
    'kobolds_knuckles': kobolds_knuckles_rules,
    'variant_knuckles': variant_knuckles_rules,
}
