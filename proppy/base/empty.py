"""Implements the `Empty` operation."""

from .operation import Operation

from ..types import NestedDict


class Empty(Operation):
    """
    Receive nothing, return nothing.

    **Examples:**
    ```python
    >>> e = Empty()
    >>> e()
    {}

    ```
    """

    def __init__(self):
        super().__init__(
            input_keys=None,
            output_keys=set(),
        )

    def __repr__(self) -> str:
        return "Empty"

    def run(self, **inputs) -> NestedDict:
        return {}


E = Empty()
