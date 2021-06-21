import typing
import discord

from discord.ext import commands

from .enums import Source


__all__: list = [
    'Track',
    'Playlist'
]


class Track:
    """
    Represents an obsidian song track.
    """

    __slots__ = [
        '_id',
        '_ctx',
        '_requester',
        '_title',
        '_author',
        '_uri',
        '_identifier',
        '_length',
        '_position',
        '_is_stream',
        '_is_seekable',
        '_source',
        '_thumbnail'
    ]

    def __init__(self, *, id: str, info: typing.Dict[str, typing.Any], ctx: typing.Optional[commands.Context] = None, **kwargs) -> None:
        self._ctx: typing.Optional[commands.Context] = ctx
        self._requester: typing.Optional[discord.Member] = kwargs.get('requester') or (ctx.author if ctx else None)

        self._id: str = id
        self._uri: str = info['uri']
        self._title: str = info['title']
        self._author: str = info['author']
        self._length: int = info['length']
        self._position: int = info['position']
        self._is_stream: bool = info['is_stream']
        self._identifier: str = info['identifier']
        self._is_seekable: bool = info['is_seekable']
        self._source: Source = Source(info['source_name'])
        self._thumbnail: typing.Optional[str] = info.get('thumbnail')

    def __repr__(self) -> str:
        return f'<Track title={self._title!r} uri={self._uri!r} source={self.source!r} length={self._length}>'

    @property
    def id(self) -> str:
        return self._id

    @property
    def ctx(self) -> typing.Optional[commands.Context]:
        return self._ctx

    @property
    def title(self) -> str:
        return self._title

    @property
    def author(self) -> str:
        return self._author

    @property
    def uri(self) -> str:
        return self._uri

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def length(self) -> int:
        return self._length

    @property
    def position(self) -> int:
        return self._position

    @property
    def stream(self) -> bool:
        return self._is_stream

    @property
    def seekable(self) -> bool:
        return self._is_seekable

    @property
    def source(self) -> Source:
        return self._source

    @property
    def thumbnail(self) -> str:
        if self.source is Source.YOUTUBE:
            return f'https://img.youtube.com/vi/{self.identifier}/hqdefault.jpg'

        if self._thumbnail:
            return self._thumbnail

        return ''

    @property
    def requester(self) -> typing.Optional[discord.Member]:
        return self._requester

    @ctx.setter
    def ctx(self, ctx: commands.Context) -> None:
        self._ctx = ctx

    @requester.setter
    def requester(self, requester: discord.Member) -> None:
        self._requester = requester


class Playlist:
    """
    Represents a playlist of tracks.
    """

    def __init__(
            self,
            *,
            info: typing.Dict[str, typing.Any],
            tracks: typing.List[typing.Dict[str, typing.Any]],
            ctx: typing.Optional[commands.Context] = None,
            cls: type = Track,
            **kwargs
    ) -> None:
        self._ctx: typing.Optional[commands.Context] = ctx
        self._requester: typing.Optional[discord.Member] = kwargs.get('requester') or (ctx.author if ctx else None)

        self._name: str = info['name']
        self._tracks: typing.List[typing.Dict[str, typing.Any]] = tracks
        self._selected_track: int = info['selected_track']

        self._uri: typing.Optional[str] = info.get('uri')

        self.__track_cls: type = cls
        self.__constructed_tracks: typing.Optional[typing.List[Track]] = None
        self.__kwargs = kwargs

    @property
    def __track_kwargs(self) -> typing.Dict[str, typing.Any]:
        return {
            **self.__kwargs,
            'requester': self._requester
        }

    @property
    def count(self) -> int:
        return len(self._tracks)

    @property
    def tracks(self) -> typing.List[Track]:
        if self.__constructed_tracks is not None:
            return self.__constructed_tracks

        self.__constructed_tracks = res = [
            self.__track_cls(id=track['track'], info=track['info'], ctx=self.ctx, **self.__track_kwargs)
            for track in self._tracks
        ]
        return res

    @property
    def ctx(self) -> typing.Optional[commands.Context]:
        return self._ctx

    @property
    def name(self) -> str:
        return self._name

    @property
    def selected_track(self) -> typing.Optional[Track]:
        try:
            return self.tracks[self._selected_track]
        except IndexError:
            return None

    @property
    def uri(self) -> typing.Optional[str]:
        return self._uri

    @property
    def source(self) -> Source:
        try:
            return self.tracks[0].source
        except (IndexError, KeyError):
            return Source.YOUTUBE

    @property
    def requester(self) -> typing.Optional[discord.Member]:
        return self._requester

    @requester.setter
    def requester(self, requester: discord.Member) -> None:
        self._requester = requester

    @ctx.setter
    def ctx(self, ctx: commands.Context) -> None:
        self._ctx = ctx

    def __iter__(self) -> iter:
        return iter(self._tracks)

    def __len__(self) -> int:
        return self.count

    def __repr__(self) -> str:
        return f'<Playlist name={self._name!r} selected_track={self.selected_track} count={len(self._tracks)}>'
