"""
Defines the classes necessary for building the syntax tree.
"""
from abc import ABC, abstractmethod
from collections.abc import Iterable

import typing as t

from .types import (
    KeyPath,
    NestedDict,
    PassAlias,
)


if t.TYPE_CHECKING:
    from .base import Operation


class SyntaxNode(ABC):
    """
    The abstract superclass for all nodes in the syntax tree.
    """

    @abstractmethod
    def assemble(self) -> "Operation":
        """Assemble the `SyntaxNode` into an `Operation`."""
        _error_msg = "The method `assemble` is not implemented."
        raise NotImplementedError(_error_msg)

    def partial(self, **inputs) -> "SyntaxNode":
        """
        Fix some of the inputs of the operation and return a new
        `SyntaxNode`.
        """

        # Import here to avoid circular import.
        from .combine import Compose  # pylint: disable=import-outside-toplevel
        from .base import (  # pylint: disable=import-outside-toplevel
            Append,
            Return,
        )

        partial_inputs = SyntaxLeaf(Return(inputs))

        append_partial_inputs = SyntaxBranch(Append, children=[partial_inputs])

        return SyntaxBranch(Compose, children=[append_partial_inputs, self])

    def __call__(self, **inputs) -> NestedDict:
        """Assembles the operation and calls it."""
        operation = self.assemble()
        return operation(**inputs)

    def __pos__(self) -> "SyntaxNode":
        # Import here to avoid circular import.
        from .base import Append  # pylint: disable=import-outside-toplevel

        return SyntaxBranch(Append, children=[self])

    def __or__(
            self,
            other: t.Union["SyntaxNode", PassAlias],
    ) -> "SyntaxNode":
        # Import here to avoid circular import.
        from .combine import Compose  # pylint: disable=import-outside-toplevel

        other = ensure_syntax_node(other)

        compose = SyntaxBranch(Compose, children=[self, other])

        return compose

    def __ror__(
            self,
            other: t.Union["SyntaxNode", PassAlias],
    ) -> "SyntaxNode":
        # Import here to avoid circular import.
        from .combine import Compose  # pylint: disable=import-outside-toplevel

        other = ensure_syntax_node(other)

        compose = SyntaxBranch(Compose, children=[other, self])

        return compose

    def __and__(
            self,
            other: t.Union["SyntaxNode", PassAlias],
    ) -> "SyntaxNode":
        # Import here to avoid circular import.
        from .combine import Concat  # pylint: disable=import-outside-toplevel

        other = ensure_syntax_node(other)

        concat = SyntaxBranch(Concat, children=[self, other])

        return concat

    def __rand__(
            self,
            other: t.Union["SyntaxNode", PassAlias],
    ) -> "SyntaxNode":
        # Import here to avoid circular import.
        from .combine import Concat  # pylint: disable=import-outside-toplevel

        other = ensure_syntax_node(other)

        concat = SyntaxBranch(Concat, children=[other, self])

        return concat

    def __rrshift__(self, other: t.Any) -> t.Tuple[t.Any, "SyntaxNode"]:
        return (other, self)


class SyntaxLeaf(SyntaxNode):
    """Wraps operations."""

    def __init__(
            self,
            operation: t.Union["Operation", PassAlias],
    ):
        # Import here to avoid circular import.
        # pylint: disable=import-outside-toplevel
        from .base import ensure_operation

        operation = ensure_operation(operation)

        self.operation = operation

    def assemble(self) -> "Operation":
        return self.operation

    def __repr__(self) -> str:
        debug_info = repr(self.operation) + "\n"
        debug_info += " -- input type tree:\n"
        debug_info += repr(self.operation.input_type_tree)
        debug_info += "\n"
        debug_info += " -- output type tree:\n"
        debug_info += repr(self.operation.output_type_tree)
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


class SwitchNode(SyntaxNode):
    """Wraps the `Switch` combination."""

    def __init__(
            self,
            key: KeyPath,
            cases: t.Iterable[t.Tuple[t.Any, SyntaxNode]],
            default: t.Optional[SyntaxNode] = None,
    ):
        self.key = key
        self.cases = cases
        self.default = default

    def assemble(self) -> "Operation":
        # Import here to avoid circular import.
        from .combine import Switch  # pylint: disable=import-outside-toplevel

        cases = [(c, o.assemble()) for c, o in self.cases]

        default = None
        if self.default is not None:
            default = self.default.assemble()

        return Switch(
            self.key,
            *cases,
            default=default,
        )

    def __repr__(self) -> str:
        debug_info = f"Switch {self.key} {{\n"
        for c, o in self.cases:
            debug_info += f"\tcase {c}: {repr(o)}\n"
        debug_info += "}\n"
        return debug_info


def switch(
        key: KeyPath,
        *cases,
        default: t.Optional[t.Union[SyntaxNode, PassAlias]] = None,
) -> SwitchNode:
    """Creates a `SwitchNode`."""

    cases_ensured = [(c, ensure_syntax_node(o)) for c, o in cases]

    default_ensured = None

    if default is not None:
        default_ensured = ensure_syntax_node(default)

    return SwitchNode(
        key=key,
        cases=cases_ensured,
        default=default_ensured,
    )


class CycleNode(SyntaxNode):
    """Wraps the `Cycle` combination."""

    def __init__(
        self,
        operation: t.Union[SyntaxNode, PassAlias],
        counter: t.Optional[int] = -1,
        key: t.Optional[KeyPath] = None,
    ):
        self.operation = ensure_syntax_node(operation)
        self.counter = counter
        self.key = key

    def assemble(self) -> "Operation":
        # Import here to avoid circular import.
        from .combine import Cycle  # pylint: disable=import-outside-toplevel

        return Cycle(
            operation=self.operation.assemble(),
            counter=self.counter,
            key=self.key,
        )

    def __repr__(self) -> str:
        key = str(self.key) if self.key is not None else ""
        counter = str(self.counter) if self.counter != -1 else ""

        debug_info = f"Cycle {key} {counter} {{\n"
        debug_info += f"\t{repr(self.operation)}\n"
        debug_info += "}\n"
        return debug_info


def cycle(
        operation: t.Union[SyntaxNode, PassAlias],
        counter: t.Optional[int] = -1,
        key: t.Optional[KeyPath] = None,
) -> CycleNode:
    """Creates a `CycleNode`."""
    operation = ensure_syntax_node(operation)

    return CycleNode(
        operation=operation,
        counter=counter,
        key=key,
    )


def ensure_syntax_node(
        obj: t.Union[SyntaxNode, PassAlias],
) -> SyntaxNode:
    """Ensures that `obj` is a syntax node."""
    # Import here to avoid circular import.
    # pylint: disable=import-outside-toplevel
    from .base import ensure_operation

    if isinstance(obj, SyntaxNode):
        return obj

    return ensure_operation(obj).get_syntax_node()
