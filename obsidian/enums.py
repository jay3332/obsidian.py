from enum import Enum


__all__ = [
    'OpCode',
    'Source'
]


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
    YARN = 'yarn'
    BANDCAMP = 'bandcamp'
    TWITCH = 'twitch'
    VIMEO = 'vimeo'
    NICO = 'nico'
    SOUNDCLOUD = 'soundcloud'
    LOCAL = 'local'
    HTTP = 'http'
    SPOTIFY = 'spotify'
