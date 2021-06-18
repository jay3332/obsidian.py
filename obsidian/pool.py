import typing
import discord

from discord.ext import commands

from .node import BaseNode, Node
from .errors import NodeAlreadyExists


__all__: list = [
    'NodePool'
]

Bot = typing.Union[discord.Client, discord.AutoShardedClient, commands.Bot, commands.AutoShardedBot]


class _NodePool:
    def __init__(self):
        self._nodes: typing.Dict[str, BaseNode] = {}

    @property
    def nodes(self) -> typing.Dict[str, BaseNode]:
        return self._nodes

    async def initiate_node(
            self,
            bot: Bot,
            host: str = '127.0.0.1',
            port: typing.Union[str, int] = '3030',
            password: typing.Optional[str] = None,
            identifier: typing.Optional[str] = None,
            region: typing.Optional[discord.VoiceRegion] = None,
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

    def get_node(self, identifier: typing.Optional[str] = None) -> BaseNode:
        return self._nodes.get(identifier)


NodePool: _NodePool = _NodePool()
