import inspect

from typing import Any, TYPE_CHECKING
from functools import wraps

from .events import *

if TYPE_CHECKING:
    from .player import Player


__all__: tuple = (
    'NodeListenerMixin',
)
    
try:
    removeprefix = str.removeprefix
except AttributeError:
    removeprefix = lambda s, prefix: s[len(prefix):] if s.startswith(prefix) else s


class NodeListenerMixin:
    """Add this as a mixin to your class to add node listeners to your class.

    All listeners begin with `on_obsidian_...`, e.g. `on_obsidian_track_end`,
    and all listeners should follow the signature `(player: Player, event: BaseEvent) -> Any`

    All listeners must be a |coroutine_link|.

    To add a listener, just add a function with it's name being the listener name.

    Example
    -------

    .. code:: py

        async def on_obsidian_track_end(player: Player, event: TrackStartEvent) -> Any:
             pass

    Current possible events:
    - `on_obsidian_track_start`
    - `on_obsidian_track_end`
    - `on_obsidian_track_stuck`
    - `on_obsidian_track_exception`
    - `on_obsidian_websocket_open`
    - `on_obsidian_websocket_closed`
    """

    __node_listener_possible_events: tuple = (
        'obsidian_track_start',
        'obsidian_track_end',
        'obsidian_track_stuck',
        'obsidian_track_exception',
        'obsidian_websocket_open',
        'obsidian_websocket_closed'
    )

    def __new__(cls, *args, **kwargs):
        _node_attr_name = kwargs.pop('node', 'node')

        def overwrite(__init__):
            @wraps(__init__)
            def __overwritten_init__(self, *args, **kwargs):
                __init__(self, *args, **kwargs)

                try:
                    node = getattr(self, _node_attr_name)
                except AttributeError:
                    raise ValueError(f'object must have a {_node_attr_name!r} attribute')

                def predicate(func):
                    try:
                        return func.__name__.startswith('on_') and removeprefix(
                            func.__name__,
                            'on_'
                        ) in cls.__node_listener_possible_events
                    except AttributeError:
                        return False

                for name, listener in inspect.getmembers(cls, predicate):
                    name = name.removeprefix('on_')
                    if name not in node.__listeners__:
                        node.__listeners__[name] = [listener]
                        return

                    node.__listeners__[name].append(listener)

            return __overwritten_init__

        cls.__init__ = overwrite(cls.__init__)
        self = super().__new__(cls)
        return self

    async def on_obsidian_track_start(self, player: 'Player', event: TrackStartEvent) -> Any:
        ...

    async def on_obsidian_track_end(self, player: 'Player', event: TrackEndEvent) -> Any:
        ...

    async def on_obsidian_track_stuck(self, player: 'Player', event: TrackStuckEvent) -> Any:
        ...

    async def on_obsidian_track_exception(self, player: 'Player', event: TrackExceptionEvent) -> Any:
        ...

    async def on_obsidian_websocket_open(self, player: 'Player', event: WebsocketOpenEvent) -> Any:
        ...

    async def on_obsidian_websocket_closed(self, player: 'Player', event: WebsocketCloseEvent) -> Any:
        ...
