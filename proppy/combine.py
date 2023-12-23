"""
Contains the operations that combine multiple operations into one.
"""
import typing as t

from copy import deepcopy

from pydash import py_

from .base import (
    Operation,
    ensure_operation,
    N,
)

from .types import (
    KeyPath,
    TypeTree,
    NestedDict,
    PassAlias,
)

from .tree_utils import (
    nested_get,
    build_tree,
    type_tree_match,
    type_tree_union,
    type_tree_difference,
)

if t.TYPE_CHECKING:
    from .syntax_tree import SyntaxNode


class Concat(Operation):
    """
    Combination of operations which takes the union of inputs and outputs.

    **Examples:**
    ```python
    >>> from .base import Pass
    >>> c = Concat(Pass({"x"}), Pass({"y"}))
    >>> c(x=1, y=10, z=100) == {"x": 1, "y": 10}
    True
    >>> c = Concat(Pass({("x", int)}), Pass({("x", str)}))
    Traceback (most recent call last):
    ...
    TypeError: The input type tree of "Pass(x -> x)"
    {'x': <class 'str'>}
    couldn't be merged with
    {'x': <class 'int'>}

    ```
    """

    def __init__(self, *operation_aliases: Operation | PassAlias):
        """
        Args:
            *operation_aliases: Operations or aliases of Pass.
        """
        operations = tuple(ensure_operation(op) for op in operation_aliases)

        input_type_tree: TypeTree = {}
        for op in operations:
            try:
                type_tree_union(
                    input_type_tree,
                    op.input_type_tree,
                    minimize=True,
                )
            except TypeError as e:
                _error_msg = [f"The input type tree of \"{op}\"\n",
                              repr(op.input_type_tree), "\n",
                              "couldn't be merged with\n",
                              repr(input_type_tree)]
                raise TypeError("".join(_error_msg)) from e

        output_type_tree: TypeTree = {}
        py_.merge(
            output_type_tree,
            *(op.output_type_tree for op in operations)
        )

        append = any(op.append for op in operations)

        self.operations = operations

        super().__init__(
            input_type_tree=input_type_tree,
            output_type_tree=output_type_tree,
            append=append,
            extend=True,
        )

    def __repr__(self) -> str:
        debug_info = super().__repr__()
        for op in self.operations:
            debug_info += '\t' + repr(op).replace('\n', '\n\t')
            debug_info += '\n'
        return debug_info

    def run(self, **inputs) -> NestedDict:
        output: NestedDict = {}

        for operation in self.operations:
            py_.merge(output, operation(**inputs))

        return output

    def get_syntax_node(self) -> "SyntaxNode":
        # Import it here to avoid circular import.
        from .syntax_tree import SyntaxBranch  # pylint: disable=import-outside-toplevel

        return SyntaxBranch(Concat)


class Compose(Operation):
    """
    Combination in which the output of an operation serves as the
    input of the next operation.

    **Examples:**
    ```python
    >>> from .base import Pass
    >>> c = Compose(
    ...     Pass({("x", "a"), ("y", "b"), "z"}),
    ...     Pass({("a", "u"), "b", "z"})
    ... )
    >>> c(x=1, y=10, z=100) == {"u": 1, "b": 10, "z": 100}
    True
    >>> c = Compose(
    ...     Pass({"x"}),
    ...     Pass({"y"})
    ... )
    Traceback (most recent call last):
    ...
    TypeError: The output doesn't match the input at position 2. The output tree
    {'x': typing.Any}
    doesn't match the input tree of "Pass(y -> y)"
    {'y': typing.Any}

    ```
    """

    def __init__(self, *operation_aliases: Operation | PassAlias):
        """
        Args:
            *operation_aliases: Operations or aliases of Pass.
        """
        operations = tuple(ensure_operation(op) for op in operation_aliases)

        append = operations[0].append
        input_type_tree = deepcopy(operations[0].input_type_tree)
        output_type_tree = deepcopy(operations[0].input_type_tree)

        for i, op in enumerate(operations):
            if append:
                py_.defaults_deep(input_type_tree, op.input_type_tree)
            elif not type_tree_match(output_type_tree, op.input_type_tree):
                _error_msg = ["The output doesn't match the input at ",
                              f"position {i+1}. The output tree\n",
                              repr(output_type_tree), "\n",
                              f"doesn't match the input tree of \"{op}\"\n",
                              repr(op.input_type_tree)]
                raise TypeError("".join(_error_msg))

            if op.append:
                py_.merge(output_type_tree, op.output_type_tree)
            else:
                append = False
                output_type_tree = deepcopy(op.output_type_tree)

        self.operations = operations

        super().__init__(
            input_type_tree=input_type_tree,
            output_type_tree=output_type_tree,
            append=append,
            extend=True,
        )

    def __repr__(self) -> str:
        debug_info = super().__repr__()
        for op in self.operations:
            debug_info += '\t' + repr(op).replace('\n', '\n\t')
            debug_info += '\n'
        return debug_info

    def run(self, **inputs) -> NestedDict:
        output = inputs

        for operation in self.operations:
            output = operation(**output)

        return output

    def get_syntax_node(self) -> "SyntaxNode":
        # Import it here to avoid circular import.
        from .syntax_tree import SyntaxBranch  # pylint: disable=import-outside-toplevel

        return SyntaxBranch(Compose)


class Cycle(Operation):
    """
    An arrangement in which an operator is run multiple times until the
    counter is `0` or the value at `key` is `False`. The output of an
    iteration is fed as a part of the input for the next iteration.

    **Examples:**
    ```python
    >>> from .base import Lambda
    >>> c = Cycle(Lambda({"x": lambda s, x: x + 1}), counter=3)
    >>> c(x=0)
    {'x': 3}
    >>> e = Cycle(Lambda({
    ...     "value": lambda s, value: value / 2.0,
    ...     "counter": lambda s, counter: counter + 1,
    ...     "cond": lambda s, value: value > 1
    ... }), key="cond")
    >>> e(value=10, counter=0, cond=True) ==\
 {"value": 0.3125, "counter": 5, "cond": False}
    True
    >>> e = Cycle(Lambda({"y": lambda s, x: x + 1}), counter=3)
    Traceback (most recent call last):
    ...
    TypeError: The output type tree
    {'y': typing.Any}
    doesn't match the input type tree
    {'x': typing.Any}

    ```
    """

    def __init__(
        self,
        operation: Operation | PassAlias,
        counter: t.Optional[int] = -1,
        key: t.Optional[KeyPath] = None,
    ):
        """
        Args:
            operation: The operation which is cycled.
            counter: The number of cycles, `-1` for infinite.
            key: The key with the `Bool` value.
        """
        operation = ensure_operation(operation)

        input_type_tree = operation.input_type_tree
        output_type_tree = operation.output_type_tree
        append = operation.append

        _trees_match = type_tree_match(output_type_tree, input_type_tree)
        if not append and not _trees_match:
            _error_msg = ["The output type tree\n",
                          repr(output_type_tree), "\n",
                          "doesn't match the input type tree\n",
                          repr(input_type_tree)]
            raise TypeError("".join(_error_msg))

        self.operation = operation
        self.counter = counter
        self.key = key

        super().__init__(
            input_type_tree=input_type_tree,
            output_type_tree=output_type_tree,
            append=append,
            extend=True,
        )

    def __repr__(self) -> str:
        debug_info = super().__repr__()
        debug_info += '\t' + repr(self.operation).replace('\n', '\n\t')
        return debug_info

    def run(self, **inputs) -> NestedDict:
        outputs = inputs

        counter = 0

        if self.counter is not None:
            counter = self.counter

        while counter != 0 \
                and (self.key is None or nested_get(outputs, self.key)):

            outputs = self.operation(**outputs)

            counter -= 1

        return outputs


class Switch(Operation):
    """
    An operator with the switch-case functionality.

    **Examples:**
    ```python
    >>> from .base import Append, Lambda
    >>> s = Switch("x",
    ...     (1, Lambda({"y": lambda s: "x is 1"})),
    ...     (2, Lambda({"y": lambda s: "x is 2"})),
    ...     default=Lambda({"y": lambda s: "x is... what?"})
    ... )
    >>> s(x=1)
    {'y': 'x is 1'}
    >>> s(x=2)
    {'y': 'x is 2'}
    >>> s(x=3)
    {'y': 'x is... what?'}
    >>> s = Switch("x",
    ...     (1, Append(Lambda({"y": lambda s: "Hi"}))),
    ...     (2, Append(Lambda({"z": lambda s: "Hi"}))),
    ...     default=N
    ... )
    >>> s(x=1, y="", z="")
    {'y': 'Hi', 'z': ''}
    >>> s(x=2, y="", z="")
    {'y': '', 'z': 'Hi'}
    >>> s(x=3, y="", z="")
    {'y': '', 'z': ''}
    >>> s = Switch("x",
    ...     (1, Lambda({"y": lambda s: "Hi"})),
    ...     (2, Lambda({"z": lambda s: "Hi"})),
    ...     default=N
    ... ) # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    TypeError: The output type tree
    {'y': typing.Any}
    of "Lambda" doesn't contain
    {'z': typing.Any}

    ```
    """

    def __init__(
        self,
        key: KeyPath,
        *cases: t.Tuple[t.Any, Operation | PassAlias],
        default: t.Optional[Operation | PassAlias] = None,
    ):
        """
        Args:
            key: Key of the dict to be compared.
            cases: Iterable of tuples (option, operation).
            default: Operation to be called if there are not matches.
        """
        self.key = key
        self.cases = {c: ensure_operation(o) for c, o in cases}

        operations = [op for _, op in self.cases.items()]

        if default is not None:
            self.default = ensure_operation(default)
            operations.append(self.default)

        input_type_tree = build_tree({key}, default=t.Any)
        output_type_tree: TypeTree = {}

        for op in operations:
            try:
                type_tree_union(output_type_tree, op.output_type_tree)
            except TypeError as e:
                _error_msg = ["The output type tree\n",
                              repr(op.output_type_tree), "\n",
                              f"of \"{op}\" couldn't be merged with\n",
                              repr(output_type_tree)]
                raise TypeError("".join(_error_msg)) from e

            try:
                type_tree_union(
                    input_type_tree,
                    op.input_type_tree,
                    minimize=True,
                )
            except TypeError as e:
                _error_msg = ["The input type tree\n",
                              repr(op.input_type_tree), "\n",
                              f"of \"{op}\" couldn't be merged with\n",
                              repr(input_type_tree)]
                raise TypeError("".join(_error_msg)) from e

        # Check that each output type tree of possible operations
        # contains the same keys. If not, and if the operation has
        # append = True, add the missing fields to the input type
        # tree of the Switch.
        for op in operations:
            try:
                diff = type_tree_difference(
                    output_type_tree,
                    op.output_type_tree,
                    compare_types=False,
                )
            except TypeError as e:
                _error_msg = [f"Operation \"{op}\" has incompatible output ",
                              "type tree\n",
                              repr(op.output_type_tree), "\n",
                              "with\n",
                              repr(output_type_tree)]
                raise TypeError("".join(_error_msg)) from e

            if len(diff) > 0:
                if op.append:
                    type_tree_union(input_type_tree, diff)
                else:
                    _error_msg = ["The output type tree\n",
                                  repr(op.output_type_tree), "\n",
                                  f"of \"{op}\" doesn't contain\n",
                                  repr(diff)]
                    raise TypeError("".join(_error_msg))

        super().__init__(
            input_type_tree=input_type_tree,
            output_type_tree=output_type_tree,
            extend=True,
        )

    def __repr__(self) -> str:
        debug_info = super().__repr__()
        debug_info += f"Switch \"{self.key}\"\n"
        for c, o in self.cases.items():
            debug_info += f"case \"{c}\""
            debug_info += '\t' + repr(o).replace('\n', '\n\t')
        return debug_info

    def run(self, **inputs) -> NestedDict:
        operation = self.cases.get(
            nested_get(inputs, self.key),
            self.default,
        )

        if operation is None:
            _error_msg = ["No condition was satisfied. Consider using a ",
                          "default operation."]
            raise ValueError(_error_msg)

        return operation(**inputs)
