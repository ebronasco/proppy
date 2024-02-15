"""Implements the `Let` operation."""

from collections.abc import Iterable

import typing as t

from pydash import py_

from .operation import Operation

from ..types import NestedDict, LetAlias, KeyPath


def nested_get(
        data: NestedDict,
        key: KeyPath,
) -> t.Any:
    """
    Retrive an element at `key` from `data` nested dict.

    **Raises:** `KeyError` if `key` is not found in `data`.

    **Examples:**
    ```python
    >>> nested_get({'a': 1}, 'a')
    1
    >>> nested_get({'a': {'b': 1}}, 'a.b')
    1
    >>> nested_get({}, 'a')
    Traceback (most recent call last):
    ...
    KeyError: 'The key "a" is not found in "{}"'

    ```
    """
    value = py_.get(data, key, default=KeyError)

    if value is KeyError:
        _error_msg = f"The key \"{key}\" is not found in \"{repr(data)}\""
        raise KeyError(_error_msg)

    return value


def nested_set(
        data: NestedDict,
        key: KeyPath,
        value: t.Any,
) -> NestedDict:
    """
    Set an element at `key` in `data` to `value`.

    **Examples:**
    ```python
    >>> data = {}
    >>> nested_set(data, 'a', 1) == {'a': 1}
    True
    >>> data == {'a': 1}
    True
    >>> nested_set(data, 'b.c', 2) == {'a': 1, 'b': {'c': 2}}
    True
    >>> data == {'a': 1, 'b': {'c': 2}}
    True
    >>> nested_set(data, 'a.d', 3)
    Traceback (most recent call last):
    ...
    AttributeError: 'int' object has no attribute 'd'

    ```
    """
    return py_.set_(data, key, value)


class Let(Operation):
    """
    The operation that lets through the specified keys from the
    input to the output. The keys can be renamed in the process.

    **Examples:**
    ```python
    >>> p = Let({'a'}) & Let({'b', ('a.d', 'c.d')})
    >>> p(a={'d': 1}, b=2) == {'a': {'d': 1}, 'b': 2, 'c': {'d': 1}}
    True

    ```
    """

    def __init__(self, keys: LetAlias):
        """
        Args:
            keys: Specifies the keys to let through.
            Check the definition of `LetAlias` for details.
        """

        iterable_keys = keys
        if not isinstance(keys, Iterable):
            iterable_keys = {keys}

        input_keys = set()
        output_keys = set()
        connections = set()

        for key in iterable_keys:
            if not isinstance(key, tuple):
                tuple_key = (key,)
            else:
                tuple_key = t.cast(t.Tuple, key)

            if len(tuple_key) == 1:
                input_keys.add(tuple_key[0])
                output_keys.add(tuple_key[0])
                connections.add((tuple_key[0], tuple_key[0]))
            elif len(tuple_key) == 2:
                if isinstance(tuple_key[1], str):
                    input_keys.add(tuple_key[0])
                    output_keys.add(tuple_key[1])
                    connections.add(tuple_key)
                else:
                    input_keys.add(tuple_key)
                    output_keys.add(tuple_key)
                    connections.add((tuple_key[0], tuple_key[0]))
            elif len(tuple_key) == 3:
                input_keys.add((tuple_key[0], tuple_key[2]))
                output_keys.add((tuple_key[1], tuple_key[2]))
                connections.add((tuple_key[0], tuple_key[1]))

        self.connections = connections

        super().__init__(
            input_keys=input_keys,
            output_keys=output_keys,
        )

    def __str__(self) -> str:
        connections_str = [f"{v} -> {u}" for v, u in self.connections]
        return f"Let({', '.join(connections_str)})"

    def __repr__(self) -> str:
        connections_str = [f"{v} -> {u}" for v, u in self.connections]
        return f"Let({', '.join(connections_str)})"

    def run(self, **inputs) -> NestedDict:
        output: NestedDict = {}

        for conn in self.connections:
            nested_set(output, conn[1], nested_get(inputs, conn[0]))

        return output


def ensure_operation(
        obj: t.Union[Operation, LetAlias],
) -> Operation:
    """
    Ensures that `obj` is an operation by passing it to `Let` if its
    not.

    Args:
        obj: Either an alias of `Let`, or an `Operation`.

    **Raises:** `TypeError` if `obj` is of the wrong type.

    **Examples:**
    ```python
    >>> ensure_operation("x")
    Let(x -> x)
    >>> ensure_operation(("x", "y"))
    Let(x -> y)
    >>> ensure_operation(["x", ("y", "z")]).connections == \
    {("x", "x"), ("y", "z")}
    True
    >>> ensure_operation(ensure_operation("x"))
    Let(x -> x)

    ```
    """
    if isinstance(obj, Operation):
        return obj

    if isinstance(obj, (str, tuple)):
        obj = {obj}

    if not isinstance(obj, Iterable):
        _error_msg = f"The value \"{obj}\" cannot be cast to an Operation."
        raise TypeError(_error_msg)

    return Let(obj)
