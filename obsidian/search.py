import logging
import contextlib

from re import compile, Pattern
from typing import Any, Dict, List, Optional, Tuple, Union

from .track import Track, Playlist
from .enums import Source, LoadType
from .errors import ObsidianSearchFailure, NoSearchMatchesFound


DEFAULT_MATCH_REGEX = compile(r'^https?://(?:www\.)?.+')

__all__: list = [
    'TrackSearcher'
]

__log__ = logging.getLogger('obsidian.node')


class _EmptyContextManager:
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class TrackSearcher:
    """
    Searches for tracks via URLs or queries.
    """

    def __init__(self, node, *, url_match_regex: Union[Pattern, str] = None) -> None:
        from .node import BaseNode

        if isinstance(url_match_regex, str):
            url_match_regex = compile(url_match_regex)

        self._node: BaseNode = node
        self._regex: Pattern = url_match_regex or DEFAULT_MATCH_REGEX

    @property
    def node(self):
        return self._node

    @property
    def _can_run_spotify(self) -> bool:
        return False  # Not Implemented

    async def _execute(self, query: str) -> Dict[str, Any]:
        return await self.node.http.load_tracks(query)

    def _sanitize_search(self, query: str, source: Optional[Source] = None) -> str:
        if self._regex.match(query) is None:
            if source is Source.YOUTUBE:
                query = 'ytsearch:' + query
            elif source is Source.SOUNDCLOUD:
                query = 'scsearch:' + query
            elif source is Source.YOUTUBE_MUSIC:
                query = 'ytmsearch:' + query

        return query

    async def _get_tracks(self, query: str, source: Optional[Source] = None, **kwargs) -> Tuple[Dict[str, Any], LoadType]:
        response = await self._execute(self._sanitize_search(query, source))

        load_type = LoadType(response['load_type'])
        message = f'SEARCH | Query {query!r} returned {load_type}: {response}'

        if load_type is LoadType.LOAD_FAILED:
            __log__.warning(message)
            raise ObsidianSearchFailure(response.get('exception'))

        __log__.info(message)

        if load_type is LoadType.NO_MATCHES or not response['tracks']:
            raise NoSearchMatchesFound(query)

        return response, load_type

    async def search_track(
            self,
            query: str,
            *,
            source: Optional[Source] = None,
            cls: type = Track,
            suppress: bool = True,
            **kwargs
    ) -> Optional[Union[Track, Playlist]]:
        if suppress:
            _suppressor = contextlib.suppress(ObsidianSearchFailure)
        else:
            _suppressor = _EmptyContextManager()

        with _suppressor:
            response, load_type = await self._get_tracks(query, source)

            if load_type is LoadType.PLAYLIST_LOADED:
                info = response['playlist_info']
                info['uri'] = query

                return Playlist(info=info, tracks=response['tracks'], cls=cls, **kwargs)

            if load_type is LoadType.TRACK_LOADED or load_type is LoadType.SEARCH_RESULT:
                try:
                    first = response['tracks'][0]
                except IndexError:
                    return
                else:
                    return cls(id=first['track'], info=first['info'], **kwargs)

    async def search_tracks(
            self,
            query: str,
            *,
            source: Optional[Source] = None,
            cls: type = Track,
            suppress: bool = False,
            limit: Optional[int] = None,
            **kwargs
    ) -> Optional[Union[List[Track], Playlist]]:
        if suppress:
            _suppressor = contextlib.suppress(ObsidianSearchFailure)
        else:
            _suppressor = _EmptyContextManager()

        with _suppressor:
            response, load_type = await self._get_tracks(query, source)

            if load_type is LoadType.PLAYLIST_LOADED:
                info = response['playlist_info']
                info['uri'] = query

                return Playlist(info=info, tracks=response['tracks'], cls=cls, **kwargs)

            if load_type is LoadType.TRACK_LOADED or load_type is LoadType.SEARCH_RESULT:
                tracks = [
                    cls(id=track['track'], info=track['info'], **kwargs)
                    for track in response['tracks']
                ]

                if limit is not None:
                    tracks = tracks[:limit]

                return tracks
