import logging

import discord

from players import PlayerBase

__all__ = ['ZilchPlayer']

logger = logging.getLogger(__name__)


class ZilchPlayer(PlayerBase):
    def __init__(self, member: discord.Member):
        """Keeps score in the dice game for a discord.Member"""
        super().__init__(member)
        self.score = 0
        self.current_round_score: int = 0
        self.score_history: list[int] = []

    def bank(self):
        """Bank the current round score and reset it"""
        logger.debug(f"Banking {self.current_round_score}")
        self.score_history.append(self.current_round_score)
        self.score += self.current_round_score
        self.current_round_score = 0
