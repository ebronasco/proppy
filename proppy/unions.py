"""
Contains the operations that combine multiple operations into one.
"""
import typing as t

from pydash import py_

from .base.operation import Operation
from .base.let import ensure_operation

from .types import (
    Key,
    NestedDict,
    LetAlias,
)

if t.TYPE_CHECKING:
    from .syntax_nodes import SyntaxNode


class Concat(Operation):
    """
    Combination of operations which takes the union of inputs and outputs.

    **Examples:**
    ```python
    >>> from .base.let import Let
    >>> c = Concat(Let({"x"}), Let({"y"}))
    >>> c(x=1, y=10, z=100) == {"x": 1, "y": 10}
    True

    ```
    """

    def __init__(
            self,
            *operation_aliases: t.Union[Operation, LetAlias],
    ):
        """
        Args:
            *operation_aliases: Operations or aliases of `Let`.
        """
        operations = tuple(ensure_operation(op) for op in operation_aliases)

        input_keys: t.Set[Key] = set()
        output_keys: t.Set[Key] = set()
        for op in operations:
            input_keys = input_keys.union(op.input_keys)
            output_keys = output_keys.union(op.output_keys)

        append = any(op.append for op in operations)

        self.operations = operations

        super().__init__(
            input_keys=input_keys,
            output_keys=output_keys,
            append=append,
            extend=True,
        )

    def __repr__(self) -> str:
        debug_info = super().__repr__()
        for op in self.operations:
            debug_info += '\t' + repr(op).replace('\n', '\n\t')
            debug_info += '\n'
        return debug_info

    def run(self, **inputs) -> NestedDict:
        output: NestedDict = {}

        for operation in self.operations:
            py_.merge(output, operation(**inputs))

        return output

    def get_syntax_node(self) -> "SyntaxNode":
        # pylint: disable=import-outside-toplevel
        from .syntax_nodes import SyntaxBranch

        return SyntaxBranch(Concat)


class Compose(Operation):
    """
    Combination in which the output of an operation serves as the
    input of the next operation.

    **Examples:**
    ```python
    >>> from .base.let import Let
    >>> c = Compose(
    ...     Let({("x", "a"), ("y", "b"), "z"}),
    ...     Let({("a", "u"), "b", "z"})
    ... )
    >>> c(x=1, y=10, z=100) == {"u": 1, "b": 10, "z": 100}
    True
    >>> c = Compose(
    ...     Let({"x"}),
    ...     Let({"y"})
    ... )
    Traceback (most recent call last):
    ...
    TypeError: The output doesn't match the input at position 2.
    The output tree
    {('x', typing.Any)}
    doesn't match the input tree of "Let(y -> y)"
    {('y', typing.Any)}

    ```
    """

    def __init__(
            self,
            *operation_aliases: t.Union[Operation, LetAlias],
    ):
        """
        Args:
            *operation_aliases: Operations or aliases of `Let`.
        """
        operations = tuple(ensure_operation(op) for op in operation_aliases)

        append = operations[0].append

        input_keys: t.Set[Key] = operations[0].input_keys
        output_keys: t.Set[Key] = operations[0].input_keys

        for i, op in enumerate(operations):
            if append:
                input_keys = input_keys.union(
                    op.input_keys - output_keys
                )
            elif op.input_keys - output_keys != set():
                _error_msg = "\n".join([
                    f"The output doesn't match the input at position {i+1}.",
                    "The output tree",
                    repr(output_keys),
                    f"doesn't match the input tree of \"{op}\"",
                    repr(op.input_keys)
                ])
                raise TypeError(_error_msg)

            if op.append:
                output_keys = output_keys.union(op.output_keys)
            else:
                append = False
                output_keys = op.output_keys

        self.operations = operations

        super().__init__(
            input_keys=input_keys,
            output_keys=output_keys,
            append=append,
            extend=True,
        )

    def __repr__(self) -> str:
        debug_info = super().__repr__()
        for op in self.operations:
            debug_info += '\t' + repr(op).replace('\n', '\n\t')
            debug_info += '\n'
        return debug_info

    def run(self, **inputs) -> NestedDict:
        output = inputs

        for operation in self.operations:
            output = operation(**output)

        return output

    def get_syntax_node(self) -> "SyntaxNode":
        # pylint: disable=import-outside-toplevel
        from .syntax_nodes import SyntaxBranch

        return SyntaxBranch(Compose)