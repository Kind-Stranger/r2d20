import logging
import discord

logger = logging.getLogger(__name__)


class LobbyView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, *,
                 lobby_title: str = None, lobby_description: str = 'Join the game!', max_players: int = 10, **kwargs):
        """A Lobby for gathing players. The embed is updated by the view automatically.

        Examples:
            Initialise this class and respond to the interaction with the embed property.
            ```python
            lobby = LobbyView(interaction, **interaction.extras)
            await interaction.response.send_message(embed=lobby.embed, view=lobby)
            await lobby.wait()
            ```

        Args:
            interaction (discord.Interaction): The interaction that initiated the lobby.
            lobby_title (str, optional): The title of the lobby, defaults to the user's display name.
            lobby_description (str, optional): A description for the lobby, defaults to 'Join the game!'.
            max_players (int, optional): The maximum number of players allowed in the lobby, defaults to 10.
            kwargs (dict): Additional keyword arguments sent to discord.ui.View

        Attributes:
            interaction (discord.Interaction): The interaction that initiated the lobby.
            embed (discord.Embed): The embed for the lobby.
            members (list[discord.Member]): A list of members, initially containing the user who initiated the interaction.
            title (str): The title of the lobby.
            description (str): The description for the lobby.
            max_players (int): The maximum number of players allowed in the lobby.
        """
        super().__init__(**kwargs)
        self.interaction = interaction
        if lobby_title is None:
            self.title = f"{interaction.user.display_name}'s Lobby"
        else:
            self.title = str(lobby_title)
        #
        self.description = str(lobby_description)
        self.max_players = int(max_players)
        self.members: list[discord.Member | discord.User] = [interaction.user]
        self.final_interaction: discord.Interaction = None
        self._embed_color = discord.Color.random()

    @property
    def embed(self) -> discord.Embed:
        embed = discord.Embed(title=self.title,
                              description=self.description, color=self._embed_color)
        if self.members:
            embed.set_author(name=self.members[0].display_name,
                             icon_url=self.members[0].display_avatar.url)
        for i, member in enumerate(self.members, start=1):
            embed.add_field(
                name=f'Player {i}', value=member.display_name, inline=False)
        return embed

    @discord.ui.button(label='Join', style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add the player to the game."""
        if interaction.user in self.members:
            await interaction.response.defer()
            return

        self.members.append(interaction.user)
        logger.debug(f'{interaction.user} has joined the lobby.')
        if len(self.members) >= 10:
            self.members = self.members[:self.max_players]
            button.disabled = True
            button.label = 'Full'
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label='Leave', style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Remove the player from the game."""
        if interaction.user not in self.members:
            await interaction.response.defer()
            return
        elif interaction.user == self.members[0]:
            await interaction.response.send_message("You are not allowed to leave your own lobby.", ephemeral=True,
                                                    delete_after=10.0)
            return

        self.members.remove(interaction.user)
        logger.debug(f'{interaction.user} has left the lobby.')
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label='Start', style=discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start the game."""
        if [interaction.user] != self.members[:1]:
            await interaction.response.send_message("Only Player 1 can start the game.", ephemeral=True,
                                                    delete_after=10.0)
            return

        self.stop()
        self.clear_items()
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def on_timeout(self):
        """Remove the view from the message."""
        logger.debug("Lobby timed out.")
        self.stop()
        self.clear_items()
        embed = self.embed
        embed.set_footer(text="Lobby timed out.")
        await self.interaction.edit_original_response(embed=embed, view=None)
