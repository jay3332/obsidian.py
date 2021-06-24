# credit: https://github.com/Axelancerr/Slate/tree/main/slate/objects/enums.py#L62

from enum import Enum


__all__: tuple = (
    'OpCode',
    'Source'
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
    TRACK_START = 'TRACK_START'
    TRACK_END = 'TRACK_END'
    TRACK_STUCK = 'TRACK_STUCK'
    TRACK_EXCEPTION = 'TRACK_EXCEPTION'
    WEBSOCKET_OPEN = 'WEBSOCKET_OPEN'
    WEBSOCKET_CLOSED = 'WEBSOCKET_CLOSED'


class TrackEndReason(Enum):
    STOPPED = 'STOPPED'
    REPLACED = 'REPLACED'
    CLEANUP = 'CLEANUP'
    LOAD_FAILED = 'LOAD_FAILED'
    FINISHED = 'FINISHED'


class TrackExceptionSeverity(Enum):
    COMMON = 'COMMON'
    SUSPICIOUS = 'SUSPICIOUS'
    FAULT = 'FAULT'
