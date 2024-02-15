"""Implements the `Return` operation."""

import typing as t

from copy import deepcopy

from .operation import Operation

from ..types import NestedDict, Key


def get_type(obj):
    """
    Return the type of `obj`. If `obj` is a function, return `typing.Callable`.

    **Examples:**
    ```python
    >>> get_type(1)
    <class 'int'>
    >>> get_type(lambda x: x)
    typing.Callable
    >>> get_type({'a': 1})
    <class 'dict'>

    ```
    """

    if callable(obj):
        return t.Callable

    return type(obj)


class Const(Operation):
    """
    Returns a dictionary given at initialization.

    **Examples:**
    ```python
    >>> r = Const({'a': 1, 'b': {'c': True}})
    >>> r() == {'a': 1, 'b': {'c': True}}
    True

    ```
    """

    def __init__(
            self,
            output: NestedDict,
            output_keys: t.Optional[t.Set[Key]] = None,
    ):
        """
        Args:
            output: A nested dict.
            output_keys: The keys of the output.
        """
        self.output = deepcopy(output)

        if output_keys is None:
            output_keys = {(k, get_type(v)) for k, v in output.items()}

        super().__init__(
            input_keys=None,
            output_keys=output_keys
        )

    def run(self, **inputs) -> NestedDict:
        return self.output
