# r2d20
A dice-rolling bot for Discord

Tested with Python 3.12

## Key Features
 * Basic dice roll commands (e.g. /d20)
 * Advance dice roll notation command (/roll)
 * Simple multiplayer dice games
 * Bot admin commands

## Required Packages
 * discord.py (version 2.5 or later) https://github.com/Rapptz/discord.py

## Running The Bot
 * Follow Discord's bot setup guide.
 * Clone the project.
 * Install required packages (See above)
 * Create a .env file at the root level and include the following:
 ```
PYTHONPATH=src
TOKEN=<your bot's token>
```
 * Run `src/r2d20/__main__.py`