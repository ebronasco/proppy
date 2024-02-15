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

from .types import (
    NestedDict,
    TypeTree,
)


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

    def __call__(self, keys):
        # pylint: disable=import-outside-toplevel
        from pydantic import TypeAdapter

        type_tree = self._build_tree(keys, default=t.Any)

        typed_dict = self._to_typed_dict("TypeTree", type_tree)

        def validator(data):
            py_.map_values_deep(type_tree, lambda v, k: None)

            py_.defaults_deep(data, type_tree)

            return TypeAdapter(typed_dict, **self.config).validate_python(data)

        return validator

    def _build_tree(
            self,
            elems: t.Iterable[t.Union[t.Tuple, t.Any]],
            default: t.Any = None,
    ) -> NestedDict:
        """
        Builds a nested dict based on `elems`.

        Elements of `elems` are `(v1,v2,...)`. then it builds a nested dict
        with keys `v1` and values `(v2,...)`. If `(v2,...)` is a singleton,
        then its replaced by `v2`.


        Args:
            elems: Iterable `elems` of `(v1,v2,...)`. Elements which are not
                tuples are replaced by the tuple `(element, default)`.
            default: Default value of the tree if only `v1` is given.

        **Raises:** `TypeError` if `elem` is not `PassAliasT`.

        **Examples:**
        ```python
        >>> pf = PydanticFactory()
        >>> pf._build_tree({('a', int), 'b', 'c.d'}) == \
        {'a': int, 'b': None, 'c': {'d': None}}
        True
        >>> pf._build_tree(True)
        Traceback (most recent call last):
        ...
        TypeError: The argument `elems` is of unsupported type:
        True

        ```
        """
        if isinstance(elems, Iterable) and not isinstance(elems, dict):
            key_value_pairs = []
            for elem in elems:
                if not isinstance(elem, tuple) or len(elem) == 1:
                    key_value_pairs.append((elem, default))
                    continue

                if len(elem) == 2:
                    key_value_pairs.append((elem[0], elem[1]))
                    continue

                key_value_pairs.append((elem[0], elem[1:]))

            if len(key_value_pairs) > 0:
                return py_.zip_object_deep(key_value_pairs)

            return {}

        _error_msg = "\n".join([
            "The argument `elems` is of unsupported type:",
            repr(elems)
        ])
        raise TypeError(_error_msg)

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
