import json
import typing
import logging
import discord
import aiohttp
import asyncio

from discord.ext import commands

from .stats import Stats
from .enums import OpCode
from .pool import NodePool
from .player import Player
from .websocket import Websocket
from .errors import NodeNotConnected


Bot = typing.Union[discord.Client, discord.AutoShardedClient, commands.Bot, commands.AutoShardedBot]

__all__ = [
    'Node'
]

__log__: logging.Logger = logging.getLogger('obsidian.player')


class BaseNode(object):
    def __init__(
            self,
            bot: Bot,
            host: str,
            port: typing.Union[str, int],
            password: typing.Optional[str] = None,
            identifier: typing.Optional[str] = None,
            region: typing.Optional[discord.VoiceRegion] = None,
            **kwargs
    ) -> None:
        self._bot: Bot = bot
        self._host: str = host
        self._port: str = str(port)
        self._password: str = password or ''
        self._identifier: str = identifier or 'MAIN'
        self._region: typing.Optional[discord.VoiceRegion] = region
        self._players: typing.Dict[int, Player] = {}

        self.__stats: typing.Optional[Stats] = None
        self.__session: aiohttp.ClientSession = kwargs.get('session') or aiohttp.ClientSession()
        self.__loop: asyncio.AbstractEventLoop = kwargs.get('loop') or bot.loop
        self.__task: typing.Optional[asyncio.Task] = None
        self.__ws: typing.Optional[Websocket] = None

    @property
    def bot(self) -> Bot:
        return self._bot

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> str:
        return self._port

    @property
    def password(self) -> str:
        return self._password

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def region(self) -> typing.Optional[discord.VoiceRegion]:
        return self._region

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.__session

    @property
    def players(self) -> typing.Dict[int, Player]:
        return self._players

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self.__loop

    @property
    def ws(self) -> Websocket:
        return self.__ws

    @property
    def stats(self) -> Stats:
        return self.__stats

    @property
    def connected(self) -> bool:
        if not self.__ws:
            return False
        return self.__ws.connected

    def dispatch(self, event: str, *args, **kwargs) -> None:
        raise NotImplementedError

    def dispatch_event(self, event: str, *args, **kwargs) -> None:
        self.loop.create_task(
            discord.utils.maybe_coroutine(self.dispatch, event, *args, **kwargs)
        )

    async def handle_ws_response(self, op: OpCode, data: dict) -> None:
        raise NotImplementedError

    async def connect(
            self,
            *,
            session: typing.Optional[aiohttp.ClientSession] = None,
            loop: typing.Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        self.__ws = Websocket(self, session or self.__session, loop or self.__loop)
        await self.ws.connect()

    async def disconnect(self, *, force: bool = False) -> None:
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
        await self.disconnect(force=force)
        del NodePool._nodes[self.identifier]

        __log__.info(f'NODE {self.identifier!r} | Node has been destroyed.')

    async def send(self, op: OpCode, data: dict) -> None:
        if not self.connected:
            raise NodeNotConnected(f'Node {self.identifier!r} is not connected.')

        payload = {'op': op.value, 'd': data}

        data = json.dumps(payload)
        if isinstance(data, bytes):
            data = data.decode('utf-8')

        await self.ws.send_str(data)

        __log__.debug(f'NODE {self.identifier!r} | Sent a {op} websocket payload: {payload}')

    def get_player(self, guild: typing.Union[discord.Guild, discord.Object, int], cls: type = Player, *args, **kwargs) -> Player:
        if isinstance(guild, int):
            guild = discord.Object(guild)

        player = self._players.get(guild.id)
        if not player:
            player = cls(self, self._bot, guild, *args, **kwargs)
            self._players[guild.id] = player
            return player

        if type(player) is not cls:
            player = cls(player.node, player.bot, player.guild, *args, **kwargs)

        return player

    def destroy_player(self, guild: typing.Union[discord.Guild, discord.Object, int]) -> None:
        if isinstance(guild, int):
            guild = discord.Object(guild)

        player = self._players.get(guild.id)
        if not player:
            return

        self.loop.create_task(player.destroy())


class Node(BaseNode):
    """
    Represents a websocket connection to Obsidian.
    """

    def dispatch(self, event: str, *args, **kwargs) -> None:
        self.bot.dispatch(event, *args, **kwargs)

    def handle_ws_response(self, op: OpCode, data: dict) -> None:
        if op is OpCode.STATS:
            self.__stats = Stats(data)
            return

        player = self.get_player(int(data['guild_id']))
        if not player:
            return

        if op is OpCode.PLAYER_EVENT:
            player.dispatch_event(data)
        elif op is OpCode.PLAYER_UPDATE:
            player.update_state(data)
