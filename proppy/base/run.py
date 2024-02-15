"""Implements the `Run` operation."""

import typing as t

from ..types import NestedDict, Key, FlatDict

from .operation import (
    Operation,
    validator_factory,
    input_keys_from_callable,
)


class Run(Operation):
    """
    Return a dict whose values are computed using `callable`s.

    **Examples:**
    ```python
    >>> l = Run({"a": lambda s, x: x + 1, "b": lambda s, x, y: x + y})
    >>> l(x=1, y=10) == {"a": 2, "b": 11}
    True
    >>> Run({"a": lambda s, x: x + 1, "b": 1})
    Traceback (most recent call last):
    ...
    TypeError: The value at "b" must be either a callable or a tuple\
 (callable, output type).

    ```
    """

    def __init__(self, output: FlatDict):
        """
        Args:
            output: The dict of `callable`s.
        """

        input_keys: t.Set[Key] = set()
        output_keys: t.Set[Key] = set()

        input_validators: t.Dict = {}

        for key, value in output.items():
            if callable(value):
                func = value
            else:
                _error_msg = "".join([
                    f"The value at \"{key}\" must be either a ",
                    "callable or a tuple (callable, output type).",
                ])

                raise TypeError(_error_msg)

            output_keys.add(key)

            func_input_keys = input_keys_from_callable(func, start_at=1)

            input_keys = input_keys.union(func_input_keys)

            input_validators[key] = validator_factory(func_input_keys)

        self.input_validators = input_validators
        self.output = output

        super().__init__(
            input_keys=input_keys,
            output_keys=output_keys,
        )

    def __str__(self) -> str:
        return "Lambda"

    def __repr__(self) -> str:
        return repr(self.output)

    def run(self, **inputs) -> NestedDict:
        output = {}

        for key, func in self.output.items():
            output[key] = func(
                self,
                **self.input_validators[key](inputs),
            )

        return output
