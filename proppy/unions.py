"""
Contains the operations that combine multiple operations into one.
"""
import typing as t

from pydash import py_

from .base.operation import Operation, LetAlias

from .base.let import ensure_operation

from .keys import Key


NestedDict = t.Dict


if t.TYPE_CHECKING:
    from .syntax_nodes import SyntaxNode


class Concat(Operation):
    """
    Combination of operations which takes the union of inputs and outputs.

    **Examples:**
    ```python
    >>> from .base.let import Let
    >>> c = Concat(Let({"x"}), Let({"y"}))
    >>> c(x=1, y=10, z=100) == {"x": 1, "y": 10}
    True

    ```
    """

    def __init__(
            self,
            *operation_aliases: t.Union[Operation, LetAlias],
    ):
        """
        Args:
            *operation_aliases: Operations or aliases of `Let`.
        """
        operations = tuple(ensure_operation(op) for op in operation_aliases)

        input_keys: t.Set[Key] = set()
        output_keys: t.Set[Key] = set()
        for op in operations:
            input_keys = input_keys.union(op.input_keys)
            output_keys = output_keys.union(op.output_keys)

        append = any(op.append for op in operations)

        self.operations = operations

        super().__init__(
            input_keys=input_keys,
            output_keys=output_keys,
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
        # pylint: disable=import-outside-toplevel
        from .syntax_nodes import SyntaxBranch

        return SyntaxBranch(Concat)


class Compose(Operation):
    """
    Combination in which the output of an operation serves as the
    input of the next operation.

    **Examples:**
    ```python
    >>> from .base.let import Let
    >>> c = Compose(
    ...     Let({("x", "a"), ("y", "b"), "z"}),
    ...     Let({("a", "u"), "b", "z"})
    ... )
    >>> c(x=1, y=10, z=100) == {"u": 1, "b": 10, "z": 100}
    True
    >>> c = Compose(
    ...     Let({"x"}),
    ...     Let({"y"})
    ... )
    Traceback (most recent call last):
    ...
    TypeError: The output doesn't match the input at position 2.
    The output tree
    {'x'}
    doesn't match the input tree of "Let(y -> y)"
    {'y'}

    ```
    """

    def __init__(
            self,
            *operation_aliases: t.Union[Operation, LetAlias],
    ):
        """
        Args:
            *operation_aliases: Operations or aliases of `Let`.
        """
        operations = tuple(ensure_operation(op) for op in operation_aliases)

        append = operations[0].append

        input_keys: t.Set[Key] = operations[0].input_keys
        output_keys: t.Set[Key] = operations[0].input_keys

        for i, op in enumerate(operations):
            complement_keys: t.Set[Key] = get_complement_keys(
                output_keys,
                op.input_keys
            )

            if append:
                input_keys = input_keys.union(complement_keys)

            elif len(complement_keys) > 0:
                _error_msg = "\n".join([
                    f"The output doesn't match the input at position {i+1}.",
                    "The output tree",
                    repr(output_keys),
                    f"doesn't match the input tree of \"{op}\"",
                    repr(op.input_keys)
                ])
                raise TypeError(_error_msg)

            if op.append:
                output_keys = output_keys.union(op.output_keys)
            else:
                append = False
                output_keys = op.output_keys

        self.operations = operations

        super().__init__(
            input_keys=input_keys,
            output_keys=output_keys,
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
        # pylint: disable=import-outside-toplevel
        from .syntax_nodes import SyntaxBranch

        return SyntaxBranch(Compose)


def get_complement_keys(
        keys1: t.Set[Key],
        keys2: t.Set[Key],
) -> t.Set[Key]:
    """
    Computes the keys of `keys2` that are not matched by any keys
    from `keys1`.

    Args:
        keys1: Set of keys.
        keys2: Set of keys.

    Returns:
        The set of keys that are not matched by any keys from
        `keys1`.
    """

    complement_keys: t.Set[Key] = set()

    keys1_dict = {str(k): k for k in keys1}

    for k2 in keys2:
        if str(k2) not in keys1_dict:
            if isinstance(k2, str):
                complement_keys.add(k2)

            elif not k2.match(None):
                complement_keys.add(k2)

        elif not isinstance(k2, str) \
                and not k2.match(keys1_dict[str(k2)]):
            complement_keys.add(k2)

    return complement_keys
