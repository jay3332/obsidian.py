from __future__ import annotations

from aiohttp import ClientResponse


__all__: tuple = (
    'ObsidianException',
    'ObsidianSearchFailure',
    'NoSearchMatchesFound',
    'HTTPError',
    'NodeNotConnected',
    'NodeAlreadyExists',
    'NodeCreationError',
    'ObsidianConnectionFailure',
    'ObsidianAuthorizationFailure',
    'ObsidianSpotifyException',
    'SpotifyHTTPError',
    'SpotifyAuthorizationFailure'
)


class ObsidianException(Exception):
    """
    Raised when an error related to this module occurs.
    """


class ObsidianSearchFailure(ObsidianException):
    """
    Raised when searching for a track fails.
    """


class NoSearchMatchesFound(ObsidianSearchFailure):
    """
    Raised when no matches are found via search query.
    """

    def __init__(self, query: str) -> None:
        super().__init__(f'No song matches for query {query!r}.')


class HTTPError(ObsidianException):
    """
    Raised when an error via HTTP request occurs.
    """

    def __init__(self, message: str, response: ClientResponse) -> None:
        super().__init__(message)
        self.response: ClientResponse = response


class ObsidianSpotifyException(ObsidianException):
    """
    Raised when an error related to spotify occurs.
    """


class SpotifyHTTPError(ObsidianSpotifyException):
    """
    Raised when an error via HTTP request [Spotify] occurs.
    """

    def __init__(self, message: str, response: ClientResponse) -> None:
        super().__init__(message)
        self.response: ClientResponse = response


class SpotifyAuthorizationFailure(SpotifyHTTPError):
    """
    Raised when authorizing to spotify fails.
    """


class NodeNotConnected(ObsidianException):
    """
    Raised when a socket request is sent without the node being connected.
    """


class ObsidianConnectionFailure(ObsidianException):
    """
    Raised when connecting fails.

    Attributes
    ----------
    node: :class:`BaseNode`
        The node that failed to connect.
    original: Exception
        The exception that was raised.
    """

    def __init__(self, node, error: BaseException) -> None:
        from .node import BaseNode

        self.node: BaseNode = node
        self.original = error

        message = f'Node {node.identifier!r} failed to connect ({error.__class__.__name__}): {error}'
        super().__init__(message)

    @classmethod
    def from_message(cls, node, message: str) -> ObsidianConnectionFailure:
        instance = cls.__new__(cls)
        instance.node = node
        instance.original = None
        super(ObsidianException, instance).__init__(message)
        return instance


class ObsidianAuthorizationFailure(ObsidianConnectionFailure):
    """
    Raised when connecting fails due to invalid authorization.
    """

    def __new__(cls, node, *args, **kwargs) -> ObsidianAuthorizationFailure:
        message = f'Node {node.identifier!r} failed authorization.'
        return ObsidianConnectionFailure.from_message(node, message)


class NodeCreationError(ObsidianException):
    """
    Raised when a node could not be successfully created.
    """


class NodeAlreadyExists(NodeCreationError):
    """
    Raised when a node with the same identifier already exists.
    """

    def __init__(self, identifier: str) -> None:
        message = f'Node identifier {identifier!r} already exists.'
        super().__init__(message)
