"""The `Operation` class and helper functions."""

from abc import ABC, abstractmethod
from inspect import getfullargspec

import typing as t

import pydash as py_

from ..validators import validator_factory, Typed
from ..types import NestedDict, Key, LetAlias

if t.TYPE_CHECKING:
    from ..syntax_nodes import SyntaxNode


def input_keys_from_callable(
        func: t.Callable,
        start_at: t.Optional[int] = 0,
) -> t.Set[Key]:
    """
    Build an input type tree of a callable.

    Args:
        func: The callable whose input type tree is built.
        start_at: Ignore the arguments at positions before `start_at`.

    **Examples:**
    ```python
    >>> input_keys_from_callable(lambda x, y: x) \
    == {('x', t.Any), ('y', t.Any)}
    True
    >>> def a(s: str, b: bool):
    ...     pass
    ...
    >>> input_keys_from_callable(a) \
    == {('s', str), ('b', bool)}
    True

    ```
    """
    argspec = getfullargspec(func)
    args = argspec.args[start_at:]
    return set(Typed(k, argspec.annotations.get(k, t.Any)) for k in args)


class Operation(ABC):
    """
    *An abstract superclass for all operations.*

    An operation is characterized by its input and output type trees,
    and by its implementation of the `run` method. Input and output
    trees define the corresponding validators.
    """

    def __init__(
            self,
            output_keys: t.Set[Key],
            input_keys: t.Optional[t.Set[Key]] = None,
            append: bool = False,
            extend: bool = False,
    ):
        """
        Args:
            output_type_tree: Type tree used to validate the output.
            input_type_tree: Type tree used to validate the input.
                *Default*: the arguments of `run`.
            append: Append the output of the operation to the given input.
            extend: Pass all input to the `run` method. If `False`, then pass
                only the input that is covered by the `input_type_tree`.
        """

        if input_keys is None:
            input_keys = input_keys_from_callable(self.run, start_at=1)

        self.input_keys = input_keys
        self.output_keys = output_keys

        self.validate_input = validator_factory(input_keys)
        self.validate_output = validator_factory(output_keys)

        self.append = append
        self.extend = extend

    def get_syntax_node(self) -> "SyntaxNode":
        """Wrap the operation into a `SyntaxLeaf`."""
        # pylint: disable=import-outside-toplevel
        from ..syntax_nodes import SyntaxLeaf

        return SyntaxLeaf(self)

    def __str__(self):
        return type(self).__name__

    def __repr__(self) -> str:
        debug_info = "\n" + type(self).__name__ + "\n"
        debug_info += f" -- input keys: {self.input_keys}\n"
        debug_info += f" -- output keys: {self.output_keys}\n"
        return debug_info

    def __call__(self, **inputs) -> NestedDict:
        """
        Performs the following steps:

        1. Validate the input using `input_type_tree`.
        2. Pass the input to `run`.
        3. Validate the output of `run` using `output_type_tree`.

        **Raises:**
        `ValidatorError` is raised by input and output validators.
        """

        try:
            valid_inputs = self.validate_input(inputs)
        except Exception as e:  # catch validator errors
            _error_msg = "\n".join([
                "Error occured in the operation:",
                repr(self),
                "Input:",
                repr(inputs),
                "doesn't match the input keys",
                repr(self.input_keys)
            ])
            raise TypeError(_error_msg) from e

        if self.extend:
            valid_inputs = inputs

        outputs = self.run(**valid_inputs)

        try:
            valid_outputs = self.validate_output(outputs)
        except Exception as e:  # catch validator errors
            _error_msg = "\n".join([
                "Error occured in the operation:",
                repr(self),
                "Output",
                repr(outputs),
                "doesn't match the output keys",
                repr(self.output_keys)
            ])
            raise TypeError(_error_msg) from e

        if self.append:
            valid_outputs = py_.merge(inputs, valid_outputs)

        return valid_outputs

    @abstractmethod
    def run(self, **inputs) -> NestedDict:
        """Must be implemented by subclasses. It is called by `__call__`."""
        _error_msg = "The method `run` is not implemented."
        raise NotImplementedError(_error_msg)

    def partial(self, **inputs) -> "SyntaxNode":
        """
        Partially apply the operation to `inputs`.

        **Examples:**
        ```python
        >>> from .let import Let
        >>> p = Let('a') & Let({'b', ('a.d', 'c.d')})
        >>> p(a={'d': 1}, b=2) == {'a': {'d': 1}, 'b': 2, 'c': {'d': 1}}
        True
        >>> p.partial(b=2)(a={'d': 1}) \
        == {'a': {'d': 1}, 'b': 2, 'c': {'d': 1}}
        True

        ```
        """
        return self.get_syntax_node().partial(**inputs)

    def __pos__(self) -> "SyntaxNode":
        return +(self.get_syntax_node())

    def __and__(
            self,
            other: t.Union["SyntaxNode", LetAlias],
    ) -> "SyntaxNode":
        # pylint: disable=import-outside-toplevel
        from ..syntax_nodes import ensure_syntax_node

        return self.get_syntax_node() & ensure_syntax_node(other)

    def __or__(
            self,
            other: t.Union["SyntaxNode", LetAlias],
    ) -> "SyntaxNode":
        # pylint: disable=import-outside-toplevel
        from ..syntax_nodes import ensure_syntax_node

        return self.get_syntax_node() | ensure_syntax_node(other)

    def __rand__(
            self,
            other: t.Union["SyntaxNode", LetAlias],
    ) -> "SyntaxNode":
        # pylint: disable=import-outside-toplevel
        from ..syntax_nodes import ensure_syntax_node

        return ensure_syntax_node(other) & self.get_syntax_node()

    def __ror__(
            self,
            other: t.Union["SyntaxNode", LetAlias],
    ) -> "SyntaxNode":
        # pylint: disable=import-outside-toplevel
        from ..syntax_nodes import ensure_syntax_node

        return ensure_syntax_node(other) | self.get_syntax_node()

    def __rrshift__(
            self,
            other: t.Any,
    ) -> t.Tuple[t.Any, "SyntaxNode"]:
        return other >> self.get_syntax_node()
