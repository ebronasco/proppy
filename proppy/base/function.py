"""
Implement the `Function` class to wrap a function into an operation.
"""

import functools
import typing as t

from .operation import Operation, input_keys_from_callable

from ..keys import Key


NestedDict = t.Dict


def operation(
        output_keys: t.Set[Key],
        input_keys: t.Optional[t.Set[Key]] = None,
        name: t.Optional[str] = None,
) -> t.Union[Operation, t.Callable]:
    """
    Decorate a function to be an operation.

    **Examples:**
    ```python
    >>> from ..keys import Typed
    >>> @operation({Typed("res.a", float)})
    ... def add(s, x, y):
    ...     return {"res": {"a": x + y}}
    >>> add(x=1, y=2)
    {'res': {'a': 3.0}}

    """

    def wrapper(func):
        return Function(
            output_keys=output_keys,
            input_keys=input_keys,
            func=func,
            name=name,
        )
    return wrapper


class Function(Operation):
    """
    Wraps a given function into an operation.

    **Examples**
    ```python
    >>> from ..keys import Typed
    >>> add = lambda s, x, y: {'res': {'a': x + y}}
    >>> op = Function({Typed("res.a", float)}, add)
    >>> op(x=1, y=2)
    {'res': {'a': 3.0}}

    ```
    """

    def __init__(
            self,
            output_keys: t.Set[Key],
            func: t.Callable,
            input_keys: t.Optional[t.Set[Key]] = None,
            name: t.Optional[str] = None,
    ):
        """
        Args:
            output_keys: The output keys of the function.
            func: The function to be wrapped. The first argument
                of `func` receives the instance `self`.
            input_keys: The required input keys of the function.
                If `None`, input keys are the arguments of `func`.
            name: Name of the function used for debug.
        """
        if input_keys is None:  # mypy: ignore
            input_keys = input_keys_from_callable(func, start_at=1)

        if name is None:  # mypy: ignore
            name = func.__name__

        self._func = func
        self._name = name

        functools.update_wrapper(self, func)

        super().__init__(
            input_keys=input_keys,
            output_keys=output_keys,
        )

    def __repr__(self) -> str:
        return self._name

    def run(self, **inputs) -> NestedDict:
        return self._func(self, **inputs)
