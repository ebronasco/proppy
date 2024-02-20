"""Implements the `Append` operation."""

import typing as t

from .operation import Operation, LetAlias

from .let import ensure_operation


NestedDict = t.Dict


class Append(Operation):
    """
    Wraps an operation. When called, returns the given input with the output
    of the operation appended to it.

    **Examples:**
    ```python
    >>> from .append import Append
    >>> from .run import Run
    >>> a = Run({"a": lambda s, x: x + 1})
    >>> a(x=1, y=10) == {"a": 2}
    True
    >>> a = Append(Run({"a": lambda s, x: x + 1}))
    >>> a(x=1, y=10) == {"a": 2, "x": 1, "y": 10}
    True

    ```
    """

    def __init__(
            self,
            op: t.Union[Operation, LetAlias],
    ):
        """
        Args:
            op: an operation or a Pass alias.
        """
        op = ensure_operation(op)

        self.operation = op

        super().__init__(
            input_keys=op.input_keys,
            output_keys=op.output_keys,
            append=True,
            extend=True,
        )

    def __repr__(self) -> str:
        return f"+{repr(self.operation)}"

    def run(self, **inputs) -> NestedDict:
        return self.operation(**inputs)

    def __neg__(self) -> Operation:
        """Unwrap the operation."""
        return self.operation
