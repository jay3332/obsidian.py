import discord
import obsidian

from discord.ext import commands


description = """
Basic music bot with simple join, leave, play, and pause commands.
"""

bot = commands.Bot(command_prefix='$', description=description)
bot.obsidian = None


async def _setup():
    bot.obsidian = await obsidian.initiate_node(bot)

bot.loop.create_task(_setup())


@bot.command(aliases=['connect'])
async def join(ctx: commands.Context, *, channel: discord.VoiceChannel = None):
    if channel is None:
        if not ctx.author.voice:
            return await ctx.send('Please join a voice channel.')

        channel = ctx.author.voice.channel

    player = ctx.bot.obsidian.get_player(ctx.guild)
    try:
        await player.connect(channel)
    except discord.HTTPException:
        return await ctx.send('I may not have permissions to join VC.')
    else:
        await ctx.send('Connected')


@bot.command()
async def play(ctx: commands.Context, *, song: str):
    player = ctx.bot.obsidian.get_player(ctx.guild)
    if not player.connected:
        await ctx.invoke(join)

    # Check a second time
    if not player.connected:
        return

    track = await bot.obsidian.search_track(song, source=obsidian.Source.YOUTUBE)
    if not track:
        return await ctx.send('No songs were found.')

    await player.play(track)
    await ctx.send(f'Now playing: {track.title}')


@bot.command(aliases=['disconnect'])
async def leave(ctx: commands.Context):
    ctx.bot.obsidian.destroy_player(ctx.guild)
    await ctx.send('Goodbye...')


@bot.command(aliases=['resume'])
async def pause(ctx: commands.Context):
    player = ctx.bot.obsidian.get_player(ctx.guild)
    if not player.connected:
        return

    new_pause = await player.set_pause()  # Let pause be handled automatically
    await ctx.send(f'Set pause to {new_pause}.')


if __name__ == '__main__':
    bot.run(...)
