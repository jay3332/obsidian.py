from typing import Any, Dict

from .enums import EventType, TrackEndReason, TrackExceptionSeverity


__all__: list = [
    'BaseEvent',
    'TrackStartEvent',
    'TrackEndEvent',
    'TrackStuckEvent',
    'TrackExceptionEvent',
    'WebsocketOpenEvent',
    'WebsocketCloseEvent',
    'get_cls'
]


class BaseEvent(object):
    __slots__ = ['_type', '_guild_id']

    def __init__(self, data: Dict[str, Any]) -> None:
        try:
            # These will appear in all our events
            self._type: EventType = EventType(data['type'])
            self._guild_id: int = int(data['guild_id'])
        except KeyError:
            # This event has an odd payload.
            self._type = None
            self._guild_id = None

    @property
    def __base_repr__(self) -> str:
        return f'type={self._type} guild_id={self._guild_id}'

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self.__base_repr__}>'

    @property
    def type(self) -> EventType:
        return self._type

    @property
    def guild_id(self) -> int:
        return self._guild_id


class TrackStartEvent(BaseEvent):
    __slots__ = ['_type', '_guild_id', '_track_id']

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)
        self._track_id: str = data.get('track')

    def __repr__(self) -> str:
        return f'<TrackStartEvent {self.__base_repr__} track_id={self._track_id!r}>'

    @property
    def track_id(self) -> str:
        return self._track_id


class TrackEndEvent(BaseEvent):
    __slots__ = ['_type', '_guild_id', '_track_id', '_reason']

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)

        self._track_id: str = data.get('track')
        self._reason: TrackEndReason = TrackEndReason(data['reason'])

    def __repr__(self) -> str:
        return f'<TrackEndEvent {self.__base_repr__} reason={self._reason} track_id={self._track_id!r}>'

    @property
    def track_id(self) -> str:
        return self._track_id

    @property
    def reason(self) -> TrackEndReason:
        return self._reason


class TrackStuckEvent(BaseEvent):
    __slots__ = ['_type', '_guild_id', '_track_id', '_threshold']

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)

        self._track_id: str = data.get('track')
        self._threshold: int = data['threshold_ms']

    def __repr__(self) -> str:
        return f'<TrackEndEvent {self.__base_repr__} threshold={self.threshold:.4f} track_id={self._track_id!r}>'

    @property
    def track_id(self) -> str:
        return self._track_id

    @property
    def threshold_ms(self) -> int:
        return self._threshold

    @property
    def threshold(self) -> float:
        return self._threshold / 1000


class TrackExceptionEvent(BaseEvent):
    __slots__ = ['_type', '_guild_id', '_track_id', '_message', '_cause', '_severity']

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)

        self._track_id: str = data['track']

        exception: Dict[str, Any] = data['exception']
        self._message: str = exception['message']
        self._cause: str = exception['cause']
        self._severity: TrackExceptionSeverity = TrackExceptionSeverity(exception['severity'])

    def __repr__(self) -> str:
        return f'<TrackExceptionEvent {self.__base_repr__} severity={self.severity} ' \
               f'cause={self.cause!r} message={self.message!r} track_id={self._track_id!r} >'

    @property
    def track_id(self) -> str:
        return self._track_id

    @property
    def message(self) -> str:
        return self._message

    @property
    def cause(self) -> str:
        return self._cause

    @property
    def severity(self) -> TrackExceptionSeverity:
        return self._severity


class WebsocketOpenEvent(BaseEvent):
    __slots__ = ['_type', '_guild_id', '_target', '_ssrc']

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)

        self._target: str = data['target']
        self._ssrc: int = data['ssrc']

    @property
    def target(self) -> str:
        return self._target

    @property
    def ssrc(self) -> int:
        return self._ssrc


class WebsocketCloseEvent(BaseEvent):
    __slots__ = ['_type', '_guild_id', '_code', '_reason', '_by_remote']

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)

        self._code: int = data['code']
        self._reason: str = data['reason']
        self._by_remote: bool = data['by_remote']

    @property
    def code(self) -> int:
        return self._code

    @property
    def reason(self) -> str:
        return self._reason

    @property
    def by_remote(self) -> bool:
        return self._by_remote


__mapping__ = {
    'TRACK_START': TrackStartEvent,
    'TRACK_END': TrackEndEvent,
    'TRACK_STUCK': TrackStuckEvent,
    'TRACK_EXCEPTION': TrackExceptionEvent,
    'WEBSOCKET_READY': WebsocketOpenEvent,
    'WEBSOCKET_OPEN': WebsocketOpenEvent,
    'WEBSOCKET_CLOSED': WebsocketCloseEvent
}


def get_cls(type_: str, /) -> type:
    return __mapping__.get(type_.upper())
