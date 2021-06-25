# credit: https://github.com/Axelancerr/Slate/tree/main/slate/objects/enums.py#L62

from enum import Enum


__all__: tuple = (
    'OpCode',
    'Source',
    'LoadType',
    'SearchType',
    'EventType',
    'TrackEndReason',
    'TrackExceptionSeverity'
)


class OpCode(Enum):
    SUBMIT_VOICE_UPDATE = 0
    STATS = 1

    SETUP_RESUMING = 2
    SETUP_DISPATCH_BUFFER = 3

    PLAYER_EVENT = 4
    PLAYER_UPDATE = 5

    PLAY_TRACK = 6
    STOP_TRACK = 7

    PLAYER_PAUSE = 8
    PLAYER_FILTERS = 9
    PLAYER_SEEK = 10
    PLAYER_DESTROY = 11
    PLAYER_CONFIGURE = 12


class Source(Enum):
    """|enum|

    Represents a search source.

    Attributes
    ----------
    YOUTUBE
        The search source for Youtube.
    YOUTUBE_MUSIC
        The search source for Youtube Music.
    SOUNDCLOUD
        The search source for Soundcloud.
    SPOTIFY
        The search soruce for Spotify.
        Your node must have a valid :class:`SpotifyClient` in order to use this source.
    YARN
        The search source for Yarn.
    BANDCAMP
        The search source for Bandcamp.
    TWITCH
        The search source for Twitch.
    VIMEO
        The search source for Vimeo.
    NICO
        The search source Nico.
    LOCAL
        Searches your local files.
    HTTP
        If the query is a direct URL, allow them.

    See Also
    --------
    :meth:`Node.search_track`

    :meth:`Node.search_tracks`
    """

    YOUTUBE = 'youtube'
    YOUTUBE_MUSIC = 'youtube_music'
    SOUNDCLOUD = 'soundcloud'
    SPOTIFY = 'spotify'

    YARN = 'yarn'
    BANDCAMP = 'bandcamp'
    TWITCH = 'twitch'
    VIMEO = 'vimeo'
    NICO = 'nico'
    LOCAL = 'local'
    HTTP = 'http'


class LoadType(Enum):
    """|enum|

    Represents load types that Obsidian sends.

    Attributes
    ----------
    NO_MATCHES
        No matches were found.
    LOAD_FAILED
        Something went wrong while trying to load tracks.
    PLAYLIST_LOADED
        A playlist was loaded.
    TRACK_LOADED
        A track (or tracks) were loaded.
    SEARCH_RESULT
        A result from a search query was loaded.
    """

    NO_MATCHES = 'NO_MATCHES'
    LOAD_FAILED = 'LOAD_FAILED'
    PLAYLIST_LOADED = 'PLAYLIST_LOADED'
    TRACK_LOADED = 'TRACK_LOADED'
    SEARCH_RESULT = 'SEARCH_RESULT'


class SearchType(Enum):
    TRACK = 'track'
    PLAYLIST = 'playlist'
    ALBUM = 'album'
    ARTIST = 'artist'


class EventType(Enum):
    """|enum|

    Represents the type of event Obsidian has sent.

    Attributes
    ----------
    TRACK_START
        A track has started.
    TRACK_END
        A track has ended.
    TRACK_STUCK
        A track has gotten stuck.
    TRACK_EXCEPTION
        There was an error while playing the track.
    WEBSOCKET_OPEN
        A websocket connection with Obsidian has been opened.
    WEBSOCKET_CLOSED
        A websocket connection with Obsidian has been closed.
    """

    TRACK_START = 'TRACK_START'
    TRACK_END = 'TRACK_END'
    TRACK_STUCK = 'TRACK_STUCK'
    TRACK_EXCEPTION = 'TRACK_EXCEPTION'
    WEBSOCKET_OPEN = 'WEBSOCKET_OPEN'
    WEBSOCKET_CLOSED = 'WEBSOCKET_CLOSED'


class TrackEndReason(Enum):
    """|enum|

    Represents a reason on why a track has ended.

    Attributes
    ----------
    STOPPED
        The track was manually stopped.
    REPLACED
        The track was replaced by another track.
    CLEANUP
        The track was cleared on cleanup.
    LOAD_FAILED
        The track failed to load.
    FINISHED
        The track finished.

    See Also
    --------
    :class:`TrackEndEvent`
    """

    STOPPED = 'STOPPED'
    REPLACED = 'REPLACED'
    CLEANUP = 'CLEANUP'
    LOAD_FAILED = 'LOAD_FAILED'
    FINISHED = 'FINISHED'


class TrackExceptionSeverity(Enum):
    """|enum|

    Represents a severity rating for the exception from :class:`TrackExceptionEvent`.

    Attributes
    ----------
    COMMON
        A common exception occured.
    SUSPICIOUS
        A suspicious exception occured.
    FAULT
        A faulty exception occured.
    """

    COMMON = 'COMMON'
    SUSPICIOUS = 'SUSPICIOUS'
    FAULT = 'FAULT'
