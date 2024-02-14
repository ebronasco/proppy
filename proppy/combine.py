"""
Contains the operations that combine multiple operations into one.
"""
import typing as t

from copy import deepcopy

from pydash import py_

from .base import (
    Operation,
    ensure_operation,
)

from .types import (
    TypeTree,
    NestedDict,
    PassAlias,
)

from .tree_utils import (
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

    def __init__(
            self,
            *operation_aliases: t.Union[Operation, PassAlias],
    ):
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
        # pylint: disable=import-outside-toplevel
        from .syntax_tree import SyntaxBranch

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
    TypeError: The output doesn't match the input at position 2.
    The output tree
    {'x': typing.Any}
    doesn't match the input tree of "Pass(y -> y)"
    {'y': typing.Any}

    ```
    """

    def __init__(
            self,
            *operation_aliases: t.Union[Operation, PassAlias],
    ):
        """
        Args:
            *operation_aliases: Operations or aliases of Pass.
        """
        operations = tuple(ensure_operation(op) for op in operation_aliases)

        append = operations[0].append

        input_type_tree: TypeTree = deepcopy(operations[0].input_type_tree)
        output_type_tree: TypeTree = deepcopy(operations[0].input_type_tree)

        for i, op in enumerate(operations):
            if append:
                type_tree_union(
                    input_type_tree,
                    type_tree_difference(
                        op.input_type_tree,
                        output_type_tree,
                        keep_bigger=False,
                    ),
                )
            elif not type_tree_match(output_type_tree, op.input_type_tree):
                _error_msg = ["The output doesn't match the input at ",
                              f"position {i+1}.\n",
                              "The output tree\n",
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
        # pylint: disable=import-outside-toplevel
        from .syntax_tree import SyntaxBranch

        return SyntaxBranch(Compose)
