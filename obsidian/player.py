from __future__ import annotations

import time
import asyncio
import discord
import logging

from abc import ABC
from discord.ext import commands
from typing import Any, Dict, List, Optional, Union

from .filters import FilterSink, VolumeFilter, BaseFilter, Equalizer
from .track import Track, Playlist
from .events import get_cls

from .enums import OpCode, Source
from .queue import Queue, PointerBasedQueue, LoopType
from .mixin import NodeListenerMixin


Bot = Union[discord.Client, discord.AutoShardedClient, commands.Bot, commands.AutoShardedBot]

__all__: tuple = (
    'Player',
    'Protocol',
    'PresetPlayer'
)

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

    async def on_voice_server_update(self, data: Dict[str, Any]) -> None:
        __log__.debug(f'PLAYER | {self.guild.id} received VOICE_SERVER_UPDATE: {data}')

        self.player._voice_server_update_data = data
        await self.player.dispatch_voice_update()

    async def on_voice_state_update(self, data: Dict[str, Any]) -> None:
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
            timeout: Optional[float] = None,
            reconnect: Optional[bool] = None,
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


class Player(NodeListenerMixin):
    """Represents a guild's music player.

    This class is recommended to be subclassed for custom behaviors.
    This class also inherits from :class:`.NodeListenerMixin`.

    Parameters
    ----------
    node: :class:`.BaseNode`
        The node constructing this player.
    bot: :class:`discord.Client`
        The bot of the corresponding node.
    guild: Union[:class:`discord.Guild`, :class:`discord.Object`]
        The guild that this player corresponds to.
    """

    def __init__(self, node, bot: Bot, guild: Union[discord.Guild, discord.Object]) -> None:
        from .node import BaseNode

        self._bot: Bot = bot
        self._node: BaseNode = node
        self._guild: Union[discord.Guild, discord.Object] = guild
        self._channel: Optional[discord.VoiceChannel] = None

        self._voice_server_update_data: Optional[Dict[str, Any]] = None
        self._session_id: Optional[str] = None

        self._last_update: float = 0

        self._frames_sent: Optional[int] = None
        self._frames_lost: Optional[int] = None
        self._frame_data_usable: bool = True

        self._last_position: Optional[float] = None
        self._current_track_id: Optional[str] = None
        self._position: float = 0
        self._paused: bool = False

        self.__protocol: Protocol = None
        self.__sink: FilterSink = FilterSink(self)

        self._current: Optional[Track] = None

        if not isinstance(self._guild, discord.Guild):
            new = self._bot.get_guild(self._guild.id)
            if new:
                self._guild = new

    def __repr__(self) -> str:
        return f'<Player node={self._node.identifier!r} connected={self.connected}>'

    @property
    def bot(self) -> Bot:
        """:class:`discord.Client` The bot that this player uses."""
        return self._bot

    @property
    def guild(self) -> Union[discord.Guild, discord.Object]:
        """Union[:class:`discord.Guild`, :class:`discord.Object`]: The guild that corresponds to this player."""
        return self._guild

    @property
    def guild_id(self) -> int:
        """int: The ID of the guild that corresponds to this player."""
        return self._guild.id

    @property
    def channel(self) -> discord.VoiceChannel:
        """:class:`discord.VoiceChannel`: The voice channel that this player is connected to."""
        return self._channel

    @property
    def node(self):
        """:class:`.Node`: The node that this player uses."""
        return self._node

    @property
    def current(self) -> Track:
        """:class:`.Track`: The current track this player is playing."""
        return self._current

    @property
    def connected(self) -> bool:
        """bool: Whether or not this player is connected."""
        return self._channel is not None

    @property
    def playing(self) -> bool:
        """
        Whether or not this player is playing music.
        """
        return self.connected and self._current is not None

    @property
    def paused(self) -> bool:
        """bool: Whether or not this player is paused."""
        return self._paused

    @property
    def current_track_id(self) -> Optional[str]:
        """Optional[str]: The raw base 64 ID of the current track playing."""
        return self._current_track_id

    @property
    def voice_client(self) -> Protocol:
        """:class:`.Protocol`: The :class:`.Protocol` this player is currently using."""
        return self.__protocol

    @property
    def filters(self) -> FilterSink:
        """:class:`.FilterSink`: The :class:`.FilterSink` of filters this player is using."""
        return self.__sink

    @filters.setter
    def filters(self, sink: FilterSink) -> None:
        if not isinstance(sink, FilterSink):
            raise TypeError('Filter sinks must inherit from FilterSink.')

        self.__sink = sink

    @property
    def volume(self) -> int:
        """int: The current volume of the music playing."""
        return self.__sink.volume.percent if self.__sink.volume else 100

    @property
    def equalizer(self) -> Optional[Equalizer]:
        """Optional[:class:`.Equalizer`]: The current equalizer of the music audio."""
        return self.__sink.equalizer

    eq = equalizer

    @property
    def listeners(self) -> List[discord.Member]:
        """List[:class:`discord.Member`]: Returns a list of :class:`discord.Member` in the voice channel that are undeafened."""
        if not self._channel:
            return []

        def predicate(member: discord.Member) -> bool:
            return not member.bot and not member.voice.deaf or not member.voice.self_deaf

        return [member for member in self._channel.members if predicate(member)]

    @property
    def position(self) -> float:
        """float: The position, in milliseconds, of the current track playing.

        For example, this can return `62000` if the track is 62 seconds in.
        """
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

    def update_state(self, data: Dict[str, Any]) -> None:
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

    def dispatch_event(self, data: Dict[str, Any]) -> None:
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
            timeout: Optional[float] = None,
            reconnect: Optional[bool] = None,
            self_deaf: bool = False
    ) -> Protocol:
        """Connects to a :class:`discord.VoiceChannel`.

        Parameters
        ----------
        channel: :class:`discord.VoiceChannel`
            The channel to connect to.
        cls: type, default: :class:`.Protocol`
            The connection protocol class to use.
        timeout: float, optional
            The timeout to use when connecting.
        reconnect: bool, optional
            Whether or not to reconnect.
        self_deaf: bool, default: False
            Whether or not to self-deafen upon connecting.

        Returns
        -------
        :class:`.Protocol`
            The connection protocol created.
        """

        if not issubclass(cls, Protocol):
            raise TypeError('Connection class must inherit from Protocol')

        self._channel = channel
        if not self.__protocol:
            self.__protocol = cls(self)

        await self.__protocol.connect(timeout=timeout, reconnect=reconnect, self_deaf=self_deaf)
        return self.__protocol

    async def disconnect(self, *, force: bool = False) -> None:
        """Disconnects from the current voice connection.

        Parameters
        ----------
        force: bool, default: False
            Whether or not to force disconnection.
        """

        if not self.__protocol or not self.connected:
            raise ValueError('No connection to disconnect from.')

        await self.__protocol.disconnect(force=force)

    async def destroy(self, *, force: bool = False) -> None:
        """Destroys, disconnects, and deletes this player.

        Parameters
        ----------
        force: bool, default: False
            Whether or not to force disconnection.
        """

        await self.disconnect(force=force)
        del self.node._players[self.guild_id]

        __log__.info(f'PLAYER | {self.guild_id} has been destroyed.')

    async def move(self, channel: discord.VoiceChannel) -> None:
        """Moves the connection to another voice channel.

        Parameters
        ----------
        channel: :class:`discord.VoiceChannel`
            The channel to move to.
        """

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
            track: Union[Track, Playlist],
            *,
            start_time: int = 0,
            end_time: int = 0,
            no_replace: bool = False
    ) -> None:
        """Plays a track using this player.

        If you provide a playlist, the player will play the `Playlist.selected_track`.

        Parameters
        ----------
        track: :class:`.Track`
            The track to play.
        start_time: int, default: 0
            The start time offset of the track, in milliseconds.
        end_time: int, default: 0
            When to end the track, in milliseconds.
        no_replace: bool, default: False
            If set to True, this will do nothing if a track is already playing.
            If set to False, this will overwrite the current playing track.
        """

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
        """Stops the current playing track.

        Parameters
        ----------
        force: bool, default: False
            Whether or not to force stop the track.
        """

        if not self._current and not force:
            return

        await self._node.send(OpCode.STOP_TRACK, {'guild_id': str(self.guild_id)})
        __log__.info(f'PLAYER | {self.guild_id} stopped the current track.')

        self._current = None

    async def set_pause(self, pause: Optional[bool] = None) -> bool:
        """Sets the paused state for the current track.

        Parameters
        ----------
        pause: bool, optional
            The new paused state.
            If this is left as None, the new paused state will be the opposite of the current.

        Returns
        -------
        bool
            The new paused state (for confirmation).
        """

        pause = pause if pause is not None else not self._paused

        await self._node.send(OpCode.PLAYER_PAUSE, {'guild_id': str(self._guild.id), 'state': pause})
        __log__.info(f'PLAYER | {self._guild.id} set its paused state to {pause}.')

        self._paused = res = pause
        return res

    async def set_position(self, position: float) -> None:
        """Sets the current time position, in milliseconds, of the current playing track.

        Parameters
        ----------
        position: float
            The new time position, in milliseconds.
        """

        if not self._current or 0 > position > self._current.length:
            return

        await self._node.send(OpCode.PLAYER_SEEK, {'guild_id': str(self._guild.id), 'position': round(position)})
        __log__.info(f'PLAYER | {self.guild.id} set position to {position}')

        self._position = position
        self._last_update = time.time() * 1000

    async def set_volume(self, volume: int = 100) -> None:
        """Sets the player volume in percent.

        The volume must be at least 0 and at most 500.

        .. warning::
            It is recommended not to allow users to set the volume past 200
            as it is then virtually earrape.

        Parameters
        ----------
        volume: int, default: 100
            The new volume of the player.
        """

        if self.__sink.volume:
            self.__sink.volume.percent = volume

        self.__sink.add(VolumeFilter(volume / 100))
        await self.update_filters()

    async def set_equalizer(self, equalizer: Equalizer) -> None:
        """Overwrites and changes the current audio equalizer.

        Parameters
        ----------
        equalizer: :class:`.Equalizer`
            The new equalizer to use.
        """

        self.__sink.add(equalizer)
        await self.update_filters()

    async def update_filters(self) -> None:
        await self._node.send(OpCode.PLAYER_FILTERS, self.__sink.to_json(self.guild_id))
        __log__.info(f'PLAYER | {self.guild.id} updated filters')

    async def set_filters(self, filters: FilterSink) -> None:
        """Completely overwrites the current filter sink into a new one.

        Parameters
        ----------
        filters: :class:`.FilterSink`
            The new filter sink to use.

        See Also
        --------
        :meth:`Player.add_filter`:
            Appends a new filter to the current filter sink.
        """

        self.filters = filters
        await self.update_filters()

    async def add_filter(self, *filters: BaseFilter) -> None:
        """Appends a new filter, or filters, to the current filter sink.

        Parameters
        ----------
        filters: :class:`.BaseFilter`
            The filter(s) to add.
        """

        for filter_ in filters:
            self.__sink.add(filter_)

        await self.update_filters()

    async def remove_filter(self, *filters) -> None:
        """Removes a filter from the current filter sink.

        Parameters
        ----------
        filters: :class:`.BaseFilter`
            The filter(s) to remove.
        """

        for filter_ in filters:
            self.__sink.remove(filter_)

        await self.update_filters()

    async def reset_filters(self) -> None:
        """
        Resets the current filter sink.
        """
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


class PresetPlayer(Player):
    """Basic music player with many things already built and handled for you.

    Note that this class should still be inherited from in order to add required methods.
    """

    def __init__(
            self,
            node,
            bot: Bot,
            guild: Union[discord.Guild, discord.Object],
            *,
            queue_cls: type = PointerBasedQueue,
            track_cls: type = Track,
            wait_timeout: float = 180,
            **kwargs
    ) -> None:
        super().__init__(node, bot, guild)
        self._queue: PointerBasedQueue = queue_cls()

        self.ctx: Optional[commands.Context] = None
        self._dj: Optional[discord.Member] = None

        maybe_ctx = kwargs.pop('ctx', None)
        if maybe_ctx:
            self.ctx = maybe_ctx
            self._dj = self.ctx.author

        self.__wait_timeout: float = 180
        self.__destroy_task: Optional[asyncio.Task] = None

    async def on_obsidian_track_end(self, _player, _event) -> Any:
        await self.do_next()

    on_obsidian_track_stuck = on_obsidian_track_end

    @property
    def dj(self) -> discord.Member:
        """:class:`discord.Member`: The current DJ of this player."""
        return self._dj

    @dj.setter
    def dj(self, new: discord.Member) -> None:
        self._dj = new

    @property
    def queue(self) -> Queue:
        """:class:`.PointerBasedQueue`: The current queue for this player."""
        return self._queue

    @property
    def now_playing(self) -> Track:
        """:class:`.Track`: The current track that is playing."""
        return self._queue.current

    @property
    def index(self) -> int:
        """int: The pointer index of the queue."""
        return self._queue.index

    current = now_playing

    def enqueue(self, track: Union[Track, Playlist]) -> None:
        """Enqueues a :class:`.Track` or an entire :class:`.Playlist`.

        Parameters
        ----------
        track: Union[:class:`.Track`, :class:`.Playlist`]
            The track or playlist to enqueue.
        """

        self._kill_destroy_task()
        self._queue.add(track)

    async def wait_then_destroy(self) -> None:
        await asyncio.sleep(self.__wait_timeout)
        await self.destroy()

    def set_loop_type(self, new: LoopType) -> None:
        """Changes the :class:`.LoopType` of the queue.

        Parameters
        ----------
        new: :class:`.LoopType`
            The new loop type to use.
        """

        self._queue.set_loop_type(new)

    def _kill_destroy_task(self) -> None:
        if self.__destroy_task is not None:
            self.__destroy_task.cancel()
            self.__destroy_task = None

    async def __play(self, track: Track) -> Optional[Track]:
        if not track:
            self.__destroy_task = self.bot.loop.create_task(self.wait_then_destroy())

        self._kill_destroy_task()
        await self.play(track)
        return track

    async def do_next(self) -> Optional[Track]:
        """Plays the track fetched from :meth:`PointerBasedQueue.get`.

        Returns
        -------
        Optional[:class:`.Track`]
            The track that will be played, if any.
        """

        return await self.__play(self._queue.get())

    async def skip(self) -> Optional[Track]:
        """Skips the current track regardless of the loop type.

        This uses :meth:`PointerBasedQueue.skip`.

        Returns
        -------
        Optional[:class:`.Track`]
            The new track to be played, if any.
        """

        return await self.__play(self._queue.skip())

    async def build_embed(self, embed: discord.Embed) -> None:
        raise NotImplementedError

    async def send_now_playing(self):
        raise NotImplementedError
