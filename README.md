<h1 align="center">
    <img src="https://i.imgur.com/0wN8rhA.png" alt="obsidian.py banner" />
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
- [Java JDK 16](https://www.oracle.com/java/technologies/javase-jdk16-downloads.html)
- [Obsidian v2](https://cdn.discordapp.com/attachments/381963689470984203/856979799733174272/Obsidian2.jar/)
- [obsidian.yml](https://github.com/mixtape-bot/obsidian/blob/v2/obsidian.yml/)

## Features
- Fully asynchronous
- Object oriented
- Playlist support
- Advanced audio filter support
- Querying tracks from many sources
- Spotify support
- Fully typed 

## Setting up Obsidian & obsidian.py

### Downloading Obsidian
First, we must download Obsidian itself.  
The JAR located in current Obsidian respoitory is outdated, however the working build can be downloaded [here](https://cdn.discordapp.com/attachments/381963689470984203/856979799733174272/Obsidian2.jar).

### Creating obsidian.yml
You must have an [obsidian.yml](https://github.com/mixtape-bot/obsidian/blob/v2/obsidian.yml/) file before running Obsidian.  
Create/download the file in the same directory as the JAR file (mentioned above).

### Installing obsidian.py
Next, let's install obsidian.py.  
You can download it directly from PyPI (Using `pip`):
```sh 
$ pip install obsidian.py
```

Or, if you want early access to new additions for obsidian.py, clone directly from Github:
```sh 
$ pip install git+https://github.com/jay3332/obsidian.py
```
### Running Obsidian
Make sure you have [Java 16](https://www.oracle.com/java/technologies/javase-jdk16-downloads.html) or higher downloaded.

To run Obsidian, `cd` to the directory the JAR file you downloaded above is located in:
```sh 
$ cd /path/to/directory
```

Then, run it using Java's command line tool:
```sh
$ cd /path/to/directory

$ java -jar Obsidian.jar 
```

(Replace `Obsidian.jar` to the name of the JAR file.)

If successful, you should see many things getting logged into console.

You're all set - now you just have to write code.  
See below for examples, or take a look into the [examples folder](https://github.com/jay3332/obsidian.py/tree/master/examples).

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
