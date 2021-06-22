import re
import aiohttp
import asyncio
import logging

from base64 import b64encode
from discord.backoff import ExponentialBackoff
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

from .track import Track, Playlist

from .errors import (
    SpotifyHTTPError,
    SpotifyAuthorizationFailure,
    NoSearchMatchesFound
)


__all__: list = [
    'SpotifyHTTPClient',
    'SpotifyClient'
]

__log__: logging.Logger = logging.getLogger('obsidian.spotify')


class SpotifyHTTPClient:
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

        self._client_id: str = client_id
        self._client_secret: str = client_secret
        self._user_agent: str = f'Application (https://github.com/jay3332/obsidian.py {__version__})'

        self.__access_token: Optional[str] = None

    def __repr__(self) -> str:
        return f'<SpotifyHTTPClient client_id={self._client_id!r}>'

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self.__loop

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.__session

    @property
    def _token(self) -> None:
        key = self._client_id + ':' + self._client_secret
        return b64encode(key.encode()).decode()

    async def _retrieve_token(self, *, generate_new: bool = False) -> None:
        if self.__access_token is not None and not generate_new:
            return self.__access_token

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
                result = info['access_token']
                self.__access_token = result
                return result
            except KeyError:
                pass

    async def request(
            self,
            method: str,
            route: str,
            parameters: Optional[Dict[str, Any]] = None,
            payload: Optional[Dict[str, Any]] = None,
            *,
            max_retries: int = 5,
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
                    token = await self._retrieve_token(generate_new=True)
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

    async def get_album_tracks(
            self,
            album_id: str,
            *,
            limit: int = 50,
            offset: int = 0,
            market: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {'limit': limit, 'offset': offset}

        if market is not None:
            payload['market'] = market

        return await self.request('GET', f"/albums/{album_id}/tracks", parameters=payload)

    async def get_all_album_tracks(
            self,
            album_id: str,
            *,
            market: Optional[str] = None
    ) -> Dict[str, Any]:
        """Helper function to retrieve all album tracks past the limit of 50.

        Parameters
        ----------
        album_id : str
            The ID of the album to use.
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code.

        Returns
        -------
        Dict[str, Any]
            The raw JSON response from Spotify.
        """

        payload = {}

        if market is not None:
            payload['market'] = market

        offset = 0
        tracks = []

        limit = None
        first_encounter = None

        while limit is None or len(tracks) < limit:
            kwargs = {**payload, 'offset': offset}

            response = await self.get_album_tracks(album_id, **kwargs)
            if limit is None:
                try:
                    limit = response['total']
                except KeyError:
                    break

            try:
                tracks += response['items']
            except KeyError:
                pass

            if first_encounter is None:
                response.pop('items', None)
                first_encounter = response

            offset += 50

        return {**first_encounter, 'items': tracks}

    async def get_playlist_tracks(
            self,
            playlist_id: str,
            *,
            limit: int = 100,
            offset: int = 0,
            market: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {'limit': limit, 'offset': offset}

        if market is not None:
            payload['market'] = market

        return await self.request('GET', f"/playlists/{playlist_id}/tracks", parameters=payload)

    async def get_all_playlist_tracks(
            self,
            playlist_id: str,
            *,
            market: Optional[str] = None
    ) -> Dict[str, Any]:
        """Helper function to retrieve all playlist tracks past the limit of 100.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist to use.
        market : Optional[str]
            An ISO 3166-1 alpha-2 country code.

        Returns
        -------
        Dict[str, Any]
            The raw JSON response from Spotify.
        """

        payload = {}

        if market is not None:
            payload['market'] = market

        offset = 0
        tracks = []

        limit = None
        first_encounter = None

        while limit is None or len(tracks) < limit:
            kwargs = {**payload, 'offset': offset}

            response = await self.get_playlist_tracks(playlist_id, **kwargs)
            if limit is None:
                try:
                    limit = response['total']
                except KeyError:
                    break

            try:
                tracks += response['items']
            except KeyError:
                pass

            if first_encounter is None:
                response.pop('items', None)
                first_encounter = response

            offset += 100

        return {**first_encounter, 'items': tracks}

    async def get_artist_top_tracks(
            self,
            artist_id: str,
            *,
            market: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        payload = {'market': market or 'US'}
        return await self.request('GET', f"/artists/{artist_id}/top-tracks", parameters=payload)

    async def get_track(
            self,
            track_id: str,
            *,
            market: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {}

        if market is not None:
            payload['market'] = market

        return await self.request('GET', f"/tracks/{track_id}", parameters=payload)

    async def search(
            self,
            query: str,
            *,
            market: str = 'US',
            limit: int = 20,
            offset: int = 0
    ) -> List[Dict[str, Any]]:
        payload = {
            "q": quote(query),
            "type": 'track',
            "limit": limit,
            "offset": offset
        }

        if market is not None:
            payload['market'] = market

        response = await self.request('GET', '/search', parameters=payload)

        try:
            return response['tracks']['items']
        except KeyError:
            return []


class SpotifyClient:
    """
    Class that interacts with Spotify.
    """

    URI_REGEX: re.Pattern = re.compile(
        r'<?http(s)?://open.spotify.com/(?P<type>album|playlist|track|artist)/(?P<id>[a-zA-Z0-9]+).*/?>?'
    )

    def __init__(
            self,
            client_id: str,
            client_secret: str,
            *,
            session: Optional[aiohttp.ClientSession] = None,
            loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        self.__http = http = SpotifyHTTPClient(
            client_id,
            client_secret,
            session=session,
            loop=loop
        )

        self._loop: asyncio.AbstractEventLoop = http.loop
        self._session: aiohttp.ClientSession = http.session

        self._client_id: str = client_id
        self._client_secret: str = client_secret

    def __repr__(self) -> None:
        return f'<SpotifyClient client_id={self._client_id!r}>'

    @property
    def http(self) -> SpotifyHTTPClient:
        return self.__http

    def sanitize_playlist_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'name': info.get('name', 'Unknown'),
            'selected_track': 0,
            'uri': info.get("external_urls", {}).get("spotify", ''),
        }

    def sanitize_track(self, track: Dict[str, Any]) -> Dict[str, Any]:
        author = ', '.join(
            artist['name'] for artist in track.get('artists', [])
        ).strip()

        if not author:
            author = 'Unknown author'

        thumbnail = ''
        _images = track.get('images')

        if _images:
            thumbnail = _images[0].get('url', '')
        elif 'album' in track:
            _images = track['album'].get('images')

            if _images:
                thumbnail = _images[0].get('url', '')

        return {
            'title': track.get('name', 'Unknown'),
            'author': author,
            'uri': track.get("external_urls", {}).get("spotify", ''),
            'identifier': track.get('id', 'Unknown'),
            'length': track.get('duration_ms', 0),
            'position': 0,
            'is_stream': False,
            'is_seekable': False,
            'source_name': 'spotify',
            'thumbnail': thumbnail
        }

    async def _search_track(
            self,
            query: str,
            *,
            market: Optional[str] = None,
            suppress: bool = True,
            cls: type = Track,
            **kwargs
    ) -> Optional[Track]:
        response = await self.http.search(query, limit=1, market=market or 'US')
        try:
            track = self.sanitize_track(response[0])
        except IndexError:
            if not suppress:
                raise NoSearchMatchesFound(query)
            return
        return cls(id='', info=track, **kwargs)

    async def _search_tracks(
            self,
            query: str,
            *,
            limit: int = 20,
            market: Optional[str] = None,
            suppress: bool = True,
            cls: type = Track,
            **kwargs
    ) -> List[Track]:
        response = await self.http.search(query, limit=limit, market=market or 'US')

        if not response:
            if not suppress:
                raise NoSearchMatchesFound(query)
            return []

        return [
            cls(
                id='',
                info=self.sanitize_track(track),
                **kwargs
            )
            for track in response
        ]

    async def get_track_via_url(
            self,
            match: re.Match,
            *,
            market: str = None,
            cls: type = Track,
            **kwargs
    ) -> Union[Track, Playlist]:
        response = None
        if match is None:
            return

        search_type = match.group('type')
        spotify_id = match.group('id')

        if search_type == 'album':
            response = await self.http.get_all_album_tracks(
                spotify_id,
                market=market
            )
        elif search_type == 'playlist':
            response = await self.http.get_all_playlist_tracks(
                spotify_id,
                market=market
            )
        elif search_type == 'artist':
            pass  # Not implemented
        elif search_type == 'track':
            response = await self.http.get_track(
                spotify_id,
                market=market
            )
            track = self.sanitize_track(response)
            return cls(id='', info=track, **kwargs)

        if search_type != 'track':
            tracks = [
                self.sanitize_track(track)
                for track in response['items']
            ]

            return Playlist(
                info=self.sanitize_playlist_info(response),
                tracks=tracks,
                cls=cls,
                **kwargs
            )

    async def get_track(
            self,
            query: str,
            *,
            market: str = None,
            suppress: bool = True,
            cls: type = Track,
            **kwargs
    ) -> Union[Track, Playlist]:
        match = self.URI_REGEX.match(query)
        if match:
            return await self.get_track_via_url(match, market=market, cls=cls, **kwargs)

        return await self._search_track(query, market=market, suppress=suppress, cls=cls, **kwargs)

    async def get_tracks(
            self,
            query: str,
            *,
            market: str = None,
            suppress: bool = True,
            limit: int = 20,
            cls: type = Track,
            **kwargs
    ) -> Union[List[Track], Playlist]:
        match = self.URI_REGEX.match(query)
        if match:
            result = await self.get_track_via_url(match, market=market, cls=cls, **kwargs)
            if isinstance(result, Track):
                return [result]
            return result

        return await self._search_tracks(query, limit=limit, market=market, suppress=suppress, cls=cls, **kwargs)
