import aiohttp
import asyncio
import logging

from base64 import b64encode
from discord.backoff import ExponentialBackoff
from typing import Any, Dict, Optional

from .errors import (
    SpotifyHTTPError,
    SpotifyAuthorizationFailure
)


__all__: list = [
    'SpotifyClient'
]

__log__: logging.Logger = logging.getLogger('obsidian.spotify')


class SpotifyClient:
    BASE_URL = 'https://api.spotify.com/v1/'

    def __init__(
            self,
            client_id: str,
            client_secret: str,
            *,
            session: Optional[aiohttp.ClientSession] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        from . import __version__

        self.__loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self.__session: aiohttp.ClientSession = session or aiohttp.ClientSession()

        self._client_id = client_id
        self._client_secret = client_secret
        self._user_agent = f'Application (https://github.com/jay3332/obsidian.py {__version__})'

    @property
    def _token(self) -> None:
        key = self._client_id + ':' + self._client_secret
        return b64encode(key.encode()).decode()

    async def _retrieve_token(self) -> None:
        data = {"grant_type": "client_credentials"}
        headers = {"Authorization": f"Basic {self._token}"}

        async with self.__session.post(
            "https://accounts.spotify.com/api/token", data=data, headers=headers
        ) as response:
            info = await response.json(encoding="utf-8")

            if 'error' in info:
                __log__.error('HTTP(SPOTIFY) | Authentication failed.')
                raise SpotifyAuthorizationFailure('Failed to authorize to spotify.', response)

            try:
                return info['access_token']
            except KeyError:
                pass

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
        token = await self._retrieve_token()

        url = self.BASE_URL + route.lstrip('/')
        _headers = {
            'Authorization': 'Bearer ' + token,
            'User-Agent': self._user_agent
        }

        if headers:
            _headers.update(headers)

        if isinstance(payload, dict):
            _headers['Content-Type'] = 'application/json'

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
                    return await response.json(encoding='utf-8')

                if response.status == 401:
                    token = await self._retrieve_token()
                    headers["Authorization"] = "Bearer " + token
                    continue

                if response.status == 429:
                    # Basic ratelimit handling
                    amount = int(response.headers.get("Retry-After"))
                    __log__.warning(f'HTTP(SPOTIFY) | Ratelimited, retrying in {amount} seconds...')

                    await asyncio.sleep(amount)
                    continue

                delay = backoff.delay()
                __log__.warning(f'HTTP(SPOTIFY) | {response.status} status code while requesting from {response.url!r}, retrying in {delay:.2f} seconds')

                await asyncio.sleep(delay)

        message = f'HTTP(SPOTIFY) | {response.status} status code while requesting from {response.url!r}, retry limit exhausted'

        __log__.error(message)
        raise SpotifyHTTPError(message, response)
