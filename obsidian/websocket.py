import typing
import asyncio
import aiohttp
import logging

from discord.backoff import ExponentialBackoff

from .enums import OpCode
from .errors import ObsidianConnectionFailure, ObsidianAuthorizationFailure


__all__: list = [
    'Websocket'
]

__log__: logging.Logger = logging.getLogger('obsidian.node')


class Websocket:
    def __init__(
            self,
            node,
            session: aiohttp.ClientSession,
            loop: asyncio.AbstractEventLoop,
            *,
            secure: bool = False,
            **connect_kwargs
    ) -> None:
        from .node import BaseNode

        self._password: str = node.password
        self._bot_user_id: str = str(node.bot.user.id)
        self._session: aiohttp.ClientSession = session
        self._loop: asyncio.AbstractEventLoop = loop

        self.__node: BaseNode = node
        self.__secure: bool = secure
        self.__ws: typing.Optional[aiohttp.ClientWebSocketResponse] = None

        self.__internal__ = connect_kwargs

    @property
    def url(self) -> str:
        ws = 'wss' if self.__secure else 'ws'
        return f'{ws}://{self.__node.host}:{self.__node.port}/magma'

    @property
    def headers(self) -> typing.Dict[str, any]:
        return {
            'Authorization': self._password,
            'User-Id': self._bot_user_id,
            'Client-Name': 'Obsidian'
        }

    @property
    def connected(self) -> bool:
        return self.__ws is not None and not self.__ws.closed

    @property
    def _ws(self) -> aiohttp.ClientWebSocketResponse:
        return self.__ws

    async def connect(self) -> aiohttp.ClientWebSocketResponse:
        identifier = self.__node.identifier

        try:
            ws = await self._session.ws_connect(self.url, headers=self.headers, **self.__internal__)
        except aiohttp.WSServerHandshakeError as exc:
            if exc.status == 4001:
                __log__.error(f'NODE {identifier!r} | Failed to authorize')
                raise ObsidianAuthorizationFailure(self.__node)

            raise Exception(exc)
        except Exception as exc:
            __log__.fatal(f'NODE {identifier!r} | Failed to connect')
            raise ObsidianConnectionFailure(self.__node, exc)
        else:
            self.__node.__task = self._loop.create_task(self.listen())
            self.__node.dispatch_event('obsidian_node_ready', self.__node)

            self.__ws = ws
            __log__.info(f'NODE {identifier!r} | Connection successful')

            return ws

    async def disconnect(self) -> None:
        await self.__ws.close()

    async def listen(self) -> None:
        backoff = ExponentialBackoff(base=7)

        while True:
            payload = await self.__ws.receive()

            if payload.type is aiohttp.WSMsgType.CLOSED:
                retry = backoff.delay()
                __log__.warning(f'NODE {self.__node.identifier!r} | Websocket is closed, attempting reconnection in {retry:.2f} seconds.')

                await asyncio.sleep(retry)

                if not self.connected:
                    self._loop.create_task(self.connect())
            else:
                data = payload.json()

                try:
                    op = OpCode(data['op'])
                except ValueError:
                    __log__.warning(f'NODE {self.__node.identifier!r} | Received payload with invalid operation code: {data}')
                    continue
                else:
                    __log__.debug(f'NODE {self.__node.identifier!r} | Received payload with op-code {op!r}: {data}')
                    self._loop.create_task(self.__node.handle_ws_response(op, data['d']))

    def send_str(self, data: str, compress: typing.Optional[int] = None) -> typing.Coroutine[None, None, None]:
        return self.__ws.send_str(data, compress)
