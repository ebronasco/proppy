from abc import ABC, abstractmethod
from copy import deepcopy

import typing as t

from pydash import py_

from .tree_utils import (
    build_tree,
    to_typed_dict,
)

class ValidatorFactory(ABC):

    @abstractmethod
    def __call__(self, keys):
        """Must return a validator."""
        error_msg = "The method `build_validator` must be implemented"
        raise NotImplementedError(error_msg)

class PydanticFactory(ValidatorFactory):

    def __init__(self, **kwargs):
        self.config = kwargs

    def __call__(self, keys):
        from pydantic import TypeAdapter

        tree = build_tree(keys, default=t.Any)

        typed_dict = to_typed_dict("TypeTree", tree)

        def validator(data):
            defaults = deepcopy(tree)
            py_.map_values_deep(defaults, lambda v, k: None)

            py_.defaults_deep(data, defaults)

            return TypeAdapter(typed_dict, **self.config).validate_python(data)

        return validator

validator_factory: ValidatorFactory = PydanticFactory()
