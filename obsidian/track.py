import discord

from discord.ext import commands
from typing import Any, Dict, List, Optional

from .enums import Source


__all__: tuple = (
    'Track',
    'Playlist'
)


class Track:
    """
    Represents an obsidian song track.
    
    Parameters
    ----------
    id: str
        The base 64 track ID.
    info: Dict[str, Any]
        The raw JSON payload returned by Obsidian,
        containing information about this track.
    ctx: Optional[:class:`commands.Context`]
        An optional context to use for this track.  
        By default, if this is provided, :attr:`Track.requester` will be the author of the context.
    kwargs
        Extra keyword arguments to pass into the constructor.
    """

    __slots__: tuple = (
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
    )

    def __init__(self, *, id: str, info: Dict[str, Any], ctx: Optional[commands.Context] = None, **kwargs) -> None:
        self._ctx: Optional[commands.Context] = ctx
        self._requester: Optional[discord.Member] = kwargs.get('requester') or (ctx.author if ctx else None)

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
        self._thumbnail: Optional[str] = info.get('thumbnail')

    def __repr__(self) -> str:
        return f'<Track title={self._title!r} uri={self._uri!r} source={self.source!r} length={self._length}>'

    @property
    def id(self) -> str:
        """
        str: The Base64 Track ID, can be used to rebuild track objects.

        See Also
        --------
        :meth:`.Node.decode_track`
        """
        return self._id

    @property
    def ctx(self) -> Optional[commands.Context]:
        """
        Optional[:class:`~discord.ext.commands.Context`]: The :class:`~discord.ext.commands.Context` 
        that invoked the track. Could be `None` .
        """
        return self._ctx

    @property
    def title(self) -> str:
        """
        str: The track title.
        """
        return self._title

    @property
    def author(self) -> str:
        """
        str: The author of the track.
        """
        return self._author

    @property
    def uri(self) -> str:
        """
        str: The track's URI.
        """
        return self._uri

    @property
    def identifier(self) -> str:
        """
        str: The tracks identifier.
        """
        return self._identifier

    @property
    def length(self) -> int:
        """
        int: The duration of the track in milliseconds.
        """
        return self._length

    @property
    def position(self) -> int:
        """
        int: The current position of the track in milliseconds.
        """
        return self._position

    @property
    def stream(self) -> bool:
        """
        bool: Whether the track is a stream or not.
        """
        return self._is_stream

    @property
    def seekable(self) -> bool:
        """
        bool: If you are able to seek the track's position or not.
        """
        return self._is_seekable

    @property
    def source(self) -> Source:
        """
        :class:`Source`: Return an |enum_link| indicates the type of the :class:`.Source` .
        """
        return self._source

    @property
    def thumbnail(self) -> str:
        """
        str: Return the image URL of the track's thumbnail, could be an empty :class:`str` depending on the :class:`.Source` .
        """
        if self.source is Source.YOUTUBE:
            return f'https://img.youtube.com/vi/{self.identifier}/hqdefault.jpg'

        if self._thumbnail:
            return self._thumbnail

        return ''

    @property
    def requester(self) -> Optional[discord.Member]:
        """
        Optional[:class:`discord.Member`]: The :class:`discord.Member` that requested the track.
        """
        return self._requester

    @ctx.setter
    def ctx(self, ctx: commands.Context) -> None:
        """
        A utility `function` for changing the :attr:`ctx`.
        """
        self._ctx = ctx

    @requester.setter
    def requester(self, requester: discord.Member) -> None:
        """
        A utility `function` for changing the :attr:`requester`.
        """
        self._requester = requester


class Playlist:
    """
    Represents a playlist of tracks.
    """

    def __init__(
            self,
            *,
            info: Dict[str, Any],
            tracks: List[Dict[str, Any]],
            ctx: Optional[commands.Context] = None,
            cls: type = Track,
            **kwargs
    ) -> None:
        self._ctx: Optional[commands.Context] = ctx
        self._requester: Optional[discord.Member] = kwargs.get('requester') or (ctx.author if ctx else None)

        self._name: str = info['name']
        self._tracks: List[Dict[str, Any]] = tracks
        self._selected_track: int = info.get('selected_track', 0)

        self._uri: Optional[str] = info.get('uri')

        self.__track_cls: type = cls
        self.__constructed_tracks: Optional[List[Track]] = None
        self.__kwargs = kwargs

    @property
    def __track_kwargs(self) -> Dict[str, Any]:
        return {
            **self.__kwargs,
            'requester': self._requester
        }

    @property
    def count(self) -> int:
        """
        int: Return the total amount of tracks in the playlist.
        """
        return len(self._tracks)

    @property
    def tracks(self) -> List[Track]:
        """
        List[Track]: Return a `list` of :class:`Track` s.
        """
        if self.__constructed_tracks is not None:
            return self.__constructed_tracks

        self.__constructed_tracks = res = [
            self.__track_cls(id=track['track'], info=track['info'], ctx=self.ctx, **self.__track_kwargs)
            for track in self._tracks
        ]
        return res

    @property
    def ctx(self) -> Optional[commands.Context]:
        """
        Optional[:class:`~discord.ext.commands.Context`]: The :class:`~discord.ext.commands.Context` 
        that invoked the playlist. Could be `None` .
        """
        return self._ctx

    @property
    def name(self) -> str:
        """
        str: The name of the playlist.
        """
        return self._name

    @property
    def selected_track(self) -> Optional[Track]:
        """
        The selected track returned by Obsidian, could be `None` .
        """
        try:
            return self.tracks[self._selected_track]
        except IndexError:
            return self.tracks[0]

    @property
    def uri(self) -> Optional[str]:
        """
        str: The playlist's URI.
        """
        return self._uri

    @property
    def source(self) -> Source:
        """
        :class:`.Source`: Return an |enum_link| indicates the type of the :class:`.Source` .
        """
        try:
            return self.tracks[0].source
        except (IndexError, KeyError):
            return Source.YOUTUBE

    @property
    def requester(self) -> Optional[discord.Member]:
        """
        Optional[:class:`discord.Member`]: The :class:`discord.Member` that requested the playlist.
        """
        return self._requester

    @requester.setter
    def requester(self, requester: discord.Member) -> None:
        """
        A utility `function` for changing the :attr:`requester`.
        """
        self._requester = requester

    @ctx.setter
    def ctx(self, ctx: commands.Context) -> None:
        """
        A utility `function` for changing the :attr:`ctx`.
        """
        self._ctx = ctx

    def __iter__(self) -> iter:
        return iter(self._tracks)

    def __len__(self) -> int:
        return self.count

    def __repr__(self) -> str:
        return f'<Playlist name={self._name!r} selected_track={self.selected_track} count={len(self._tracks)}>'
