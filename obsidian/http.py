import logging
import asyncio

from aiohttp import ClientSession
from discord.backoff import ExponentialBackoff
from typing import Any, Coroutine, Dict, List, Optional

from .errors import HTTPError


__all__: tuple = (
    'HTTPClient'
)

__log__: logging.Logger = logging.getLogger('obsidian.node')


class HTTPClient:
    def __init__(self, session: ClientSession, host: str, port: str, password: str) -> None:
        self.__session: ClientSession = session
        self.__host: str = host
        self.__port: str = port
        self.__password: str = password

    @property
    def url(self) -> str:
        return f'http://{self.__host}:{self.__port}/'

    async def request(
            self,
            method: str,
            route: str,
            parameters: Optional[Dict[str, Any]] = None,
            payload: Optional[Dict[str, Any]] = None,
            *,
            max_retries: int = 3,
            backoff: Optional[ExponentialBackoff] = None,
            headers: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if max_retries < 1:
            raise ValueError('Max retries must be at least 1.')

        backoff = backoff or ExponentialBackoff()

        url = self.url + route.lstrip('/')
        _headers = {'Authorization': self.__password}

        if headers:
            _headers.update(headers)

        kwargs = {
            'method': method,
            'url': url,
            'headers': headers
        }

        if parameters is not None:
            kwargs['params'] = parameters

        if payload is not None:
            kwargs['json'] = payload

        for _ in range(max_retries):
            async with self.__session.request(**kwargs) as response:
                if 200 <= response.status < 300:
                    return await response.json()

                delay = backoff.delay()
                __log__.warning(f'HTTP | {response.status} status code while requesting from {response.url!r}, retrying in {delay:.2f} seconds')

                await asyncio.sleep(delay)

        message = f'HTTP | {response.status} status code while requesting from {response.url!r}, retry limit exhausted'

        __log__.error(message)
        raise HTTPError(message, response)

    def load_tracks(self, identifier: str) -> Coroutine[Any, Any, Dict[str, Any]]:
        return self.request('GET', '/loadtracks', parameters={
            'identifier': identifier
        })

    def decode_track(self, track: str) -> Coroutine[Any, Any, Dict[str, Any]]:
        return self.request('GET', '/decodetrack', parameters={
            'track': track
        })

    def decode_tracks(self, tracks: List[str]) -> Coroutine[Any, Any, Dict[str, Any]]:
        return self.request('POST', '/decodetracks', parameters={
            'tracks': tracks
        })
