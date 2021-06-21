<h1 align="center">
    obsidian.py
</h1>
<p align="center">
    <sup>
        A wrapper around Obsidian's REST and Websocket API.
    </sup>
</p>

----

## What is obsidian.py?
A fully object-oriented wrapper around [Obsidian v2](https://github.com/mixtape-bot/obsidian/blob/v2/) designed for [discord.py](https://github.com/Rapptz/discord.py/).  
This wrapper is based off of [Slate](https://github.com/Axelancerr/Slate).

## Requirements
### Python (3.7+)
- [discord.py](https://pypi.org/project/discord.py/)
- [aiohttp](https://pypi.org/project/aiohttp/)
### Obsidian (v2)
- [Obsidian v2](https://tinyurl.com/obsidian-v2)
- [obsidian.yml](https://github.com/mixtape-bot/obsidian/blob/v2/obsidian.yml/)

## Features
- Fully asynchronous
- Object oriented
- Playlist support
- Advanced audio filter support
- Querying tracks from many sources 
- Fully typed 

## Examples 
### Basic
```py 
import discord
import obsidian

from discord.ext import commands


class Bot(commands.Bot):
    def __init__(self, **options):
        super().__init__(**options)
        self.loop.create_task(self.start_obsidian)

    async def start_obsidian(self):
        self.obsidian = await obsidian.initiate_node(bot=self)


bot = Bot(command_prefix='$')

@bot.command()
async def connect(ctx):
    channel = ctx.author.voice.channel
    player = ctx.bot.obsidian.get_player(ctx.guild)
    await player.connect(channel)

@bot.command()
async def play(ctx, *, song: str):
    player = ctx.bot.obsidian.get_player(ctx.guild)
    track = await ctx.bot.obsidian.search_track(song, source=obsidian.Source.YOUTUBE)
    await player.play(track)


if __name__ == '__main__':
    bot.run('TOKEN')

```

## Credits
- Heavily based off of [Slate](https://github.com/Axelancerr/Slate)
- Inspired by [wavelink](https://github.com/PythonistaGuild/Wavelink)
