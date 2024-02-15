"""Implement the `Id` operation."""

import typing as t

from .operation import Operation

from ..types import NestedDict


class Id(Operation):
    """
    Returns what it receives. Call the `callable`s if given.

    **Examples:**
    ```python
    >>> i = Id()
    >>> i(a=1, b=2) == {"a": 1, "b": 2}
    True
    >>> i = Id(print)
    >>> i(a=1) == {"a": 1}
    {'a': 1}
    True

    ```
    """

    def __init__(self, *funcs: t.Callable):
        """
        Args:
            *funcs: Callables to be called.
        """

        for func in funcs:
            if func is not None and not callable(func):
                _error_msg = f"The argument \"{func}\" must be a callable."
                raise TypeError(_error_msg)

        self.funcs = funcs

        super().__init__(
            input_keys=None,
            output_keys=set(),
            append=True,
            extend=True,
        )

    def __repr__(self) -> str:
        if len(self.funcs) > 0:
            funcs_str = f"({[repr(f) for f in self.funcs]})"
        else:
            funcs_str = ""
        return "Id" + funcs_str

    def run(self, **inputs) -> NestedDict:
        for func in self.funcs:
            func(inputs)
        return {}


N = Id()
