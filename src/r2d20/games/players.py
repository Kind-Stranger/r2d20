
import discord


class PlayerBase:
    """Base class which allows direct access to discord.Member attributes.
    Useful for keeping track of scores and such.
    """
    def __init__(self, member: discord.Member):
        self._member = member

    def __str__(self):
        return self._member.display_name

    @property
    def member(self):
        return self._member
    
    def __getattr__(self, name):
        """Gives direct access to discord.Member attributes"""
        if hasattr(self.member, name):
            return getattr(self.member, name)
        else:
            raise AttributeError(f"'{self.__class__.__name__} has no attribute '{name}'")
