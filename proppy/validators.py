"""
This module contains the `ValidatorFactory` class, which is an
abstract class that defines the interface for a factory that
creates validators.

Some of its implementations are:
- `PydanticFactory`: A factory that creates Pydantic validators.
"""
from abc import ABC, abstractmethod
from collections.abc import Iterable

import typing as t
from typing_extensions import TypedDict

from pydash import py_

from .keys import (
    Typed,
    Key,
)


TypeTree = t.Dict


# pylint: disable=too-few-public-methods
class ValidatorFactory(ABC):
    """
    Abstract class that defines the interface for a factory that
    creates validators.
    """

    @abstractmethod
    def __call__(self, keys):
        """Must return a validator."""
        error_msg = "The method `__call__` must be implemented"
        raise NotImplementedError(error_msg)


# pylint: disable=too-few-public-methods
class PydanticFactory(ValidatorFactory):
    """
    Implementation of `ValidatorFactory` that creates Pydantic
    validators.
    """

    def __init__(self, **kwargs):
        self.config = kwargs

    def __call__(self, keys: t.Iterable[Key]):
        # pylint: disable=import-outside-toplevel
        from pydantic import TypeAdapter

        typed_keys = set()

        for key in keys:
            if isinstance(key, Typed):
                typed_keys.add(key)
            elif isinstance(key, str):
                typed_keys.add(Typed(key, t.Any))
            else:
                _error_msg = f"Unsupported key type: {repr(key)}"
                raise TypeError(_error_msg)

        type_tree = self._build_tree(typed_keys)

        typed_dict = self._to_typed_dict("TypeTree", type_tree)

        def validator(data):
            py_.map_values_deep(type_tree, lambda v, k: None)

            py_.defaults_deep(data, type_tree)

            return TypeAdapter(typed_dict, **self.config).validate_python(data)

        return validator

    def _build_tree(
            self,
            elems: t.Iterable[Typed],
    ) -> TypeTree:
        """
        Builds a nested dict based on `elems`.

        Args:
            elems: Iterable of `Typed(name, type)`.

        **Raises:** `TypeError` if `elem` is of unsupported type.

        **Examples:**
        ```python
        >>> pf = PydanticFactory()
        >>> pf._build_tree({
        ...     Typed('a', int),
        ...     Typed('b', t.Any),
        ...     Typed('c.d', t.Any)
        ... }) == {'a': int, 'b': t.Any, 'c': {'d': t.Any}}
        True
        >>> pf._build_tree(True)
        Traceback (most recent call last):
        ...
        TypeError: The argument `elems` must be an iterable.
        Value of `elems`: True
        >>> pf._build_tree([True])
        Traceback (most recent call last):
        ...
        TypeError: The elements of `elems` must be instances of `Typed`.
        Value of `elems` element: True


        ```
        """
        if not isinstance(elems, Iterable):
            _error_msg = "\n".join([
                "The argument `elems` must be an iterable.",
                f"Value of `elems`: {repr(elems)}"
            ])
            raise TypeError(_error_msg)

        key_value_pairs = []
        for elem in elems:
            if not isinstance(elem, Typed):
                _error_msg = "\n".join([
                    "The elements of `elems` must be instances of `Typed`.",
                    f"Value of `elems` element: {repr(elem)}"
                ])
                raise TypeError(_error_msg)

            key_value_pairs.append((str(elem), elem.get_type()))

        if len(key_value_pairs) > 0:
            return py_.zip_object_deep(key_value_pairs)

        return {}

    def _to_typed_dict(
            self,
            root_name: str,
            type_tree: TypeTree,
    ) -> t.Type:
        """Wrap keys in TypedDict named `root_name` recursively."""

        try:
            tree_items = type_tree.items()
        except AttributeError as e:
            _error_msg = ["The argument `type_tree` must be a `dict`. ",
                          "Value of `type_tree`:\n",
                          repr(type_tree)]
            raise AttributeError("".join(_error_msg)) from e

        typed_subdicts = {}

        for k, v in tree_items:
            if isinstance(v, dict):
                typed_subdicts[k] = self._to_typed_dict(str(k), v)
            else:
                typed_subdicts[k] = v

        return TypedDict(root_name, typed_subdicts)  # type: ignore


validator_factory: ValidatorFactory = PydanticFactory()
