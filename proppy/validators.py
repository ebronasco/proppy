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

from pydash import py_

from pydantic import ConfigDict, create_model

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

    def __init__(self, config: t.Optional[ConfigDict] = None):
        if config is None:
            self.config = ConfigDict()
        else:
            self.config = config

    def __call__(self, keys: t.Iterable[Key]):
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

        model = create_model(
            "Model",
            **{
                k: self._create_model(v)
                for k, v in type_tree.items()
            },
            __config__=self.config
        )

        return lambda data: model(**data).model_dump()

    def _create_model(self, type_or_tree):
        if isinstance(type_or_tree, TypeTree):
            return (
                create_model(
                    "Model",
                    **{
                        k: self._create_model(v)
                        for k, v in type_or_tree.items()
                    },
                    __config__=self.config
                ),
                ...
            )

        if self._is_optional(type_or_tree):
            default_value = None
        else:
            default_value = ...

        return (type_or_tree, default_value)

    def _is_optional(self, type_):
        return t.get_origin(type_) is t.Union \
            and type(None) in t.get_args(type_)

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


validator_factory: ValidatorFactory = PydanticFactory(
    config=ConfigDict(arbitrary_types_allowed=True)
)
