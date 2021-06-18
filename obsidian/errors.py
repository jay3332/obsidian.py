from __future__ import annotations

from .node import BaseNode


class ObsidianException(Exception):
    """
    Raised when an error related to this module occurs.
    """


class NodeNotConnected(ObsidianException):
    """
    Raised when a socket request is sent without the node being connected.
    """


class ObsidianConnectionFailure(ObsidianException):
    """
    Raised when connecting fails.
    """

    def __init__(self, node: BaseNode, error: BaseException) -> None:
        self.node = node
        self.original = error

        message = f'Node {node.identifier!r} failed to connect ({error.__class__.__name__}): {error}'
        super().__init__(message)

    @classmethod
    def from_message(cls, node: BaseNode, message: str) -> ObsidianConnectionFailure:
        instance = cls.__new__(cls)
        instance.node = node
        instance.original = None
        super(ObsidianException, instance).__init__(message)
        return instance


class ObsidianAuthorizationFailure(ObsidianConnectionFailure):
    """
    Raised when connecting fails due to invalid authorization.
    """

    def __new__(cls, node: BaseNode, *args, **kwargs) -> ObsidianAuthorizationFailure:
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
