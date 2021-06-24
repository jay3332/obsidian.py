import discord
import aiohttp
import asyncio

from discord.ext import commands
from typing import Dict, Optional, Union, overload

from .node import BaseNode, Node
from .errors import NodeAlreadyExists

from .spotify import SpotifyClient


__all__: tuple = (
    'NodePool'
)

Bot = Union[discord.Client, discord.AutoShardedClient, commands.Bot, commands.AutoShardedBot]


class _NodePool:
    def __init__(self):
        self._nodes: Dict[str, BaseNode] = {}

    def __repr__(self) -> str:
        return f'NodePool [ {", ".join(map(repr, self._nodes))} ]'

    @property
    def nodes(self) -> Dict[str, BaseNode]:
        return self._nodes

    @overload
    async def initiate_node(
            self,
            bot: Bot,
            host: str = '127.0.0.1',
            port: Union[str, int] = '3030',
            password: Optional[str] = None,
            identifier: Optional[str] = None,
            region: Optional[discord.VoiceRegion] = None,
            *,
            cls: type = Node,
            session: Optional[aiohttp.ClientSession] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None,
            heartbeat: Optional[float] = None,
            secure: Optional[bool] = None,
            **kwargs
    ) -> BaseNode:
        ...

    @overload
    async def initiate_node(
            self,
            bot: Bot,
            host: str = '127.0.0.1',
            port: Union[str, int] = '3030',
            password: Optional[str] = None,
            identifier: Optional[str] = None,
            region: Optional[discord.VoiceRegion] = None,
            *,
            cls: type = Node,
            session: Optional[aiohttp.ClientSession] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None,
            heartbeat: Optional[float] = None,
            secure: Optional[bool] = None,
            spotify: Optional[SpotifyClient] = None,
            **kwargs
    ) -> BaseNode:
        ...

    @overload
    async def initiate_node(
            self,
            bot: Bot,
            host: str = '127.0.0.1',
            port: Union[str, int] = '3030',
            password: Optional[str] = None,
            identifier: Optional[str] = None,
            region: Optional[discord.VoiceRegion] = None,
            *,
            cls: type = Node,
            session: Optional[aiohttp.ClientSession] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None,
            heartbeat: Optional[float] = None,
            secure: Optional[bool] = None,
            spotify_client_id: Optional[str] = None,
            spotify_client_secret: Optional[str] = None,
            **kwargs
    ) -> BaseNode:
        ...

    async def initiate_node(
            self,
            bot: Bot,
            host: str = '127.0.0.1',
            port: Union[str, int] = '3030',
            password: Optional[str] = None,
            identifier: Optional[str] = None,
            region: Optional[discord.VoiceRegion] = None,
            *,
            cls: type = Node,
            **kwargs
    ) -> BaseNode:
        if not issubclass(cls, BaseNode):
            raise TypeError('Node classes must inherit from BaseNode.')

        if identifier in self._nodes:
            raise NodeAlreadyExists(identifier)

        node = cls(bot, host, port, password, identifier, region, **kwargs)
        await node.connect()

        self._nodes[node.identifier] = node
        return node

    def get_node(self, identifier: Optional[str] = None) -> BaseNode:
        return self._nodes.get(identifier)


NodePool = _NodePool()
