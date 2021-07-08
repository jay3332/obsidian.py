import json
import aiohttp
import asyncio
import discord
import logging

from discord.ext import commands
from typing import Any, Dict, List, Optional, Union, overload

from .stats import Stats
from .player import Player
from .http import HTTPClient
from .websocket import Websocket
from .search import TrackSearcher
from .errors import NodeNotConnected

from .mixin import NodeListenerMixin
from .enums import OpCode, Source
from .track import Track, Playlist

from .spotify import SpotifyClient


Bot = Union[discord.Client, discord.AutoShardedClient, commands.Bot, commands.AutoShardedBot]

__all__: tuple = (
    'Node',
)

__log__: logging.Logger = logging.getLogger('obsidian.node')


class BaseNode(object):
    """Represents the base class for all nodes.

    You should use :class:`Node` instead.

    Parameters
    ----------
    bot: :class:`discord.Client`
        The client or bot that this node belongs to.
    host: str
        The IP of the host that Obsidian is running on.
    port: str
        The port of the host that Obsidian is running on.
    password: Optional[str]
        The password needed to connect to Obsidian.
    identifier: Optional[str]
        The name to use to refer to this node. Defaults to `'MAIN'`
    region: Optional[:class:`discord.VoiceRegion`]
        The voice region this node will be in.

    See Also
    --------
    :class:`Node`
    """

    @overload
    def __init__(
            self,
            bot: Bot,
            host: str = '127.0.0.1',
            port: Union[str, int] = '3030',
            password: Optional[str] = None,
            identifier: Optional[str] = None,
            region: Optional[discord.VoiceRegion] = None,
            *,
            session: Optional[aiohttp.ClientSession] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None,
            heartbeat: Optional[float] = None,
            secure: Optional[bool] = None,
            **kwargs
    ) -> None:
        ...

    @overload
    def __init__(
            self,
            bot: Bot,
            host: str = '127.0.0.1',
            port: Union[str, int] = '3030',
            password: Optional[str] = None,
            identifier: Optional[str] = None,
            region: Optional[discord.VoiceRegion] = None,
            *,
            session: Optional[aiohttp.ClientSession] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None,
            heartbeat: Optional[float] = None,
            secure: Optional[bool] = None,
            spotify: Optional[SpotifyClient] = None,
            **kwargs
    ) -> None:
        ...

    @overload
    def __init__(
            self,
            bot: Bot,
            host: str = '127.0.0.1',
            port: Union[str, int] = '3030',
            password: Optional[str] = None,
            identifier: Optional[str] = None,
            region: Optional[discord.VoiceRegion] = None,
            *,
            session: Optional[aiohttp.ClientSession] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None,
            heartbeat: Optional[float] = None,
            secure: Optional[bool] = None,
            spotify_client_id: Optional[str] = None,
            spotify_client_secret: Optional[str] = None,
            **kwargs
    ) -> None:
        ...

    def __init__(
            self,
            bot: Bot,
            host: str = '127.0.0.1',
            port: Union[str, int] = '3030',
            password: Optional[str] = None,
            identifier: Optional[str] = None,
            region: Optional[discord.VoiceRegion] = None,
            **kwargs
    ) -> None:
        self._bot: Bot = bot
        self._host: str = host
        self._port: str = str(port)
        self._password: str = password or ''
        self._identifier: str = identifier or 'MAIN'
        self._region: Optional[discord.VoiceRegion] = region
        self._players: Dict[int, Player] = {}
        self._search: TrackSearcher = TrackSearcher(self)

        self.__stats: Optional[Stats] = None
        self.__session: aiohttp.ClientSession = kwargs.get('session') or aiohttp.ClientSession()
        self.__loop: asyncio.AbstractEventLoop = kwargs.get('loop') or bot.loop
        self.__task: Optional[asyncio.Task] = None
        self.__ws: Optional[Websocket] = None

        self.__http: HTTPClient = HTTPClient(
            self.__session, self._host, self._port, self._password
        )

        spotify = kwargs.get('spotify')
        spotify_client_id = kwargs.get('spotify_client_id')
        spotify_client_secret = kwargs.get('spotify_client_secret')

        self._spotify: Optional[SpotifyClient] = None

        if spotify:
            self._spotify = spotify

        elif spotify_client_id and spotify_client_secret:
            self._spotify = SpotifyClient(
                spotify_client_id,
                spotify_client_secret,
                loop=self.__loop,
                session=self.__session
            )

        self.__internal__: Dict[str, Any] = kwargs
        self.__listeners__: Dict[str, List[callable]] = {}

    def __repr__(self) -> str:
        return f'<Node identifier={self._identifier!r}>'

    @property
    def bot(self) -> Bot:
        """:class:`discord.Client`: The :class:`discord.Client` that this node corresponds to."""
        return self._bot

    @property
    def host(self) -> str:
        """str: The IP of the host of Obsidian."""
        return self._host

    @property
    def port(self) -> str:
        """str: The port of the host of Obsidian."""
        return self._port

    @property
    def password(self) -> str:
        """str: The password needed to connect to Obsidian."""
        return self._password

    @property
    def identifier(self) -> str:
        """str: The identifier for this node, specified in the constructor."""
        return self._identifier

    @property
    def region(self) -> Optional[discord.VoiceRegion]:
        """:class:`discord.VoiceRegion`: The voice region for this node, specified in the constructor."""
        return self._region

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.__session

    @property
    def players(self) -> Dict[int, Player]:
        return self._players

    @property
    def spotify(self) -> Optional[SpotifyClient]:
        return self._spotify

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self.__loop

    @property
    def ws(self) -> Websocket:
        return self.__ws

    @property
    def http(self) -> HTTPClient:
        return self.__http

    @property
    def stats(self) -> Stats:
        """:class:`.Stats` The statistics for this node returned by the websocket."""
        return self.__stats

    @property
    def connected(self) -> bool:
        """bool: Whether or not this node is connected."""

        if not self.__ws:
            return False
        return self.__ws.connected

    def dispatch(self, event: str, *args, **kwargs) -> None:
        raise NotImplementedError

    def dispatch_event(self, player, event: str, *args, **kwargs) -> None:
        self.loop.create_task(
            discord.utils.maybe_coroutine(self.dispatch, player, event, *args, **kwargs)
        )

        for listener in self.__listeners__.get(event, []):
            self.loop.create_task(
                discord.utils.maybe_coroutine(listener, *args, **kwargs)
            )

    async def handle_ws_response(self, op: OpCode, data: dict) -> None:
        raise NotImplementedError

    async def connect(
            self,
            *,
            session: Optional[aiohttp.ClientSession] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        """Establishes a websocket connection for this node.

        Parameters
        ----------
        session: Optional[:class:`aiohttp.ClientSession`]
            The session to use when connecting.
        loop: Optional[:class:`asyncio.AbstractEventLoop`]
            The event loop to use when connecting.
        """

        await self.bot.wait_until_ready()

        connect_kwargs = {
            'heartbeat': self.__internal__.get('heartbeat'),
            'secure': self.__internal__.get('secure', False)
        }

        self.__ws = Websocket(self, session or self.__session, loop or self.__loop, **connect_kwargs)
        await self.ws.connect()

    async def disconnect(self, *, force: bool = False) -> None:
        """Disconnects the current websocket connection for this node.

        Parameters
        ----------
        force: bool, default: False
            Whether or not to force disconnection.
        """

        if self.connected:
            await self.ws.disconnect()

        for player in self._players.values():
            await player.disconnect(force=force)

        self.__ws = None

        if self.__task and not self.__task.done():
            self.__task.cancel()

        self.__task = None
        __log__.info(f'NODE {self.identifier!r} | Node disconnected.')

    async def destroy(self, *, force: bool = False) -> None:
        """Disconnects, deletes, and destroys this node.

        Parameters
        ----------
        force: bool, default: False
            Whether or not to force disconnection.
        """

        from .pool import NodePool

        await self.disconnect(force=force)
        del NodePool._nodes[self.identifier]

        __log__.info(f'NODE {self.identifier!r} | Node has been destroyed.')

    async def send(self, op: Union[OpCode, int], data: dict) -> None:
        """Sends a message to the Obsidian websocket.

        Parameters
        ----------
        op: Union[:class:`.OpCode`, int]
            The Op-Code of the request.
        data: Dict[str, Any]
            The JSON payload to send.
        """

        if not self.connected:
            raise NodeNotConnected(f'Node {self.identifier!r} is not connected.')

        if not isinstance(op, int):
            op = op.value

        payload = {'op': op, 'd': data}

        data = json.dumps(payload)
        if isinstance(data, bytes):
            data = data.decode('utf-8')

        await self.ws.send_str(data)

        __log__.debug(f'NODE {self.identifier!r} | Sent a {op} websocket payload: {payload}')

    def get_player(
            self,
            guild: Union[discord.Guild, discord.Object, int],
            cls: type = Player,
            must_exist: bool = False,
            *args,
            **kwargs
    ) -> Optional[Player]:
        """Gets an existing :class:`.Player`, or if not found, creates it.

        Parameters
        ----------
        guild: Union[:class:`discord.Guild`, :class:`discord.Object`, int]
            The guild that this player corresponds to.
        cls: type, default: :class:`.Player`
            The class to cast the player to.
        must_exist: bool, default: False
            Whether or not to return `None` if the player doesn't already exist.
        args
            Extra arguments to pass into the class constructor.
        kwargs
            Extra keyword arguments to pass into the class constructor.

        Returns
        -------
        :class:`.Player`
            The player found, or if it didn't exist, created.
        """

        if isinstance(guild, int):
            guild = discord.Object(guild)

        player = self._players.get(guild.id)
        if not player:
            if must_exist:
                return

            player = cls(self, self._bot, guild, *args, **kwargs)
            self._players[guild.id] = player
            return player

        if type(player) is not cls:
            player = cls(player.node, player.bot, player.guild, *args, **kwargs)

        return player

    def destroy_player(self, guild: Union[discord.Guild, discord.Object, int]) -> None:
        """Destroys and deletes a player.

        Parameters
        ----------
        guild: Union[:class:`discord.Guild`, :class:`discord.Object`, int]
            The player's corresponding guild.
        """

        if isinstance(guild, int):
            guild = discord.Object(guild)

        player = self._players.get(guild.id)
        if not player:
            return

        self.loop.create_task(player.destroy())

    async def decode_track(self, id: str, /, *, cls: type = Track, **kwargs) -> Optional[Track]:
        """|coro|

        Decodes a track given it's Base 64 ID.

        Parameters
        ----------
        id: str
            The track's ID, usually represented in Base 64.
        cls: type, default: :class:`Track`
            The class to cast the track to.
        kwargs
            Extra keyword arguments to pass into the class constructor.

        Returns
        -------
        Optional[:class:`Track`]
            The decoded track, if any.

        See Also
        --------
        :meth:`Node.decode_tracks`
        """

        return cls(id=id, info=await self.http.decode_track(id), **kwargs)

    async def decode_tracks(self, ids: str, /, *, cls: type = Track, **kwargs) -> Optional[List[Track]]:
        """|coro|

        Decodes multiple tracks, given their Base 64 ID's.

        Parameters
        ----------
        ids: List[str]
            A list of base 64 track ID's to decode.
        cls: type, default: :class:`Track`
            The class to cast the tracks to.
        kwargs
            Extra keyword arguments to pass into the class constructor.

        Returns
        -------
        Optional[List[:class:`Track`]]
            A list of constructed tracks, if any.

        See Also
        --------
        :meth:`Node.decode_track`
        """

        tracks = await self.http.decode_tracks(ids)
        return [cls(id=id_, info=track, **kwargs) for id_, track in zip(ids, tracks['tracks'])]

    @overload
    async def search_track(
            self,
            query: str,
            *,
            source: Optional[Source] = None,
            cls: type = Track,
            suppress: bool = False,
            **kwargs
    ) -> Optional[Union[Track, Playlist]]:
        ...

    async def search_track(self, *args, **kwargs):
        """Searches for one single track given a query or URL.

        .. warning::
            If the track is a direct URL, the `source` kwarg will be ignored.

        Parameters
        ----------
        query: str
            The search query or URL.
        source: Optional[:class:`.Source`]
            The source that the track should come from.
        cls: type, default: :class:`.Track`
            The class to cast the track to.
        suppress: bool, default: False
            Whether or not to suppress :exc:`.NoSearchMatchesFound`

        Returns
        -------
        Optional[Union[:class:`.Track`, :class:`.Playlist`]]
            The track or playlist that was found, if any.
        """

        return await self._search.search_track(*args, **kwargs)

    @overload
    async def search_tracks(
            self,
            query: str,
            *,
            source: Optional[Source] = None,
            cls: type = Track,
            suppress: bool = True,
            limit: Optional[int] = None,
            **kwargs
    ) -> Optional[Union[List[Track], Playlist]]:
        ...

    async def search_tracks(self, *args, **kwargs):
        """Searches for multiple tracks given a query or URL.

        .. warning::
            If the track is a direct URL, the `source` kwarg will be ignored.

        .. warning::
            If a playlist is found, the return type will not be a list, rather just the playlist itself.

        Parameters
        ----------
        query: str
            The search query or URL.
        source: Optional[:class:`.Source`]
            The source that the tracks should come from.
        cls: type, default: :class:`.Track`
            The class to cast the tracks to.
        suppress: bool, default: False
            Whether or not to suppress :exc:`.NoSearchMatchesFound`
        limit: Optional[int]
            The maximum amount of tracks to return.

        Returns
        -------
        Union[List[:class:`.Track`], :class:`.Playlist`]
            A list of tracks found, or a playlist.
        """

        return await self._search.search_tracks(*args, **kwargs)


class Node(BaseNode, NodeListenerMixin):
    """Represents a connection to Obsidian that manages requests and websockets.

    Parameters
    ----------
    bot: :class:`discord.Client`
        The client or bot that this node belongs to.
    host: str
        The IP of the host that Obsidian is running on.
    port: str
        The port of the host that Obsidian is running on.
    password: Optional[str]
        The password needed to connect to Obsidian.
    identifier: Optional[str]
        The name to use to refer to this node. Defaults to `'MAIN'`
    region: Optional[:class:`discord.VoiceRegion`]
        The voice region this node will be in.
    """

    @property
    def node(self):
        return self  # Relavant for NodeListenerMixin

    def dispatch(self, player, event: str, *args, **kwargs) -> None:
        # Temporary solution that made in a PR
        try:
            x = getattr(player, event)(player, event, *args, **kwargs)
            if x:
                return
        except AttributeError:
            pass
                
        #self.bot.dispatch(event, *args, **kwargs)

    async def handle_ws_response(self, op: OpCode, data: dict) -> None:
        if op is OpCode.STATS:
            self.__stats = Stats(data)
            return

        player = self.get_player(int(data['guild_id']), must_exist=True)
        if not player:
            return

        if op is OpCode.PLAYER_EVENT:
            player.dispatch_event(data)

        elif op is OpCode.PLAYER_UPDATE:
            player.update_state(data)
