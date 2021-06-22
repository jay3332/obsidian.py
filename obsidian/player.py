from __future__ import annotations

import time
import typing
import discord
import logging

from abc import ABC
from discord.ext import commands

from .filters import FilterSink, VolumeFilter, BaseFilter, Equalizer
from .track import Track, Playlist
from .events import get_cls

from .enums import OpCode, Source


Bot = typing.Union[discord.Client, discord.AutoShardedClient, commands.Bot, commands.AutoShardedBot]

__all__: list = [
    'Player',
    'Protocol'
]

__log__: logging.Logger = logging.getLogger('obsidian.player')


class Protocol(discord.VoiceProtocol, ABC):
    def __init__(self, player: Player) -> None:
        super().__init__(player.bot, player.channel)

        self.client = player.bot
        self.channel = player.channel

        self._player = player

    def __inject(self) -> None:
        self.client._connection._add_voice_client(self.guild.id, self)

    @property
    def player(self) -> Player:
        return self._player

    @property
    def guild(self) -> discord.Guild:
        return self.player.guild

    async def on_voice_server_update(self, data: typing.Dict[str, typing.Any]) -> None:
        __log__.debug(f'PLAYER | {self.guild.id} received VOICE_SERVER_UPDATE: {data}')

        self.player._voice_server_update_data = data
        await self.player.dispatch_voice_update()

    async def on_voice_state_update(self, data: typing.Dict[str, typing.Any]) -> None:
        __log__.debug(f'PLAYER | {self.guild.id} received VOICE_STATE_UPDATE: {data}')

        channel_id = data.get('channel_id')
        if not channel_id:
            self.channel = None
            self.player._channel = None
            self.player._session_id = None
            self.player._voice_server_update_data = None
            return

        self.channel = self.guild.get_channel(int(channel_id))
        self.player._session_id = data.get('session_id')
        await self.player.dispatch_voice_update()

    async def connect(
            self,
            *,
            timeout: typing.Optional[float] = None,
            reconnect: typing.Optional[bool] = None,
            self_deaf: bool = False
    ) -> None:
        self.__inject()
        await self.guild.change_voice_state(channel=self.channel, self_deaf=self_deaf)
        __log__.info(f'PLAYER | {self.guild.id} connected to voice channel {self.channel.id}')

    async def disconnect(self, *, force: bool = False) -> None:
        if not self.player.connected and not force:
            return

        await self.guild.change_voice_state(channel=None)

        if self.player.node.connected:
            await self.player.stop(force=force)
            await self.player.node.send(OpCode.PLAYER_DESTROY, {'guild_id': str(self.guild.id)})

        del self.player.node._players[self.guild.id]
        self.cleanup()

        __log__.info(f'PLAYER | {self.guild.id} was disconnected.')

    async def move(self, channel: discord.VoiceChannel) -> None:
        await self.player.set_pause(True)
        await self.guild.change_voice_state(channel=channel)

        __log__.info(f'PLAYER | {self.guild.id} moved to {channel.id}.')

        self.channel = channel
        await self.player.set_pause(False)


class Player:
    """
    Represents a guild's player.
    """

    def __init__(self, node, bot: Bot, guild: typing.Union[discord.Guild, discord.Object]) -> None:
        from .node import BaseNode

        self._bot: Bot = bot
        self._node: BaseNode = node
        self._guild: typing.Union[discord.Guild, discord.Object] = guild
        self._channel: typing.Optional[discord.VoiceChannel] = None

        self._voice_server_update_data: typing.Optional[typing.Dict[str, typing.Any]] = None
        self._session_id: typing.Optional[str] = None

        self._last_update: float = 0

        self._frames_sent: typing.Optional[int] = None
        self._frames_lost: typing.Optional[int] = None
        self._frame_data_usable: bool = True

        self._last_position: typing.Optional[float] = None
        self._current_track_id: typing.Optional[str] = None
        self._position: float = 0
        self._paused: bool = False

        self.__protocol: Protocol = None
        self.__sink: FilterSink = FilterSink(self)

        self._current: typing.Optional[Track] = None

        if not isinstance(self._guild, discord.Guild):
            new = self._bot.get_guild(self._guild.id)
            if new:
                self._guild = new

    def __repr__(self) -> str:
        return f'<Player node={self._node.identifier!r} connected={self.connected}>'

    @property
    def bot(self) -> Bot:
        return self._bot

    @property
    def guild(self) -> typing.Union[discord.Guild, discord.Object]:
        return self._guild

    @property
    def guild_id(self) -> int:
        return self._guild.id

    @property
    def channel(self) -> discord.VoiceChannel:
        return self._channel

    @property
    def node(self):
        return self._node

    @property
    def current(self) -> Track:
        return self._current

    @property
    def connected(self) -> bool:
        return self._channel is not None

    @property
    def playing(self) -> bool:
        return self.connected and self._current is not None

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def current_track_id(self) -> typing.Optional[str]:
        return self._current_track_id

    @property
    def voice_client(self) -> Protocol:
        return self.__protocol

    @property
    def filters(self) -> FilterSink:
        return self.__sink

    @filters.setter
    def filters(self, sink: FilterSink) -> None:
        if not isinstance(sink, FilterSink):
            raise TypeError('Filter sinks must inherit from FitlerSink.')

        self.__sink = sink

    @property
    def volume(self) -> int:
        return self.__sink.volume.percent if self.__sink.volume else 100

    @property
    def equalizer(self) -> typing.Optional[Equalizer]:
        return self.__sink.equalizer

    eq = equalizer

    @property
    def listeners(self) -> typing.List[discord.Member]:
        if not self._channel:
            return []

        def predicate(member: discord.Member) -> bool:
            return not member.bot and not member.voice.deaf or not member.voice.self_deaf

        return [member for member in self._channel.members if predicate(member)]

    @property
    def position(self) -> float:
        if not self.is_playing():
            return 0

        if self._paused:
            return min(self._position, self._current.length)

        position = self._position + ((time.time() * 1000) - self._last_update)

        if position > self._current.length:
            return 0

        return position

    # For people coming from wavelink
    def is_playing(self) -> bool:
        return self.playing

    def is_paused(self) -> bool:
        return self._paused

    def is_connected(self) -> bool:
        return self.connected

    def update_state(self, data: typing.Dict[str, typing.Any]) -> None:
        __log__.info(f'PLAYER | {self.guild.id} updating state: {data}')

        self._last_update = time.time() * 1000

        frames = data.get('frames', {})
        self._frames_sent = frames.get('sent')
        self._frames_lost = frames.get('lost')
        self._frame_data_usable = frames.get('usable', False)

        current_track = data.get('current_track', {})
        self._current_track_id = current_track.get('track')
        self._last_position = current_track.get('position', 0.)
        self._paused = current_track.get('paused', False)

    def dispatch_event(self, data: typing.Dict[str, typing.Any]) -> None:
        try:
            t = data['t']
        except KeyError:
            __log__.error(f'PLAYER | {self.guild_id!r} received unknown event type: {data}')
            return
        else:
            t = get_cls(t)

        event = t(data)

        __log__.info(f'PLAYER | {self.guild_id!r} dispatching {event.type!r}: {data}')
        self.node.dispatch_event(f'obsidian_{event.type.value.lower()}', self, event)

    async def dispatch_voice_update(self) -> None:
        if not self._session_id or not self._voice_server_update_data:
            return

        payload = {'session_id': self._session_id, **self._voice_server_update_data}
        await self._node.send(OpCode.SUBMIT_VOICE_UPDATE, payload)

    async def connect(
            self,
            channel: discord.VoiceChannel,
            *,
            cls: type = Protocol,
            timeout: typing.Optional[float] = None,
            reconnect: typing.Optional[bool] = None,
            self_deaf: bool = False
    ) -> Protocol:
        if not issubclass(cls, Protocol):
            raise TypeError('Connection class must inherit from Protocol')

        self._channel = channel
        if not self.__protocol:
            self.__protocol = cls(self)

        await self.__protocol.connect(timeout=timeout, reconnect=reconnect, self_deaf=self_deaf)
        return self.__protocol

    async def disconnect(self, *, force: bool = False) -> None:
        if not self.__protocol or not self.connected:
            raise ValueError('No connection to disconnect from.')

        await self.__protocol.disconnect(force=force)

    async def destroy(self, *, force: bool = False) -> None:
        await self.disconnect(force=force)
        del self.node._players[self.guild_id]

        __log__.info(f'PLAYER | {self.guild_id} has been destroyed.')

    async def move(self, channel: discord.VoiceChannel) -> None:
        if not self.__protocol or not self.connected:
            raise ValueError('No connection to move.')

        await self.__protocol.move(channel)

    async def _sanitize_spotify_track(self, track: Track) -> str:
        youtube_equivalent = await self._node.search_track(
            f'{track.title} {track.author} audio',
            source=Source.YOUTUBE,
            suppress=True
        )

        if youtube_equivalent:
            track._id = res = youtube_equivalent.id
            return res

    async def play(
            self,
            track: typing.Union[Track, Playlist],
            *,
            start_time: int = 0,
            end_time: int = 0,
            no_replace: bool = False
    ) -> None:
        if isinstance(track, Playlist):
            track = track.selected_track

        if track.id == 'spotify':
            _id = await self._sanitize_spotify_track(track)
        else:
            _id = track.id

        self._position = 0
        self._last_update = 0

        payload = {
            'guild_id': str(self._guild.id),
            'track': str(_id),
        }

        if 0 < start_time < track.length:
            payload['start_time'] = start_time
        if 0 < end_time < track.length:
            payload['end_time'] = end_time
        if no_replace:
            payload['no_replace'] = no_replace

        await self._node.send(OpCode.PLAY_TRACK, payload)
        __log__.info(f'PLAYER | {self.guild_id} is now playing {track!r}')

        self._current = track

    async def stop(self, *, force: bool = False) -> None:
        if not self._current and not force:
            return

        await self._node.send(OpCode.STOP_TRACK, {'guild_id': str(self.guild_id)})
        __log__.info(f'PLAYER | {self.guild_id} stopped the current track.')

        self._current = None

    async def set_pause(self, pause: typing.Optional[bool] = None) -> bool:
        pause = pause if pause is not None else not self._paused

        await self._node.send(OpCode.PLAYER_PAUSE, {'guild_id': str(self._guild.id), 'state': pause})
        __log__.info(f'PLAYER | {self._guild.id} set its paused state to {pause}.')

        self._paused = res = pause
        return res

    async def set_position(self, position: float) -> None:
        if not self._current or 0 > position > self._current.length:
            return

        await self._node.send(OpCode.PLAYER_SEEK, {'guild_id': str(self._guild.id), 'position': round(position)})
        __log__.info(f'PLAYER | {self.guild.id} set position to {position}')

        self._position = position
        self._last_update = time.time() * 1000

    async def set_volume(self, volume: int = 100) -> None:
        if self.__sink.volume:
            self.__sink.volume.percent = volume

        self.__sink.add(VolumeFilter(volume / 100))
        await self.update_filters()

    async def set_equalizer(self, equalizer: Equalizer) -> None:
        self.__sink.add(equalizer)
        await self.update_filters()

    async def update_filters(self) -> None:
        await self._node.send(OpCode.PLAYER_FILTERS, self.__sink.to_json(self.guild_id))
        __log__.info(f'PLAYER | {self.guild.id} updated filters')

    async def set_filters(self, filters: FilterSink) -> None:
        self.filters = filters
        await self.update_filters()

    async def add_filter(self, *filters: BaseFilter) -> None:
        for filter_ in filters:
            self.__sink.add(filter_)

        await self.update_filters()

    async def remove_filter(self, *filters) -> None:
        for filter_ in filters:
            self.__sink.remove(filter_)

        await self.update_filters()

    async def reset_filters(self) -> None:
        self.__sink.reset()
        await self.update_filters()

    # Aliases

    seek = set_position
    set_filter = set_filters
    overwrite_filters = set_filters
    add_filters = add_filter
    remove_filters = remove_filter
    reset_filter = reset_filters
    set_vol = set_volume
    set_eq = set_equalizer
