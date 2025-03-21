import discord as _discord

# Prevent discord PyNaCl missing warning
_discord.voice_client.VoiceClient.warn_nacl = False
