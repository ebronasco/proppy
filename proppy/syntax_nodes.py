"""
Defines the classes necessary for building the syntax tree.
"""
from abc import ABC, abstractmethod
from collections.abc import Iterable

import typing as t

from .base.let import ensure_operation
from .base.append import Append
from .base.const import Const

from .types import (
    NestedDict,
    LetAlias,
    Key,
)


if t.TYPE_CHECKING:
    from .base.operation import Operation


class SyntaxNode(ABC):
    """
    The abstract superclass for all nodes in the syntax tree.
    """

    @abstractmethod
    def assemble(self) -> "Operation":
        """Assemble the `SyntaxNode` into an `Operation`."""
        _error_msg = "The method `assemble` is not implemented."
        raise NotImplementedError(_error_msg)

    def partial(
            self,
            output_keys: t.Optional[t.Set[Key]] = None,
            **inputs,
    ) -> "SyntaxNode":
        """
        Fix some of the inputs of the operation and return a new
        `SyntaxNode`.
        """

        # Import here to avoid circular import.
        # pylint: disable=import-outside-toplevel
        from .unions import Compose

        partial_inputs = SyntaxLeaf(Const(inputs, output_keys=output_keys))

        append_partial_inputs = SyntaxBranch(Append, children=[partial_inputs])

        return SyntaxBranch(Compose, children=[append_partial_inputs, self])

    def __call__(self, **inputs) -> NestedDict:
        """Assembles the operation and calls it."""
        operation = self.assemble()
        return operation(**inputs)

    def __pos__(self) -> "SyntaxNode":

        return SyntaxBranch(Append, children=[self])

    def __or__(
            self,
            other: t.Union["SyntaxNode", LetAlias],
    ) -> "SyntaxNode":
        # Import here to avoid circular import.
        from .unions import Compose  # pylint: disable=import-outside-toplevel

        other = ensure_syntax_node(other)

        compose = SyntaxBranch(Compose, children=[self, other])

        return compose

    def __ror__(
            self,
            other: t.Union["SyntaxNode", LetAlias],
    ) -> "SyntaxNode":
        # Import here to avoid circular import.
        from .unions import Compose  # pylint: disable=import-outside-toplevel

        other = ensure_syntax_node(other)

        compose = SyntaxBranch(Compose, children=[other, self])

        return compose

    def __and__(
            self,
            other: t.Union["SyntaxNode", LetAlias],
    ) -> "SyntaxNode":
        # Import here to avoid circular import.
        from .unions import Concat  # pylint: disable=import-outside-toplevel

        other = ensure_syntax_node(other)

        concat = SyntaxBranch(Concat, children=[self, other])

        return concat

    def __rand__(
            self,
            other: t.Union["SyntaxNode", LetAlias],
    ) -> "SyntaxNode":
        # Import here to avoid circular import.
        from .unions import Concat  # pylint: disable=import-outside-toplevel

        other = ensure_syntax_node(other)

        concat = SyntaxBranch(Concat, children=[other, self])

        return concat

    def __rrshift__(self, other: t.Any) -> t.Tuple[t.Any, "SyntaxNode"]:
        return (other, self)


class SyntaxLeaf(SyntaxNode):
    """Wraps operations."""

    def __init__(
            self,
            operation: t.Union["Operation", LetAlias],
    ):

        operation = ensure_operation(operation)

        self.operation = operation

    def assemble(self) -> "Operation":
        return self.operation

    def __repr__(self) -> str:
        debug_info = repr(self.operation) + "\n"
        debug_info += " -- input keys:\n"
        debug_info += repr(self.operation.input_keys)
        debug_info += "\n"
        debug_info += " -- output keys:\n"
        debug_info += repr(self.operation.output_keys)
        return debug_info


class SyntaxBranch(SyntaxNode):
    """Wraps combinations of operations, that is, Concat, Compose, Append."""

    def __init__(
            self,
            operation_class: t.Type["Operation"],
            children: t.Optional[t.Iterable] = None,
    ):
        self.operation_class = operation_class
        self.children: t.Iterable = {}

        if children is not None:
            if not isinstance(children, Iterable):
                _error_msg = "The `children` argument must be an Iterable."
                raise TypeError(_error_msg)

            self.children = children

    def flatten(self) -> None:
        """
        Flattens the children recursively, for example, the syntax tree
        `Compose(Compose(x, y), z)` becomes `Compose(x, y, z)`.
        """
        new_children = []

        for child in self.children:
            if not isinstance(child, SyntaxBranch) \
                    or child.operation_class != self.operation_class:
                new_children.append(child)
                continue

            child.flatten()

            new_children += child.children

        self.children = new_children

    def assemble(self) -> "Operation":
        self.flatten()

        return self.operation_class(
            *[child.assemble() for child in self.children]
        )

    def __repr__(self) -> str:
        debug_info = repr(self.operation_class.__name__) + "{\n"
        for child in self.children:
            debug_info += '\t' + repr(child).replace('\n', '\n\t')
            debug_info += '\n\n'

        debug_info += "}"
        return debug_info


def ensure_syntax_node(
        obj: t.Union[SyntaxNode, LetAlias],
) -> SyntaxNode:
    """Ensures that `obj` is a syntax node."""
    if isinstance(obj, SyntaxNode):
        return obj

    return ensure_operation(obj).get_syntax_node()
