"""
This module contains the `ValidatorFactory` class, which is an
abstract class that defines the interface for a factory that
creates validators.

Some of its implementations are:
- `PydanticFactory`: A factory that creates Pydantic validators.
"""
from abc import ABC, abstractmethod
from pprint import pformat

import typing as t

import runtype as rt

from pydash import py_

from .keys import (
    Typed,
    Key,
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
class TypeValidatorFactory(ValidatorFactory):
    """
    Implementation of `ValidatorFactory` that checks that the
    values of `Typed` keys are of the given types.
    """

    def __call__(self, keys: t.Iterable[Key]):
        typed_keys = set()

        for key in keys:
            if isinstance(key, Typed):
                typed_keys.add(key)
            elif isinstance(key, str):
                typed_keys.add(Typed(key))
            else:
                _error_msg = f"Unsupported key type: {repr(key)}"
                raise TypeError(_error_msg)

        def validate(data):
            validated_data = {}
            validation_errors = {}
            for key in typed_keys:
                value = py_.get(data, str(key), default=key.get_default())

                try:
                    if not rt.isa(value, key.get_type()):
                        validation_errors[str(key)] = {
                            "expected": key.get_type(),
                            "received": type(value),
                            "value": value,
                        }

                        continue

                # ignore type check if the type is not supported
                except NotImplementedError:
                    pass

                # ignore type check if the ForwardRef is not resolved
                except RuntimeError:
                    pass

                py_.set_(validated_data, str(key), value)

            if len(validation_errors) > 0:
                raise ValueError(pformat(validation_errors))

            return validated_data

        return validate


validator_factory: ValidatorFactory = TypeValidatorFactory()
