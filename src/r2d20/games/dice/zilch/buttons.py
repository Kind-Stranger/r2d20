import logging
import random
import discord

__all__ = ['ZilchDieButton']

logger = logging.getLogger(__name__)


class ZilchDieButton(discord.ui.Button):
    """A button representing a die in the Zilch game.

    NOTE:
        The button's label, style and disabled properties are handled by
        this class and will be overridden if passed to the parent class.

    Args:
        **kwargs: Additional keyword arguments sent to discord.ui.Button

    Attributes:
        held_style (discord.ButtonStyle): Style when the die is held.
        unheld_style (discord.ButtonStyle): Style when the die is not held.
        value (int): The current value of the die.
        is_held (bool): Whether the die is currently held.
        is_locked (bool): Whether the die is locked and cannot be rolled again.

    """
    held_style = discord.ButtonStyle.red
    unheld_style = discord.ButtonStyle.grey

    def __init__(self, **kwargs):
        super().__init__(style=self.unheld_style, emoji="🎲", **kwargs)
        self._is_held: bool = False
        self._is_locked: bool = False
        self.roll()

    @property
    def value(self) -> int:
        return self._value

    @property
    def is_held(self) -> bool:
        return self._is_held and not self._is_locked

    @property
    def is_locked(self) -> bool:
        return self._is_locked

    def roll(self) -> int:
        """Roll this die and set button label according to result"""
        self._value = random.randint(1, 6)
        logger.debug(f"Rolled die: {self._value}")
        self._set_label_to_value()

    def toggle_hold(self):
        """Toggle held flag and styles"""
        if self._is_locked:
            logger.warning(f"Toggled hold but die is locked")
            return True
        self._is_held = not self._is_held
        logger.debug(f"Toggled hold:  {self._is_held}")
        self._set_style()

    def lock_if_held(self):
        """Lock the die if it is currently held"""
        if self._is_held:
            self._is_locked = True
            self._set_disabled()

    def reset(self):
        """Reset the die to its default state"""
        logger.debug(f"Resetting die")
        self._is_held = False
        self._is_locked = False
        self._set_style()
        self._set_label_to_value()

    def _set_label_to_value(self):
        """Sets the label based on the current dice value"""
        self.label = f'[{self._value}]'

    def _set_style(self):
        """Sets the style of the button based on whether it is cuurently held"""
        self.style = self.held_style if self._is_held else self.unheld_style

    def _set_disabled(self):
        """Sets the button to disabled if it has been locked"""
        self.disabled = self._is_locked
