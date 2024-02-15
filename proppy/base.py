"""
Defines the `Operation` superclass and some fundamental operations.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from copy import deepcopy

import typing as t
import functools

from pydash import py_

from .syntax_tree import ensure_syntax_node

from .tree_utils import (
    keys_from_callable,
    nested_get,
    nested_set,
)

from .types import (
    Key,
    FlatDict,
    NestedDict,
    PassAlias,
)

from .validator import (
    validator_factory,
)

if t.TYPE_CHECKING:
    from .syntax_tree import SyntaxNode


def ensure_typed_keys(
        keys: t.Set[Key],
) -> t.Set[Key]:
    """
    Ensures that `keys` is a set of (`Key`, `type`).

    Args:
        keys: A set of keys
    """
    new_keys = set()
    for key in keys:
        if isinstance(key, tuple):
            new_keys.add(key)
        else:
            new_keys.add((key, t.Any))

    return new_keys


class Operation(ABC):
    """
    *An abstract superclass for all operations.*

    An operation is characterized by its input and output type trees,
    and by its implementation of the `run` method. Input and output
    trees define the corresponding validators.
    """

    # pylint: disable=too-many-instance-attributes
    # Eight is reasonable in this case.

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
            input_keys = keys_from_callable(self.run, start_at=1)

        self.input_keys = ensure_typed_keys(input_keys)
        self.output_keys = ensure_typed_keys(output_keys)

        self.validate_input = validator_factory(input_keys)
        self.validate_output = validator_factory(output_keys)

        self.append = append
        self.extend = extend

    def get_syntax_node(self) -> "SyntaxNode":
        """Wrap the operation into a `SyntaxLeaf`."""

        # import it here to avoid circular import.
        # pylint: disable=import-outside-toplevel
        from .syntax_tree import SyntaxLeaf

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
        except Exception as e:
            _error_msg = ["Error occured in the operation:\n",
                          repr(self), "\n",
                          "Input:\n",
                          repr(inputs), "\n",
                          "doesn't match the input keys\n",
                          repr(self.input_keys)]
            raise TypeError("".join(_error_msg)) from e

        if self.extend:
            valid_inputs = inputs

        outputs = self.run(**valid_inputs)

        try:
            valid_outputs = self.validate_output(outputs)
        except Exception as e:
            _error_msg = ["Error occured in the operation:\n",
                          repr(self), "\n",
                          "Output\n",
                          repr(outputs), "\n",
                          "doesn't match the output keys\n",
                          repr(self.output_keys)]
            raise TypeError("".join(_error_msg)) from e

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
        >>> p = Pass('a') & Pass({'b', ('a.d', 'c.d')})
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
            other: t.Union["SyntaxNode", PassAlias],
    ) -> "SyntaxNode":
        return self.get_syntax_node() & ensure_syntax_node(other)

    def __or__(
            self,
            other: t.Union["SyntaxNode", PassAlias],
    ) -> "SyntaxNode":
        return self.get_syntax_node() | ensure_syntax_node(other)

    def __rand__(
            self,
            other: t.Union["SyntaxNode", PassAlias],
    ) -> "SyntaxNode":
        return ensure_syntax_node(other) & self.get_syntax_node()

    def __ror__(
            self,
            other: t.Union["SyntaxNode", PassAlias],
    ) -> "SyntaxNode":
        return ensure_syntax_node(other) | self.get_syntax_node()

    def __rrshift__(
            self,
            other: t.Any,
    ) -> t.Tuple[t.Any, "SyntaxNode"]:
        return other >> self.get_syntax_node()


class Pass(Operation):
    """
    The operator that "passes through" the data with the possibility of
    changing its shape.

    **Examples:**
    ```python
    >>> p = Pass({'a'}) & Pass({'b', ('a.d', 'c.d')})
    >>> p(a={'d': 1}, b=2) == {'a': {'d': 1}, 'b': 2, 'c': {'d': 1}}
    True

    ```
    """

    def __init__(self, keys: PassAlias):
        """
        Args:
            keys: Specifies the keys to pass. Check the definition of
            `PassAlias` for details.
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
        return f"Pass({', '.join(connections_str)})"

    def __repr__(self) -> str:
        connections_str = [f"{v} -> {u}" for v, u in self.connections]
        return f"Pass({', '.join(connections_str)})"

    def run(self, **inputs) -> NestedDict:
        output: NestedDict = {}

        for conn in self.connections:
            nested_set(output, conn[1], nested_get(inputs, conn[0]))

        return output


class Return(Operation):
    """
    Returns a dictionary given at initialization.

    **Examples:**
    ```python
    >>> r = Return({'a': 1, 'b': {'c': True}})
    >>> r() == {'a': 1, 'b': {'c': True}}
    True

    ```
    """

    def __init__(
            self,
            output: NestedDict,
            output_keys: t.Optional[t.Set[Key]] = None,
    ):
        """
        Args:
            output: A nested dict.
            output_keys: The keys of the output.
        """
        self.output = deepcopy(output)

        if output_keys is None:
            output_keys = set(output.keys())

        super().__init__(
            input_keys=None,
            output_keys=output_keys
        )

    def run(self, **inputs) -> NestedDict:
        return self.output


def operation(
        output_keys: t.Set[Key],
        input_keys: t.Optional[t.Set[Key]] = None,
        name: t.Optional[str] = None,
) -> t.Union[Operation, t.Callable]:
    """
    Decorate a function to be an operation.

    **Examples:**
    ```python
    >>> @operation({("res.a", float)})
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
    >>> add = lambda s, x, y: {'res': {'a': x + y}}
    >>> op = Function({("res.a", float)}, add)
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
            input_keys = keys_from_callable(func, start_at=1)

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


class Lambda(Operation):
    """
    Return a dict whose values are computed using `callable`s.

    **Examples:**
    ```python
    >>> l = Lambda({"a": lambda s, x: x + 1, "b": lambda s, x, y: x + y})
    >>> l(x=1, y=10) == {"a": 2, "b": 11}
    True
    >>> Lambda({"a": lambda s, x: x + 1, "b": 1})
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
                _error_msg = [
                    f"The value at \"{key}\" must be either a ",
                    "callable or a tuple (callable, output type).",
                ]

                raise TypeError("".join(_error_msg))

            output_keys.add(key)

            func_input_keys = keys_from_callable(func, start_at=1)

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


class Append(Operation):
    """
    Wraps an operation. When called, returns the given input with the output
    of the operation appended to it.

    **Examples:**
    ```python
    >>> a = Lambda({"a": lambda s, x: x + 1})
    >>> a(x=1, y=10) == {"a": 2}
    True
    >>> a = Append(Lambda({"a": lambda s, x: x + 1}))
    >>> a(x=1, y=10) == {"a": 2, "x": 1, "y": 10}
    True

    ```
    """

    def __init__(
            self,
            op: t.Union[Operation, PassAlias],
    ):
        """
        Args:
            op: an operation or a Pass alias.
        """
        op = ensure_operation(op)

        self.operation = op

        super().__init__(
            input_keys=op.input_keys,
            output_keys=op.output_keys,
            append=True,
            extend=True,
        )

    def __repr__(self) -> str:
        return f"+{repr(self.operation)}"

    def run(self, **inputs) -> NestedDict:
        return self.operation(**inputs)

    def __neg__(self) -> Operation:
        """Unwrap the operation."""
        return self.operation


class Empty(Operation):
    """
    Receive nothing, return nothing.

    **Examples:**
    ```python
    >>> e = Empty()
    >>> e()
    {}

    ```
    """

    def __init__(self):
        super().__init__(
            input_keys=None,
            output_keys=set(),
        )

    def __repr__(self) -> str:
        return "Empty"

    def run(self, **inputs) -> NestedDict:
        return {}


E = Empty()


class Id(Operation):
    """
    Returns what it receives. Call the `callable`s if given.

    **Examples:**
    ```python
    >>> i = Id()
    >>> i(a=1, b=2) == {"a": 1, "b": 2}
    True
    >>> i = Id(print)
    >>> i(a=1) == {"a": 1}
    {'a': 1}
    True

    ```
    """

    def __init__(self, *funcs: t.Callable):
        """
        Args:
            *funcs: Callables to be called.
        """

        for func in funcs:
            if func is not None and not callable(func):
                _error_msg = f"The argument \"{func}\" must be a callable."
                raise TypeError(_error_msg)

        self.funcs = funcs

        super().__init__(
            input_keys=None,
            output_keys=set(),
            append=True,
            extend=True,
        )

    def __repr__(self) -> str:
        if len(self.funcs) > 0:
            funcs_str = f"({[repr(f) for f in self.funcs]})"
        else:
            funcs_str = ""
        return "Id" + funcs_str

    def run(self, **inputs) -> NestedDict:
        for func in self.funcs:
            func(inputs)
        return {}


def ensure_operation(
        obj: t.Union[Operation, PassAlias],
) -> Operation:
    """
    Ensures that `obj` is an operation by passing it to `Pass` if its
    not.

    Args:
        obj: Either an alias of `Pass`, or an `Operation`.

    **Raises:** `TypeError` if `obj` is of the wrong type.

    **Examples:**
    ```python
    >>> ensure_operation("x")
    Pass(x -> x)
    >>> ensure_operation(("x", "y"))
    Pass(x -> y)
    >>> ensure_operation(["x", ("y", "z")]).connections == \
    {("x", "x"), ("y", "z")}
    True
    >>> ensure_operation(ensure_operation("x"))
    Pass(x -> x)

    ```
    """
    if isinstance(obj, Operation):
        return obj

    if isinstance(obj, (str, tuple)):
        obj = {obj}

    if not isinstance(obj, Iterable):
        _error_msg = f"The value \"{obj}\" cannot be cast to an Operation."
        raise TypeError(_error_msg)

    return Pass(obj)


N = Id()
