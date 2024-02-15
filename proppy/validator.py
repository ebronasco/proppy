"""
This module contains the `ValidatorFactory` class, which is an
abstract class that defines the interface for a factory that
creates validators.

Some of its implementations are:
- `PydanticFactory`: A factory that creates Pydantic validators.
"""
from abc import ABC, abstractmethod

import typing as t

from pydash import py_

from .tree_utils import (
    build_tree,
    to_typed_dict,
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
        from copy import deepcopy

        tree = build_tree(keys, default=t.Any)

        typed_dict = to_typed_dict("TypeTree", tree)

        def validator(data):
            defaults = deepcopy(tree)
            py_.map_values_deep(defaults, lambda v, k: None)

            py_.defaults_deep(data, defaults)

            return TypeAdapter(typed_dict, **self.config).validate_python(data)

        return validator


validator_factory: ValidatorFactory = PydanticFactory()
