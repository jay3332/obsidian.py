from __future__ import annotations

from copy import copy
from collections import deque
from typing import Iterable, Iterator, Optional, Union

from .track import Track, Playlist


class QueueFull(Exception):
    ...


class Queue(Iterable[Track]):
    """Utility queue class made only for Tracks and Playlists.

    .. warning::
        You can only queue Tracks and Playlists. Playlists will be implicitly handled for you.

    Parameters
    ----------
    max_size: Optional[int]
        The maximum number of tracks that the queue can hold.

    cls: type = collections.deque
        The deque class to use for the internal queue.
    """

    def __init__(
            self,
            max_size: Optional[int],
            *,
            cls: type = deque
    ) -> None:
        self.__max_size: Optional[int] = max_size
        self.__queue: deque = cls()

    def __repr__(self) -> str:
        return f'<Queue tracks={self.count}>'

    def __len__(self) -> int:
        return self.count

    def __contains__(self, track: Track) -> bool:
        """
        Check if a track is contained inside of the queue.
        """
        return track in self.__queue

    def __bool__(self) -> bool:
        return self.count > 0

    def __add__(self, tracks: Iterable[Track]) -> Queue:
        new = self.copy()
        new.extend(tracks)
        return new

    def __iadd__(self, track: Union[Iterable[Union[Track, Playlist]], Union[Track, Playlist]]) -> None:
        if isinstance(track, (Track, Playlist)):
            return self.add(track)

        self.extend(track)

    def __iter__(self) -> Iterator[Track]:
        return iter(self.__queue)

    def __reversed__(self) -> Iterator[Track]:
        return reversed(self.__queue)

    def __getitem__(self, index: int) -> Track:
        return self.__queue[index]

    def __setitem__(self, index: int, item: Track) -> None:
        self.__queue[index] = item

    def __delitem__(self, index: int) -> None:
        del self.__queue[index]

    @property
    def internal_queue(self) -> deque:
        return self.__queue

    @property
    def max_size(self) -> Optional[int]:
        return self.__max_size

    @property
    def count(self) -> int:
        return len(self.__queue)

    @property
    def full(self) -> bool:
        if self.max_size is None:
            return False
        return self.count >= self.max_size

    def add(self, track: Union[Track, Playlist], *, left: bool = False) -> None:
        """Adds a Track or Playlist to the queue.

        If a playlist is provided, the queue will extend from it's tracks.
        """

        if isinstance(track, Playlist):
            return self.extend(track.tracks)

        if self.full:
            raise QueueFull(f'Could not add track {track.title!r} because the queue was full.')

        method = self.__queue.appendleft if left else self.__queue.append
        method(track)

    def set(self, index: int, new: Track) -> None:
        self.__setitem__(index, new)

    def remove(self, track_or_index: Union[int, Track]) -> None:
        if isinstance(track_or_index, int):
            return self.__delitem__(track_or_index)

        self.__queue.remove(track_or_index)

    def pop(self, index: int = 0) -> Track:
        """The rough equivalent of :meth:`Queue.remove` but is internally done differently.

        Note: This removes from the left, not the right unlike regular Python lists.
        This is because queues would usually work like this.
        """

        if index == 0:
            return self.__queue.popleft()

        if index == -1:
            return self.__queue.pop()

        _before = self.__queue[index]
        self.remove(index)
        return _before

    def get(self) -> Track:
        return self.pop()

    def insert(self, index: int, track: Union[Track, Playlist]) -> None:
        if isinstance(track, Playlist):
            raise TypeError(f'Playlists are not supported for insertion as of now.')

        if self.full:
            raise QueueFull(f'Could not insert track {track.title!r} because the queue was full.')

        self.__queue.insert(index, track)

    def extend(self, tracks: Iterable[Union[Track, Playlist]]) -> None:
        for track in tracks:
            self.add(track)

    def copy(self) -> Queue:
        new = self.__class__(self.max_size, cls=type(self.__queue))
        new.__queue = copy(self.__queue)

        return new

    def clear(self) -> None:
        self.__queue.clear()

    append = add
    put = add

    __copy__ = copy
